from __future__ import annotations

import warnings

from sauronlab.core.core_imports import *
from sauronlab.model.cache_interfaces import ASensorCache, AWellCache
from sauronlab.model.features import FeatureType, FeatureTypes
from sauronlab.model.treatments import Treatments
from sauronlab.model.well_frames import SerializedWellFrame
from sauronlab.model.well_names import WellNamers
from sauronlab.model.wf_builders import *
from sauronlab.model.wf_tools import *

FeatureTypeLike = Union[None, int, str, Features, FeatureType]

DEFAULT_CACHE_DIR = sauronlab_env.cache_dir / "wells"


@abcd.auto_eq()
@abcd.auto_repr_str()
class WellCache(AWellCache):
    """
    A cache for WellFrames with a particular feature.
    """

    def __init__(
        self,
        feature: FeatureTypeLike,
        cache_dir: PathLike = DEFAULT_CACHE_DIR,
        dtype=None,
        sensor_cache: Optional[ASensorCache] = None,
    ):
        self.feature = FeatureTypes.of(feature) if feature is not None else None
        cache_dir = Path(cache_dir) / ("-" if self.feature is None else self.feature.internal_name)
        self._cache_dir = Tools.prepped_dir(cache_dir)
        self._dtype = dtype
        self._sensor_cache = sensor_cache

    @abcd.overrides
    def with_sensor_cache(self, sensor_cache: Optional[ASensorCache] = None) -> WellCache:
        self._sensor_cache = sensor_cache
        return self

    @abcd.overrides
    def with_dtype(self, dtype) -> WellCache:
        """
        Returns a copy with dtype set.
        Features will be converted when loaded using ``pd.as_type(dtype)``.

        Args:
            dtype:
        """
        return WellCache(self.feature, self._cache_dir, dtype)

    @property
    def cache_dir(self) -> Path:
        return self._cache_dir

    @abcd.overrides
    def path_of(self, run: RunLike) -> Path:
        run = Tools.run(run)
        return self.cache_dir / (str(run.id) + ".feather")

    @abcd.overrides
    def key_from_path(self, path: PathLike) -> RunLike:
        path = Path(path).relative_to(self.cache_dir)
        return int(regex.compile(r"^([0-9]+)\.feather", flags=regex.V1).fullmatch(path.name).group(1))

    @abcd.overrides
    def load_multiple(self, runs: RunsLike) -> WellFrame:
        runs = Tools.runs(runs)
        self.download(*runs)
        return WellFrame.concat(*[self.load(r) for r in runs])

    @abcd.overrides
    def load(self, run: RunLike) -> WellFrame:
        run = Tools.run(run)
        self.download(run)
        return self._load(run)

    @abcd.overrides
    def download(self, *runs: RunsLike) -> None:
        runs = {r for r in Tools.runs(runs) if r not in self}
        missing = {r for r in runs if not self.contains(r)}
        logger.debug(f"got {missing} as missing runs")
        try:
            # TODO: if > 20 runs, split into multiple queries
            wf = (
                WellFrameBuilder.runs(missing)
                .with_sensor_cache(self._sensor_cache)
                .with_feature(self.feature, self._dtype)
                .with_names(WellNamers.well())
                .build()
            )
            self._save(wf)
        except CacheSaveError:
            logger.error(f"Failed on {missing}", exc_info=True)
            raise
        except EmptyCollectionError:
            logger.debug(f"got empty collection, this could just mean nothing was missing from the cache")
            #just means nothing was missing
            pass

    def _load(self, runs: RunsLike) -> WellFrame:
        runs = ValarTools.runs(runs)

        def read(r):
            try:
                # just use plain pd.read_feather right now
                # we'll deserialize at the end
                dfx = SerializedWellFrame.read_feather(self.path_of(r))
                # WellFrameColumnTools.set_useless_cols(dfx)
                return dfx
            except Exception:
                raise CacheSaveError(f"Failed to load run {str(r)} from cache at {self.path_of(r)}")

        raw_df = pd.concat([read(r) for r in runs], sort=False)
        df = WellFrame.deserialize(raw_df)
        # df = df.with_new_names(df["well"])
        if self._dtype is not None:
            df = df.astype(self._dtype)
        return df

    def _save(self, df: WellFrame) -> None:
        for run in df["run"].unique():
            dfc = WellFrame(df[df["run"] == run])
            saved_to = self.path_of(run)
            logger.info(f"Saving run {run} to {saved_to}") #'Logger' object has no attribute 'minor' -CH
            try:
                dfc.serialize().to_feather(str(saved_to), version=2, compression="lz4")
            except Exception:
                raise CacheSaveError(f"Failed to save run {str(run)} to cache at {saved_to}")


__all__ = ["WellCache"]

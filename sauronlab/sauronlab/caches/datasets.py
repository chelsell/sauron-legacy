from sauronlab.caches.caching_wfs import *
from sauronlab.caches.sensor_caches import *
from sauronlab.caches.wf_caches import *
from sauronlab.core.core_imports import *
from sauronlab.model.compound_names import *
from sauronlab.model.features import FeatureType
from sauronlab.model.well_frames import *
from sauronlab.model.well_names import *
from sauronlab.model.wf_tools import *


class Dataset(metaclass=abc.ABCMeta):
    """ """

    def fetch(self) -> WellFrame:
        if self.path.exists():
            df = self.read()
            how = "Loaded cached"
        else:
            logger.notice(f"Downloading {self.name}...")
            df = self._download()
            how = "Downloaded"
        logger.notice(
            f"{how} {self.name} w/ {len(df.unique_runs())} runs, {len(df.unique_names())} names, {len(df)} wells."
        )
        return df

    def read(self) -> WellFrame:
        df = SerializedWellFrame.read_feather(self.path)
        return WellFrame.deseralize(WellFrameColumnTools.set_useless_cols(df))

    @property
    def path(self) -> Path:
        return sauronlab_env.dataset_cache_dir / (self.name.lower() + ".feather")

    @property
    @abcd.override_recommended
    def name(self) -> str:
        """ """
        return self.__class__.__name__

    def _download(self):
        """ """
        raise NotImplementedError()


class Datasets:
    @classmethod
    def create(
        cls,
        name: str,
        feature: FeatureType,
        today: datetime,
        wheres: Sequence[peewee.Expression],
        namer: WellNamer = WellNamers.well(),
        compound_namer: CompoundNamer = CompoundNamers.inchikey(),
        post_process: Optional[Callable[[WellFrame], WellFrame]] = None,
    ):
        sensor_cache = SensorCache()
        cache = WellCache(feature, sensor_cache=sensor_cache)

        class X(Dataset):
            @property
            @abcd.overrides
            def name(self) -> str:
                return name

            def _download(self):
                query = (
                    CachingWellFrameBuilder(cache, today)
                    .with_feature(feature)
                    .with_sensor_cache(sensor_cache)
                    .with_compound_names(compound_namer)
                    .with_names(namer)
                    .where((~ControlTypes << ValarTools.trash_controls()))
                )
                for where in wheres:
                    query = query.where(where)
                df = query.build().subset(1, 101998)
                if post_process is not None:
                    df = post_process(df)
                return df

        X.__name__ = name.capitalize() + "Dataset"

        return X()


__all__ = ["Dataset", "Datasets"]

from __future__ import annotations

from sauronlab.core.core_imports import *
from sauronlab.model.audio import Waveform
from sauronlab.model.cache_interfaces import AStimCache
from sauronlab.model.stim_frames import BatteryStimFrame

DEFAULT_UNEXPANDED_CACHE_DIR = sauronlab_env.cache_dir / "batteries" / "unexpanded"
DEFAULT_EXPANDED_CACHE_DIR = sauronlab_env.cache_dir / "batteries" / "expanded"


@abcd.auto_repr_str()
@abcd.auto_eq()
class StimframeCache(AStimCache):
    """
    A cache for BatteryStimFrames.
    """

    def __init__(
        self,
        cache_dir: PathLike = None,
        waveform_loader: Optional[Callable[[str], Waveform]] = None,
    ):
        self.waveform_loader = waveform_loader
        if cache_dir is None:
            cache_dir = (
                DEFAULT_EXPANDED_CACHE_DIR if self.is_expanded else DEFAULT_UNEXPANDED_CACHE_DIR
            )
        self._cache_dir = Tools.prepped_dir(cache_dir)

    @property
    def cache_dir(self) -> Path:
        return self._cache_dir

    @property
    def is_expanded(self) -> bool:
        return self.waveform_loader is not None

    @abcd.overrides
    def path_of(self, battery: BatteryLike) -> Path:
        if not isinstance(battery, int):  # avoid query
            battery = Batteries.fetch(battery).id
        return self.cache_dir / (str(battery) + ".feather")

    @abcd.overrides
    def key_from_path(self, path: PathLike) -> BatteryLike:
        path = Path(path).relative_to(self.cache_dir)
        return int(
            regex.compile(r"^([0-9]+)\.csv\.gz", flags=regex.V1).fullmatch(path.name).group(1)
        )

    @abcd.overrides
    def load(self, battery: BatteryLike) -> BatteryStimFrame:
        self.download(battery)
        return self._load(battery)

    @abcd.overrides
    def download(self, *batteries: BatteryLike) -> None:
        for battery in batteries:
            battery = Batteries.fetch(battery)
            is_legacy = ValarTools.battery_is_legacy(battery)
            if battery not in self:
                logger.trace(
                    f"Downloading battery {battery.id} ({battery.name})"
                )  # No logging.minor can be found -CH
                stimframes = BatteryStimFrame.of(battery)
                if self.is_expanded:
                    logger.trace(
                        f"Inserting waveform into battery {battery.id} ({battery.name})"
                    )  # No logging.minor can be found -CH
                    stimframes.expand_audio_inplace(self.waveform_loader, is_legacy=is_legacy)
                # noinspection PyTypeChecker
                self._save(battery, stimframes)

    def _load(self, battery: BatteryLike) -> BatteryStimFrame:
        battery = Batteries.fetch(battery)
        try:
            logger.debug(f"Loading cached battery battery {battery.id}")
            df = pd.read_feather(self.path_of(battery.id))
        except Exception as e:
            raise CacheLoadError(f"Failed to load stimframes for battery {battery.id}") from e
        return BatteryStimFrame._gen_from(battery).convert(df)

    def _save(self, battery, bsf) -> None:
        try:
            with Tools.silenced(no_stderr=True, no_stdout=True):
                saved_to = self.path_of(battery.id)
                logger.info(f"Saving battery {battery.id} to {saved_to}")
                bsf.reset_index().to_feather(str(saved_to))
        except Exception as e:
            raise XValueError(f"Failed to save stimframes for battery {battery.id}") from e

    def __repr__(self):
        return f"{type(self).__name__}('{self.cache_dir}'/{self.is_expanded})"

    def __str__(self):
        return repr(self)


__all__ = ["StimframeCache"]

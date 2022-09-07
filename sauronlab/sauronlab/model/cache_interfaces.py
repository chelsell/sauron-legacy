from __future__ import annotations

import pydub

from sauronlab.core.core_imports import *
from sauronlab.core.valar_singleton import *
from sauronlab.model.assay_frames import AssayFrame
from sauronlab.model.audio import *
from sauronlab.model.sensors import *
from sauronlab.model.stim_frames import BatteryStimFrame
from sauronlab.model.well_frames import *

KEY = TypeVar("KEY")
VALUE = TypeVar("VALUE")


class ASauronxVideo(metaclass=ABCMeta):
    """"""


@abcd.auto_repr_str()
@abcd.auto_hash()
@abcd.auto_eq()
class ASauronlabCache(Generic[KEY, VALUE], metaclass=ABCMeta):
    """ """

    @property
    def cache_dir(self) -> Path:
        """ """
        raise NotImplementedError()

    def path_of(self, key: KEY) -> Path:
        raise NotImplementedError()

    def key_from_path(self, path: PathLike) -> KEY:
        raise NotImplementedError()

    def download(self, *keys: KEY) -> None:
        raise NotImplementedError()

    def load(self, key: KEY) -> VALUE:
        raise NotImplementedError()

    def contains(self, key: KEY) -> bool:
        return self.path_of(key).exists()

    def contents(self) -> Sequence[KEY]:
        lst = []
        for path in self.cache_dir.iterdir():
            k = self.key_from_path(path)
            ## it might not be a relevant file (ex thumbs.db)
            if k is not None:
                lst.append(k)
        return lst

    def delete(self, key: KEY) -> None:
        # TOD delete directories
        path = self.path_of(key).relative_to(self.cache_dir).parts
        if self.contains(key):
            self.path_of(key).unlink()

    def __contains__(self, key: KEY) -> bool:
        return self.contains(key)

    def __delitem__(self, key: KEY) -> None:
        self.delete(key)

    def __getitem__(self, key: KEY) -> VALUE:
        return self.load(key)


class AWellCache(ASauronlabCache[RunLike, WellFrame], metaclass=ABCMeta):
    """"""

    def load_multiple(self, runs: RunsLike) -> WellFrame:
        raise NotImplementedError()

    def with_dtype(self, dtype) -> AWellCache:
        raise NotImplementedError()


class ASensorCache(ASauronlabCache[Tup[SensorNames, RunLike], SensorDataLike], metaclass=ABCMeta):
    """"""


class AAssayCache(ASauronlabCache[BatteryLike, AssayFrame], metaclass=ABCMeta):
    """"""


class AStimCache(ASauronlabCache[BatteryLike, BatteryStimFrame], metaclass=ABCMeta):
    """"""

    @property
    def is_expanded(self):
        """"""
        raise NotImplementedError()


class StimulusWaveform(Waveform):
    """"""

    pass


class AVideoCache(ASauronlabCache[RunLike, ASauronxVideo], metaclass=ABCMeta):
    """"""


class AnAudioStimulusCache(ASauronlabCache[StimulusLike, Path], metaclass=ABCMeta):
    """ """

    def load_pydub(self, name: str) -> pydub.AudioSegment:
        raise NotImplementedError()

    def load_waveform(self, stimulus) -> StimulusWaveform:
        raise NotImplementedError()


__all__ = [
    "ASauronlabCache",
    "ASensorCache",
    "AWellCache",
    "AAssayCache",
    "AStimCache",
    "AnAudioStimulusCache",
    "AVideoCache",
    "StimulusWaveform",
    "ASauronxVideo",
]

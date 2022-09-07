import pydub

from sauronlab.core.core_imports import *
from sauronlab.core.environment import sauronlab_env
from sauronlab.model.cache_interfaces import AnAudioStimulusCache, StimulusWaveform

DEFAULT_CACHE_DIR = sauronlab_env.cache_dir / "stimuli"


@abcd.auto_eq()
@abcd.auto_repr_str()
class AudioStimulusCache(AnAudioStimulusCache):
    """
    A cache for audio files for stimuli.
    """

    def __init__(self, cache_dir: PathLike = DEFAULT_CACHE_DIR):
        self._cache_dir = Tools.prepped_dir(cache_dir)

    @property
    def cache_dir(self) -> Path:
        """ """
        return self._cache_dir

    @abcd.overrides
    def path_of(self, stimulus: StimulusLike) -> Path:
        return self.cache_dir / (stimulus.name + ".wav")

    @abcd.overrides
    def key_from_path(self, path: PathLike) -> StimulusLike:
        pass

    @abcd.overrides
    def load(self, stimulus: StimulusLike) -> Path:
        stimulus = Stimuli.fetch(stimulus)
        self.download(stimulus)
        return self.path_of(stimulus)

    @abcd.overrides
    def download(self, *keys: StimulusLike) -> None:
        for stimulus in keys:
            stimulus = Stimuli.fetch(stimulus)
            tmpfile = self.path_of(stimulus)
            logger.info(f"Downloading audio for stimulus {stimulus}")
            if tmpfile.exists():
                return
            if stimulus.audio_file_id is None:
                raise ValarLookupError(f"No audio file for {stimulus.name}")
            audio_file = AudioFiles.fetch(stimulus.audio_file_id)
            if audio_file.data is None:
                raise DataIntegrityError(f"Audio file for stimulus {stimulus.name} has no data")
            fmt_str = Path(audio_file.filename).suffix.lstrip(".")
            try:
                # TODO constant framerate
                song = pydub.AudioSegment(
                    data=audio_file.data, sample_width=2, frame_rate=44100, channels=1
                )
            except Exception:
                raise DataIntegrityError(f"Audio file for stimulus {stimulus.name} is invalid")
            song.export(tmpfile, format=fmt_str)

    @abcd.overrides
    def load_pydub(self, stimulus: StimulusLike) -> pydub.AudioSegment:
        path = self.load(stimulus)
        try:
            return pydub.AudioSegment.from_file(path)
        except Exception:
            raise DataIntegrityError(f"Failed to read file {path}")

    @abcd.overrides
    def load_waveform(self, stimulus: StimulusLike) -> StimulusWaveform:
        import soundfile

        stimulus = Stimuli.fetch(stimulus)
        path = self.load(stimulus)
        try:
            data, sampling_rate = soundfile.read(str(path))
        except Exception:
            raise LoadError(f"Failed to read file {path}")
        return StimulusWaveform(
            stimulus.name, str(path), data, sampling_rate, -1, 1, stimulus.description
        )


__all__ = ["StimulusWaveform", "AudioStimulusCache"]

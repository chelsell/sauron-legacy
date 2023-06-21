import math
from typing import Optional, Union

import pydub
import simpleaudio as sa

# these are slightly misused here
from pocketutils.core.exceptions import BadWriteError, UnrecognizedKeyError

from .configuration import config


class AudioInfo:
    def __init__(self, wave_obj: sa.WaveObject, duration_ms: Optional[float], intensity: float):
        self.wave_obj = wave_obj
        self.duration_ms = duration_ms
        self.intensity = intensity

    def __str__(self):
        return "AudioInfo({}ms@{}dB)".format(self.duration_ms, round(self.intensity, 5))

    @staticmethod
    def build(stimulus: Union[int, str], applied_length: Optional[int] = None, volume: int = 255):
        import valarpy.model as model

        if isinstance(stimulus, model.AudioFiles):
            audio = stimulus
        elif isinstance(stimulus, model.Stimuli):
            audio = (
                model.AudioFiles.select(model.AudioFiles, model.Stimuli)
                .join(model.Stimuli)
                .where(model.Stimuli.id == int(stimulus.id))
                .first()
            )
        elif isinstance(stimulus, int) or isinstance(stimulus, str) and stimulus.isdigit():
            audio = (
                model.AudioFiles.select(model.AudioFiles, model.Stimuli)
                .join(model.Stimuli)
                .where(model.Stimuli.id == int(stimulus))
                .first()
            )
        else:
            audio = (
                model.AudioFiles.select(model.AudioFiles, model.Stimuli)
                .join(model.Stimuli)
                .where(model.Stimuli.name == stimulus)
                .first()
            )
        if audio is None:
            raise UnrecognizedKeyError("No audio stimulus named {} exists".format(stimulus))
        return AudioInfo._build_audio(audio.id, applied_length, volume)

    @staticmethod
    def _build_audio(audio_file_id: int, applied_length: Optional[int] = None, volume: int = 255):

        if applied_length is not None and applied_length < 0:
            raise BadWriteError(f"File {audio_file_id}: length {applied_length} < 0")
        if volume < 0 or volume > 255:
            raise BadWriteError(f"The volume is {volume} but must be 0–255")

        import valarpy.model as model

        valar_obj = model.AudioFiles.select().where(model.AudioFiles.id == audio_file_id).first()
        if valar_obj is None:
            raise UnrecognizedKeyError(f"No audio file with ID {audio_file_id}")
        song = pydub.AudioSegment(data=valar_obj.data, sample_width=2, frame_rate=44100, channels=1)
        n_sec_valar = valar_obj.n_seconds * 1000
        length_delta = abs(len(song) - n_sec_valar)
        if length_delta > 0.00001:
            raise AssertionError(
                f"File {audio_file_id} is {len(song)}, but Valar says it’s {n_sec_valar}"
            )

        if applied_length is None:
            resized = song
        else:
            n_repeats = math.ceil(applied_length / len(song))
            resized = (song * n_repeats)[0:applied_length]

        if volume == 0 or applied_length == 0:
            final = pydub.AudioSegment.silent(duration=0.5)
        else:
            # noinspection PyTypeChecker
            volume_floor = config.get("sauron.hardware.stimuli.audio.audio_floor")
            volume_ceil = config.get("sauron.hardware.stimuli.audio.audio_ceil")
            # final = resized + (volume * (volume_floor / 255) - volume_floor)
            # print(volume * (volume_ceil - volume_floor) / 255 + volume_floor)
            final = resized + volume * (volume_ceil - volume_floor) / 255 + volume_floor

        play_obj = sa.WaveObject(final.raw_data, 1, 2, 44100)

        return AudioInfo(play_obj, applied_length, volume)


__all__ = ["AudioInfo"]

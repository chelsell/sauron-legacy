from enum import Enum
from typing import Optional, Union

from .audio import AudioInfo
from .configuration import config


class StimulusType(Enum):
    ANALOG = 1
    DIGITAL = 2
    AUDIO = 3


class Stimulus:
    def __init__(
        self,
        valar_stimulus,
        byte_intensity: Union[int, float, bool],
        audio_obj: Optional[AudioInfo],
    ) -> None:
        self.valar_stimulus = valar_stimulus
        self.name = valar_stimulus.name.replace(" ", "_")
        self.stim_type = self._determine_stim_type()
        self.byte_intensity = byte_intensity
        self.audio_obj = audio_obj
        # TODO assert audio
        if self.is_audio():
            self.intensity = audio_obj.intensity
        else:
            self.intensity = byte_intensity
        if self.is_digital():
            self.intensity = bool(self.intensity)  # shouldn't be needed

    def is_audio(self) -> bool:
        return self.stim_type == StimulusType.AUDIO

    def is_analog(self) -> bool:
        return self.stim_type == StimulusType.ANALOG

    def is_digital(self) -> bool:
        return self.stim_type == StimulusType.DIGITAL

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return "{}[{}] = {}".format(self.name, self.valar_stimulus.id, self.intensity)

    def __lt__(self, other):
        if isinstance(other, str):
            return False
        return (self.valar_stimulus, self.byte_intensity) < (
            other.valar_stimulus,
            other.byte_intensity,
        )

    def _determine_stim_type(self) -> StimulusType:
        if self.valar_stimulus.audio_file is not None:
            if (
                self.name in config.stimuli["analog_pins"]
                or self.name in config.stimuli["digital_pins"]
            ):
                raise BadConfigException(
                    "{} is in the pins list but is an audio file".format(self.name)
                )
            return StimulusType.AUDIO
        elif self.valar_stimulus.analog:
            if (
                self.name not in config.stimuli["analog_pins"]
                or self.name in config.stimuli["digital_pins"]
            ):
                raise BadConfigException(
                    "{} is analog and should be listed (and only listed) in analog_pins".format(
                        self.name
                    )
                )
            return StimulusType.ANALOG
        else:
            if (
                self.name not in config.stimuli["digital_pins"]
                or self.name in config.stimuli["analog_pins"]
            ):
                raise BadConfigException(
                    "{} is digital and should be listed (and only listed) in digital_pins".format(
                        self.name
                    )
                )
            return StimulusType.DIGITAL


__all__ = ["Stimulus", "StimulusType"]

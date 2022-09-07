from __future__ import annotations

from sauronlab.core.core_imports import *


@enum.unique
class SensorNames(CleverEnum):
    """
    These are standard sensors.
    Any ``SensorCache`` is required to handle all them exactly.
    However, a ``SauronlabSensor`` class might handle a more general case than called for here.
    For example, the current implementation of ``MicrophoneWaveformSensor`` can handle any sampling rate,
    whereas ``SensorNames.MICROPHONE_WAVEFORM`` here specifically uses 1000 Hz, as does the current implementation
    of ``SensorCache``.

    Each choice can be either _composite_ or _raw_.
    Raw sensors correspond to ``Sensors`` rows (possibly multiple),
    and they can be listed in the ``sensors`` section of the ``generations.json`` file.
    See the function ``json_name`` (in general, turns into lowercase and strips 'RAW_').

    Composite functions have a non-empty ``components`` that list the underlying raw sensors.
    Raw sensors of course return an empty list.

    For example, the ``PHOTOSENSOR`` choice is backed by
    ``RAW_PHOTOSENSOR_MILLIS``, ``RAW_PHOTOSENSOR_VALUES``, and ``RAW_STIMULUS_MILLIS``.
    The latter three are simply numpy arrays (saved as ``.npy`` files currently).
    The composite photosensor is trimmed to the empirical start and end of the battery,
    which requires the millisecond values from the stimuli and photosensor recordings.

    As another example, the microphone waveform (``MICROPHONE_WAVEFORM``) requires the trimmed
    audio recording (``MICROPHONE``), which in turn requires
    ``RAW_MICROPHONE_RECORDING``, ``RAW_MICROPHONE_MILLIS``, and ``RAW_STIMULUS_MILLIS``.
    """

    PHOTOSENSOR = ()
    THERMOSENSOR = ()
    MICROPHONE = ()
    MICROPHONE_WAVEFORM = ()
    SECONDARY_CAMERA = ()
    PREVIEW_FRAME = ()
    STIMULUS_MILLIS = ()
    CAMERA_MILLIS = ()
    #
    RAW_SECONDARY_CAMERA = ()
    RAW_PREVIEW_FRAME = ()
    RAW_MICROPHONE_RECORDING = ()
    RAW_MICROPHONE_MILLIS = ()
    RAW_CAMERA_MILLIS = ()
    RAW_STIMULUS_MILLIS = ()
    RAW_STIMULUS_VALUES = ()
    RAW_STIMULUS_IDS = ()
    RAW_PHOTOSENSOR_MILLIS = ()
    RAW_PHOTOSENSOR_VALUES = ()
    RAW_THERMOSENSOR_MILLIS = ()
    RAW_THERMOSENSOR_VALUES = ()

    @property
    def is_raw(self) -> bool:
        return self.name.startswith("RAW_")

    @property
    def is_composite(self) -> bool:
        return not self.name.startswith("RAW_")

    @property
    def components(self) -> Sequence[SensorNames]:
        """
        Lists other SensorNames that this one requires.

        Returns:
            A sequence of ``SensorNames`` choices, which may be empty
        """
        if self == SensorNames.MICROPHONE_WAVEFORM:
            return [SensorNames.MICROPHONE]
        elif self == SensorNames.MICROPHONE:
            return [
                SensorNames.RAW_MICROPHONE_MILLIS,
                SensorNames.RAW_MICROPHONE_RECORDING,
                SensorNames.RAW_STIMULUS_MILLIS,
            ]
        elif self == SensorNames.PHOTOSENSOR:
            return [
                SensorNames.RAW_PHOTOSENSOR_MILLIS,
                SensorNames.RAW_PHOTOSENSOR_VALUES,
                SensorNames.RAW_STIMULUS_MILLIS,
            ]
        elif self == SensorNames.THERMOSENSOR:
            return [
                SensorNames.RAW_THERMOSENSOR_MILLIS,
                SensorNames.RAW_THERMOSENSOR_VALUES,
                SensorNames.RAW_STIMULUS_MILLIS,
            ]
        elif self == SensorNames.STIMULUS_MILLIS:
            return [
                SensorNames.RAW_STIMULUS_IDS,
                SensorNames.RAW_STIMULUS_MILLIS,
                SensorNames.RAW_STIMULUS_VALUES,
            ]
        elif self == SensorNames.CAMERA_MILLIS:
            return [SensorNames.RAW_CAMERA_MILLIS]
        elif self == SensorNames.PREVIEW_FRAME:
            return [SensorNames.RAW_PREVIEW_FRAME]
        elif self == SensorNames.SECONDARY_CAMERA:
            return [SensorNames.RAW_SECONDARY_CAMERA]
        else:
            return []

    @property
    def millis_component(self) -> Optional[SensorNames]:
        return {
            SensorNames.MICROPHONE: SensorNames.RAW_MICROPHONE_MILLIS,
            SensorNames.PHOTOSENSOR: SensorNames.RAW_PHOTOSENSOR_MILLIS,
            SensorNames.THERMOSENSOR: SensorNames.RAW_THERMOSENSOR_MILLIS,
            SensorNames.STIMULUS_MILLIS: SensorNames.RAW_STIMULUS_MILLIS,
            SensorNames.CAMERA_MILLIS: SensorNames.RAW_CAMERA_MILLIS,
        }.get(self)

    @property
    def values_component(self) -> Optional[SensorNames]:
        return {
            SensorNames.MICROPHONE: SensorNames.RAW_MICROPHONE_RECORDING,
            SensorNames.PHOTOSENSOR: SensorNames.RAW_PHOTOSENSOR_VALUES,
            SensorNames.THERMOSENSOR: SensorNames.RAW_THERMOSENSOR_VALUES,
            SensorNames.STIMULUS_MILLIS: SensorNames.RAW_STIMULUS_VALUES,
        }.get(self)

    @property
    def raw_bytes_component(self) -> Optional[SensorNames]:
        return {
            SensorNames.PREVIEW_FRAME: SensorNames.RAW_PREVIEW_FRAME,
            SensorNames.SECONDARY_CAMERA: SensorNames.RAW_SECONDARY_CAMERA,
        }.get(self)

    @property
    def is_timing(self) -> bool:
        return self == SensorNames.CAMERA_MILLIS or self == SensorNames.STIMULUS_MILLIS

    @property
    def is_audio_composite(self) -> bool:
        return self == SensorNames.MICROPHONE

    @property
    def is_audio_waveform(self) -> bool:
        return self == SensorNames.MICROPHONE_WAVEFORM

    @property
    def is_image(self) -> bool:
        return self in [
            SensorNames.PREVIEW_FRAME,
            SensorNames.RAW_PREVIEW_FRAME,
            SensorNames.SECONDARY_CAMERA,
            SensorNames.RAW_SECONDARY_CAMERA,
        ]

    @property
    def is_time_dependent(self) -> bool:
        """
        Returns True if this is a composite sensor that has matching vectors of values and milliseconds.
        (It might also have other accompanying sensors.)
        Always returns False for raw sensors.
        """
        return (
            self is SensorNames.PHOTOSENSOR
            or self is SensorNames.THERMOSENSOR
            or self is SensorNames.MICROPHONE
        )

    @property
    def json_name(self) -> str:
        if self.is_raw:
            return self.name.lower().replace("raw_", "")
        raise KeyError(f"No json_name for composite sensor {self}")


__all__ = ["SensorNames"]

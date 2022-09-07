from __future__ import annotations

from PIL import Image, ImageDraw
from scipy.interpolate import interp1d

from sauronlab.core.core_imports import *
from sauronlab.core.valar_singleton import *
from sauronlab.model.audio import *
from sauronlab.model.sensor_names import SensorNames


class MicrophoneWaveform(Waveform):
    """"""

    pass


@abcd.auto_repr_str()
@abcd.auto_eq()
@abcd.auto_hash()
class _AbsBatteryTimeData(metaclass=abc.ABCMeta):
    """
    BatteryTimeData object (contains start/end timestamps, length of battery, etc.) for a given run.
    These are EITHER empirical or expected.
    """

    def __init__(self, run: RunLike, start_ms: int, end_ms: int):
        """

        Args:
            run:
            start_ms: From the stimulus_millis sensor: specifically ``stimulus_millis[0]``
            end_ms:From the stimulus_millis sensor: specifically ``stimulus_millis[-1]``
        """
        self.run, self.start_ms, self.end_ms = Tools.run(run), int(start_ms), int(end_ms)

    @property
    def start_dt(self) -> datetime:
        """"""
        raise NotImplementedError()

    @property
    def end_dt(self) -> datetime:
        """"""
        raise NotImplementedError()

    @property
    def n_ms(self) -> int:
        """"""
        return self.end_ms - self.start_ms

    def __len__(self) -> int:
        return len(self.data)


class EmpiricalBatteryTimeData(_AbsBatteryTimeData):
    """
    BatteryTimeData object (contains start/end timestamps, length of battery, etc.) for a given run.
    These are the empirical values, not the expected ones!
    """

    @property
    def start_dt(self) -> datetime:
        """"""
        return self.run.datetime_run + timedelta(milliseconds=self.start_ms)

    @property
    def end_dt(self) -> datetime:
        """"""
        return self.run.datetime_run + timedelta(milliseconds=self.end_ms)


class ExpectedBatteryTimeData(_AbsBatteryTimeData):
    """
    BatteryTimeData object (contains start/end timestamps, length of battery, etc.) for a given run.
    The start time is empirical
    """

    @property
    def start_dt(self) -> datetime:
        """"""
        return self.run.datetime_run + timedelta(milliseconds=self.start_ms)

    @property
    def end_dt(self) -> datetime:
        """"""
        battery = self.run.experiment.battery
        return self.start_dt + timedelta(
            seconds=battery.length / ValarTools.battery_stimframes_per_second(battery)
        )


class SauronlabSensor:
    """"""

    def __init__(self, run: RunLike, sensor_data: Union[SensorDataLike, Image.Image]):
        """
        Sensor wrapper object that holds converted sensor_data for a given run.

        Args:
            run: Run ID, Submission ID, Submission Object, or Run Object
            sensor_data: Converted Sensor_data

        """
        self._sensor_data = sensor_data
        self._run = Runs.fetch(run)

    @property
    def run(self) -> Runs:
        """ """
        return self._run

    @property
    def data(self) -> Union[SensorDataLike, Image.Image]:
        """ """
        return self._sensor_data

    @property
    def name(self) -> str:
        """ """
        return Tools.strip_off_end(self.__class__.__name__.lower(), "sensor")

    @property
    def abbrev(self) -> str:
        """ """
        raise NotImplementedError()

    @property
    def symbol(self) -> str:
        """ """
        raise NotImplementedError()

    def __str__(self):
        return "{}(r{} ℓ={})".format(
            self.__class__.__name__,
            self.run.id,
            len(self._sensor_data) if hasattr(self._sensor_data, "__len__") else "?",
        )

    def __repr__(self):
        return "{}(r{} ℓ={} @{})".format(
            self.__class__.__name__,
            self.run.id,
            len(self._sensor_data) if hasattr(self._sensor_data, "__len__") else "?",
            str(hex(id(self))),
        )


class TimeDataSensor(SauronlabSensor, metaclass=abc.ABCMeta):
    """
    BatteryTimeData object (contains start/end timestamps, length of battery, etc.) for a given run.
    These are the empirical values, not the expected ones!

    """

    def __init__(self, run: RunLike, battery_data: np.array):
        super().__init__(run, battery_data)
        self.planned_battery_n_ms = run.experiment.battery.length

    def timestamps(self) -> Sequence[datetime]:
        """ """
        return [self.run.datetime_run + timedelta(milliseconds=int(ms)) for ms in self.data]

    def timestamp_at(self, ind: int) -> datetime:
        """


        Args:
            ind: int:

        Returns:

        """
        return self.run.datetime_run + timedelta(milliseconds=int(self.data[ind]))

    @property
    def start_ms(self) -> int:
        """ """
        return self._sensor_data[0]

    @property
    def end_ms(self) -> int:
        """ """
        return self._sensor_data[-1]

    @property
    def n_ms(self) -> float:
        """ """
        # noinspection PyUnresolvedReferences
        return (self._sensor_data[1] - self._sensor_data[0]).total_seconds() * 1000

    @property
    def start_end_dts(self) -> Tup[datetime, datetime]:
        """ """
        return self.timestamp_at(0), self.timestamp_at(-1)

    def __len__(self) -> int:
        return len(self.data)


class StimulusTimeData(TimeDataSensor):
    """ """

    @property
    def abbrev(self) -> str:
        """ """
        return "stim"

    @property
    def symbol(self) -> str:
        """ """
        return "⚑"


class CameraTimeData(TimeDataSensor):
    """"""

    @property
    def abbrev(self) -> str:
        """ """
        return "frame"

    @property
    def symbol(self) -> str:
        """ """
        return "🎥"


class RawDataSensor(SauronlabSensor):
    """"""

    @property
    def abbrev(self) -> str:
        """ """
        return "raw"

    @property
    def symbol(self) -> str:
        """ """
        return "⚒"


class ImageSensor(SauronlabSensor):
    def __init__(self, run: RunLike, sensor_data: SensorDataLike):
        """
        Sensor that holds Image sensor data (Webcam and Preview). Applies grid if it holds preview data.

        Args:
            run: Run ID, Submission ID, Submission Object, or Run Object
            sensor_data: Converted image sensor data (Webcam/Preview)

        Returns:

        """
        super().__init__(run, sensor_data)

    @property
    def data(self) -> Image.Image:
        """ """
        return self._sensor_data

    def draw_roi_grid(
        self, color: str = "black", roi_ref: Union[int, str, Refs] = 63
    ) -> SauronlabSensor:
        """
        Draws a grid, returning a new ImageSensor.

        Args:
            color: A color code recognized by PIL (Python Imaging Library), such as a hex code starting with #
            roi_ref: The reference from which to obtain the ROIs; the default is the sauronx ROI set from the TOML,
                     which may or may not exist

        Returns:
            A copy of this ImageSensor

        """
        new = deepcopy(self)
        draw = ImageDraw.Draw(new.data)
        roi_ref = Refs.fetch(roi_ref).id
        rois = list(
            Rois.select(Rois, Wells)
            .join(Wells)
            .where(Wells.run_id == self.run.id)
            .where(Rois.ref == roi_ref)
        )
        wb1 = Tools.wb1_from_run(self.run)
        if len(rois) != wb1.n_wells:
            raise LengthMismatchError(f"{len(rois)} rois but {wb1.n_wells} wells")
        for w in rois:
            draw.rectangle((w.x0, w.y0, w.x1, w.y1), outline=color)
        return new

    @property
    def abbrev(self) -> str:
        return "img"

    @property
    def symbol(self) -> str:
        return "📷"

    def __str__(self):
        return "{}(r{} w={},h={})".format(
            self.__class__.__name__, self.run.id, self._sensor_data.width, self._sensor_data.height
        )

    def __repr__(self):
        return "{}(r{} w={},h={} @ {})".format(
            self.__class__.__name__,
            self.run.id,
            self._sensor_data.width,
            self._sensor_data.height,
            str(hex(id(self))),
        )


class SecondaryCameraSensor(ImageSensor):
    """"""


class PreviewFrameSensor(ImageSensor):
    """"""


class TimeDepSauronlabSensor(SauronlabSensor, metaclass=abc.ABCMeta):
    """ """

    def __init__(
        self,
        run: RunLike,
        timing_data: np.array,
        sensor_data: np.array,
        battery_data: EmpiricalBatteryTimeData,
        samples_per_sec: Optional[int],
    ):
        """
        Sensor data for sensors that have a time component

        Args:
            run: Run ID, Submission ID, Submission Object, or Run Object
            timing_data: Converted Timing Data
            sensor_data: Converted Sensor Data
            battery_data: BatteryTimeData object
            samples_per_sec: For example, audio files typically use 44100 Hz; keep None if the sampling is not even
        """
        super().__init__(run, sensor_data)
        self._bt_data = battery_data
        self._timing_data = timing_data
        self._samples_per_sec = samples_per_sec
        if len(self.timing_data) != len(self.data):
            logger.error(
                f"{self.__class__.__name__}: Millis length={len(self.timing_data)} but data length={len(self.data)} for r{run.id}"
            )

    @property
    def samples_per_sec(self) -> int:
        """ """
        return self._samples_per_sec

    @property
    def values_per_ms(self) -> int:
        """ """
        raise NotImplementedError()

    @property
    def timing_data(self) -> np.array:
        """ """
        return self._timing_data

    @property
    def bt_data(self) -> EmpiricalBatteryTimeData:
        """ """
        return self._bt_data

    def interpolate(self, step_ms: int = 1, kind: str = "zero", **kwargs) -> __qualname__:
        n_samples = int(np.round(float(self.bt_data.n_ms) / step_ms))
        new_timing = np.linspace(self.timing_data[0], self.timing_data[-1], n_samples)
        interp = interp1d(self.timing_data, self.data, kind=kind, **kwargs)
        values = interp(new_timing)
        return self.__class__(
            self.run, new_timing, values, copy(self.bt_data), self.samples_per_sec
        )

    def slice_ms(self, start_ms: Optional[int], end_ms: Optional[int]) -> __qualname__:
        """
        Slices Sensor data

        Args:
            start_ms:
            end_ms:

        Returns:
            A copy of this class

        """
        started = self.bt_data.start_ms if start_ms is None else self.bt_data.start_ms + start_ms
        finished = self.bt_data.end_ms if end_ms is None else self.bt_data.end_ms + end_ms
        msvals: np.array = self.timing_data
        t0 = np.searchsorted(msvals, started, side="left")
        t1 = np.searchsorted(msvals, finished, side="right")
        return self.__class__(
            self.run, msvals[t0:t1], self.data[t0:t1], copy(self.bt_data), self.samples_per_sec
        )

    def __len__(self) -> int:
        return len(self.data)


class PhotosensorSensor(TimeDepSauronlabSensor):
    """ """

    @property
    def abbrev(self) -> str:
        return "photo"

    @property
    def symbol(self) -> str:
        return "🌣"

    @property
    def values_per_ms(self) -> int:
        """ """
        return 1


class ThermosensorSensor(TimeDepSauronlabSensor):
    """"""

    @property
    def abbrev(self) -> str:
        return "therm"

    @property
    def symbol(self) -> str:
        return "🌡"

    @property
    def values_per_ms(self) -> int:
        """ """
        return 1


class AccelSensor(TimeDepSauronlabSensor):
    """
    Acceleration _magnitude_ from an accelerometer.
    """

    @property
    def abbrev(self) -> str:
        return "accel"

    @property
    def symbol(self) -> str:
        return "🏍"

    @property
    def values_per_ms(self) -> int:
        """ """
        return 1


class MicrophoneWaveformSensor(TimeDepSauronlabSensor):
    """ """

    def __init__(
        self,
        run: Runs,
        waveform: MicrophoneWaveform,
        timing_data: np.array,
        battery_data: EmpiricalBatteryTimeData,
        samples_per_sec: int,
    ):
        super().__init__(run, timing_data, waveform.data, battery_data, samples_per_sec)
        self._waveform = waveform

    @property
    def waveform(self) -> MicrophoneWaveform:
        return self._waveform

    @property
    def abbrev(self) -> str:
        return "audio"

    @property
    def symbol(self) -> str:
        return "🔊"

    @property
    def values_per_ms(self) -> float:
        """ """
        return self.samples_per_sec * 1000


class MicrophoneSensor(TimeDepSauronlabSensor):
    """ """

    @property
    def abbrev(self) -> str:
        return "mic"

    @property
    def symbol(self) -> str:
        return "🎤"

    @property
    def values_per_ms(self) -> float:
        """ """
        return 44.1  # TODO 44100 kHz

    def waveform(self, downsample_to_hertz: int) -> MicrophoneWaveformSensor:
        """


        Args:
            downsample_to_hertz:

        Returns:

        """
        waveform = MicrophoneWaveform(
            name="r" + str(self.run.id),
            path=None,
            data=self.data,
            sampling_rate=self.samples_per_sec,
            minimum=None,
            maximum=None,
            description=self.run.name,
            start_ms=None,
            end_ms=None,
        )
        waveform = waveform.downsample(downsample_to_hertz, resample=False)
        waveform = waveform.normalize()
        # TODO /1000 / downsample_to_hertz
        n_samples = int(np.round(waveform.n_ms))
        ideal_timing_data = np.linspace(self.timing_data[0], self.timing_data[-1], n_samples)
        return MicrophoneWaveformSensor(
            run=self.run,
            waveform=waveform,
            timing_data=ideal_timing_data,
            battery_data=self.bt_data,
            samples_per_sec=downsample_to_hertz,
        )


__all__ = [
    "SensorNames",
    "SauronlabSensor",
    "TimeDepSauronlabSensor",
    "PhotosensorSensor",
    "MicrophoneSensor",
    "MicrophoneWaveformSensor",
    "ThermosensorSensor",
    "StimulusTimeData",
    "TimeDataSensor",
    "ExpectedBatteryTimeData",
    "EmpiricalBatteryTimeData",
    "ImageSensor",
    "SensorNames",
    "MicrophoneWaveform",
    "CameraTimeData",
    "SensorNames",
    "SecondaryCameraSensor",
    "PreviewFrameSensor",
    "RawDataSensor",
]

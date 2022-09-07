import datetime
import logging
import multiprocessing as mp
import threading
import wave
from enum import Enum
from multiprocessing import Process
from os.path import dirname
from typing import Dict, List

import numpy as np
import pandas as pd
import pyaudio

# from scipy.io import wavfile  # TODO broken
from hipsterplot import HipsterPlotter

from sauronx import stamp

from .arduino import Board
from .configuration import config
from .paths import *


class SensorParams:
    # this allows us to add new info without refactoring
    def __init__(self, duration: int, output_dir: str):
        self.duration = duration
        self.output_dir = output_dir


class SensorTrigger(Enum):
    """Start times for sensors."""

    CAMERA_START = 1
    EXPERIMENT_START = 0
    SOUND_TEST = 4
    LIGHT_TEST = 5
    TEMPERATURE_TEST = 6


class Sensor:

    # triggers = None  # type: list of SensorTrigger

    def __init__(self, params: SensorParams) -> None:
        self.params = params
        # logging.info("Set up {}".format(self.name()))

    def file_path(self) -> str:
        raise NotImplementedError()

    @classmethod
    def sensor_name(cls) -> str:
        return cls.__name__.lower()

    def __str__(self):
        return self.name()

    def name(self) -> str:
        return self.__class__.__name__.lower()

    def start(self, **kwargs) -> None:
        raise NotImplementedError()

    def test(self, **kwargs) -> None:
        raise NotImplementedError()

    def save(self, **kwargs) -> None:
        raise NotImplementedError()

    def term(self) -> None:
        pass  # assume it closes automatically

    def _record(self, *args) -> None:
        raise NotImplementedError()

    def plot(self) -> str:
        return ""

    def _get_board(self, kwargs) -> Board:
        try:
            return kwargs["board"]
        except KeyError:
            raise KeyError(
                "The sensor was not passed an initialized PyMata board object and could not start"
            )


class Microphone(Sensor):

    triggers = [SensorTrigger.EXPERIMENT_START, SensorTrigger.SOUND_TEST]

    def __init__(self, params: SensorParams) -> None:
        super(Microphone, self).__init__(params)
        self.params = params
        self.coll = config.get_coll(self.params.output_dir)
        self._stream = None
        self._p = None
        self._timestamps = None
        self._frames = None
        self.audio_format = pyaudio.paInt32
        self.channels = 1
        self.sample_rate = int(config.sensors["microphone.sample_rate"])
        self.frames_per_buffer = int(config.sensors["microphone.frames_per_buffer"])
        self.log_file = None
        self.should_kill = [None]
        self._thread = threading.Thread(target=self._record)

    def file_path(self) -> str:
        # TODO
        return self.coll.microphone_wav_path()

    def timestamp_file_path(self) -> str:
        # TODO
        return self.coll.microphone_timestamps_path()

    def start(self, **kwargs) -> None:
        logging.debug("Recording {} to {}".format(self.name(), self.file_path()))
        self.log_file = self.file_path()
        self._init()
        self._thread.start()

    def test(self, **kwargs) -> None:
        log_file_path = kwargs["log_file_path"]
        self.log_file = log_file_path
        logging.debug("Recording {} to {}".format(self.name(), log_file_path))
        self._init()
        self._record()

    def _init(self):
        make_dirs(dirname(self.log_file))
        self.timestamps = []
        self.frames = []
        try:
            self._p = pyaudio.PyAudio()
            self._stream = self._p.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.frames_per_buffer,
            )
        except Exception as e:
            logging.exception("Failed to start microphone.")
            warn_user("Failed to start microphone.")
            raise e
        self.should_kill = [False]

    def _record(self) -> None:
        # TODO exception handling got a bit much here
        try:
            while not self.should_kill[0]:
                data = self._stream.read(self.frames_per_buffer)
                self.frames.append(data)
                self.timestamps.append(datetime.datetime.now())
        except Exception as e:
            logging.exception("Microphone failed while capturing")
            warn_user("Microphone failed while capturing")
            raise e
        self.save()
        self._kill()

    def term(self):
        self.should_kill[0] = True

    def save(self):
        try:
            logging.info("Writing microphone data...")
            logging.debug("Writing microphone timestamps")
            with open(self.timestamp_file_path(), "w") as f:
                for ts in self.timestamps:
                    f.write(stamp(ts) + "\n")
            logging.debug("Writing microphone WAV data")
            wf = wave.open(self.log_file, "wb")
            try:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self._p.get_sample_size(self.audio_format))
                wf.setframerate(self.sample_rate)
                wf.writeframes(b"".join(self.frames))
            finally:
                wf.close()
        except Exception as e:
            warn_user("Microphone failed while writing the .wav file")
            raise e
        logging.info("Finished writing microphone data.")

    def plot(self):
        logging.info("Plotting microphone data (may take a couple minutes)...")
        logging.warning("Sometimes plotting the microphone data can crash the interpreter.")
        from scipy.io import wavfile

        with open(self.file_path(), "rb") as f:
            sampling_rate, data = wavfile.read(f)
            ms = np.array([i / sampling_rate * 1000 for i in range(0, len(data))])
        low_x = self.timestamps[0].strftime("%H:%M:%S")
        high_x = self.timestamps[-1].strftime("%H:%M:%S")
        s = HipsterPlotter(num_y_chars=10).plot(
            data, title=self.name(), low_x_label=low_x, high_x_label=high_x
        )
        with open(self.file_path() + ".plot.txt", "w", encoding="utf8") as f:
            f.write(s)
        return s

    def _kill(self):
        logging.info("Terminating microphone...")
        logging.debug("Ending microphone process")
        try:
            self._p.terminate()  # failing here is probably bad
        except Exception as b:
            logging.warning("Failed to terminate microphone process")
            logging.debug(b, exc_info=True)
        logging.debug("Ending microphone stream")
        try:
            self._stream.stop_stream()
        except Exception as b:
            logging.warning("Failed to stop microphone stream")
            logging.debug(b, exc_info=True)
        logging.debug("Closing microphone stream")
        try:
            self._stream.close()
        except Exception as b:
            logging.warning("Failed to close microphone process")
            logging.debug(b, exc_info=True)
        self._p = None  # ; self._thread = None
        logging.debug("Microphone exited")
        logging.info("Terminated microphone.")


class CsvSensor(Sensor):
    def _record(self, data) -> None:
        self.vals.append((data[2], datetime.datetime.now()))

    def start(self, **kwargs) -> None:
        logging.debug("Recording {} to {}".format(self.name(), self.file_path()))
        self.board = self._get_board(kwargs)
        make_dirs(dirname(self.file_path()))
        self.board.register_sensor(self.pin, self._record)

    def test(self, **kwargs) -> None:
        self.start(**kwargs)

    def term(self):
        self.save()
        if self.board is not None:  # None if it failed before initializing
            self.board.reset_sensor(self.pin)

    def save(self):
        with open(self.file_path(), "w", encoding="utf8") as log_file:
            log_file.write("Value,Time\n")
            for v, t in self.vals:
                log_file.write("%s,%s\n" % (v, t))
        logging.info("Saved {} data".format(self.name()))

    def plot(self):
        fmt = "%Y-%m-%d %H:%M:%S.%f"
        df = pd.read_csv(self.file_path())
        if len(df) == 0:
            return "{}: <no data>".format(self.sensor_name())
        low_x = datetime.datetime.strptime(df["Time"].iloc[0], fmt).strftime("%H:%M:%S")
        high_x = datetime.datetime.strptime(df["Time"].iloc[-1], fmt).strftime("%H:%M:%S")
        s = HipsterPlotter(num_y_chars=10).plot(
            df["Value"], title=self.name(), low_x_label=low_x, high_x_label=high_x
        )
        with open(self.file_path() + ".plot.txt", "w", encoding="utf8") as f:
            f.write(s)
        return s


class Thermometer(CsvSensor):

    triggers = [SensorTrigger.EXPERIMENT_START, SensorTrigger.TEMPERATURE_TEST]

    def __init__(self, params: SensorParams) -> None:
        super(Thermometer, self).__init__(params)
        self.board = None
        self.params = params
        self.pin = int(config.sensors["analog_pins.thermometer"])
        self.vals = []

    def file_path(self) -> str:
        return pjoin(self.params.output_dir, "sensors", "thermometer_log.csv")


class Photometer(CsvSensor):
    triggers = [SensorTrigger.EXPERIMENT_START, SensorTrigger.LIGHT_TEST]

    def __init__(self, params: SensorParams) -> None:
        super(Photometer, self).__init__(params)
        self.params = params
        self.pin = int(config.sensors["analog_pins.photometer"])
        self.vals = []

    def file_path(self) -> str:
        return pjoin(self.params.output_dir, "sensors", "photometer_log.csv")


class SensorRegistry:

    permitted = [Microphone, Thermometer, Photometer]
    enabled = None  # type: List[type]
    params = None  # type: SensorParams
    _ready = None  # type: Dict[SensorTrigger, List[Sensor]]
    _name_to_sensor = {s.sensor_name(): s for s in permitted}

    def __init__(self, params: SensorParams) -> None:
        self.params = params
        self.enabled = []
        for sensor in self.permitted:
            if sensor.sensor_name() in config.sensors["registry"]:
                self.enabled.append(sensor)
        for sensor in config.sensors["registry"]:
            assert sensor in [
                z.sensor_name() for z in self.permitted
            ], "Sensor {} not found".format(sensor)
        regs = (
            ": " + ", ".join([str(z.sensor_name()) for z in self.enabled])
            if len(self.enabled) > 0
            else ""
        )
        logging.info("Detected {} registered sensors{}".format(len(self.enabled), regs))
        self._ready = {trigger: [] for trigger in SensorTrigger}

    def fetch(self):
        x = []
        for k, v in self._ready.items():
            x.extend(v)
        return x

    def __len__(self) -> int:
        return len(self.enabled)

    def __contains__(self, item):
        if isinstance(item, str):
            return self._name_to_sensor[item] in self.enabled
        elif isinstance(item, type):
            # a bit weird, but I feel safer about matching on the name
            if not hasattr(item, "sensor_name"):
                raise TypeError(
                    "Must look up sensor by name or Sensor class; got invalid type {}.".format(
                        item.__name__
                    )
                )
            return self._name_to_sensor[item.sensor_name()] in self.enabled
        else:
            raise TypeError("Must look up sensor by name or Sensor class; got {}.".format(item))

    def ready(self, trigger: SensorTrigger) -> None:
        logging.debug("Readying sensors to start with trigger {}".format(trigger))
        for sensor in self.enabled:
            if trigger in sensor.triggers:
                self._ready[trigger].append(sensor(self.params))

    def start(self, trigger: SensorTrigger, board: object = None) -> None:
        logging.debug("Firing sensors for trigger {}".format(trigger))
        for sensor in self._ready[trigger]:
            sensor.start(board=board)

    def test(self, trigger: SensorTrigger, board: object = None, file_path: str = None) -> None:
        logging.debug("Firing sensors for trigger {}".format(trigger))
        for sensor in self._ready[trigger]:
            sensor.test(board=board, log_file_path=file_path)

    def save(self, trigger: SensorTrigger) -> None:
        logging.debug("Saving sensors for trigger {}".format(trigger))
        for sensor in self._ready[trigger]:
            sensor.save()

    def terminate(self, trigger: SensorTrigger) -> None:
        logging.debug("Deactivating sensors for trigger {}".format(trigger))
        for sensor in self._ready[trigger]:
            sensor.term()

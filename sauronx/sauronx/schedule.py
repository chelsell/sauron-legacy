import datetime
import logging
from time import monotonic
from typing import Iterator, List, Optional, Tuple, Union

from sauronx import stamp

from .arduino import Board
from .configuration import config
from .global_audio import SauronxAudio
from .stimulus import Stimulus, StimulusType


class ScheduledStimulus:
    """
    This is basically a subclass of Stimulus that contains a pin and scheduled seconds.
    Because Python's not good with constructor overriding with overloading,
    it encapsulates a Stimulus object and delegates methods.
    """

    def __init__(
        self, scheduled_seconds: float, stimulus: Union[str, Stimulus], pin: Optional[int]
    ) -> None:
        self.scheduled_seconds = scheduled_seconds
        self.stimulus = stimulus
        self.pin = pin
        if isinstance(stimulus, Stimulus):
            self.audio_obj = stimulus.audio_obj
            self.name = stimulus.name
            self.intensity = stimulus.intensity
            self.byte_intensity = stimulus.byte_intensity
            self.stim_type = stimulus.stim_type
            self.valar_id = stimulus.valar_stimulus.id

    def is_assay_start(self) -> bool:
        return isinstance(self.stimulus, str)

    def is_audio(self) -> bool:
        if isinstance(self.stimulus, str):
            return False
        return self.stimulus.stim_type == StimulusType.AUDIO

    def is_analog(self) -> bool:
        if isinstance(self.stimulus, str):
            return False
        return self.stimulus.stim_type == StimulusType.ANALOG

    def is_digital(self) -> bool:
        if isinstance(self.stimulus, str):
            return False
        return self.stimulus.stim_type == StimulusType.DIGITAL

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        if isinstance(self.stimulus, str):
            return "assay:{}".format(self.stimulus)
        return "{}[id={},pin={}] = {}  @ {}ms".format(
            self.name, self.valar_id, self.pin, self.intensity, 1000 * self.scheduled_seconds
        )


class StimulusTimeRecord:
    def __init__(self, stimulus: ScheduledStimulus, real_timestamp: datetime.datetime) -> None:
        self.stimulus = stimulus
        self.real_timestamp = real_timestamp

    def delta_timestamp(self) -> datetime.datetime:
        return StimulusTimeRecord.calc_delta(self.real_timestamp)

    @staticmethod
    def calc_delta(real_timestamp: datetime.datetime) -> datetime.datetime:
        return real_timestamp + datetime.timedelta(microseconds=0)


class StimulusTimeLog:
    def __init__(self, records: Optional[List[StimulusTimeRecord]] = None) -> None:
        self.records = [] if records is None else records
        self.start_time = None  # type: datetime
        self.end_time = None  # type: datetime

    def start(self) -> None:
        self.start_time = datetime.datetime.now()

    def finish(self) -> None:
        self.end_time = datetime.datetime.now()

    def __iter__(self) -> Iterator[StimulusTimeRecord]:
        return iter(self.records)

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(
        self, index: Union[int, slice]
    ) -> Union[StimulusTimeRecord, List[StimulusTimeRecord]]:
        if isinstance(index, slice):
            return [self.records[i] for i in range(index.start, index.stop, index.step)]
        else:
            return self.records[index]

    def append(self, record: StimulusTimeRecord) -> None:
        self.records.append(record)

    def write(self, log_file: str) -> None:
        logging.debug("Writing stimulus times.")
        with open(log_file, "w") as file:
            file.write("datetime,id,intensity\n")
            start_stamp = stamp(StimulusTimeRecord.calc_delta(self.start_time))
            file.write("{},0,0\n".format(start_stamp))
            for record in self:
                current_stamp = stamp(record.delta_timestamp())
                if not record.stimulus.is_assay_start():
                    file.write(
                        "{},{},{}\n".format(
                            current_stamp, record.stimulus.valar_id, record.stimulus.byte_intensity
                        )
                    )
            end_stamp = stamp(StimulusTimeRecord.calc_delta(self.end_time))
            file.write("{},0,0".format(end_stamp))
        logging.debug("Finished writing stimulus times.")


class Schedule:
    """
    This class is itself a queue: It will drop elements out of Schedule.queue as they are taken.
    """

    def __init__(self, stimulus_list: List[Tuple[int, Stimulus]], n_ms_total: int) -> None:
        """Stimulus_list is in MILLISECONDS."""
        self.stimulus_list = stimulus_list
        self.queue = []
        self.time_range = range(0, len(self.stimulus_list))
        self.n_ms_total = n_ms_total
        # sorting on tuples apparently sorts by the first index first
        for index_ms, stimulus in stimulus_list:
            seconds = index_ms / 1000
            if isinstance(stimulus, str):  # assay name
                self.queue.append(ScheduledStimulus(seconds, stimulus, None))
            elif stimulus.is_digital():
                pin = config.stimuli["digital_pins"][stimulus.name]
                self.queue.append(ScheduledStimulus(seconds, stimulus, pin))
            elif stimulus.is_analog():
                pin = config.stimuli["analog_pins"][stimulus.name]
                self.queue.append(ScheduledStimulus(seconds, stimulus, pin))
            elif stimulus.is_audio():
                self.queue.append(ScheduledStimulus(seconds, stimulus, None))
            else:
                raise ValueError("No stimulus type {}".format(stimulus.name))

    def get_nowait(self) -> ScheduledStimulus:
        return self.queue.pop(0)

    def run_scheduled_and_wait(self, board: Board, audio: SauronxAudio) -> StimulusTimeLog:
        """Runs the stimulus schedule immediately.
        This runs the scheduled stimuli and blocks. Does not sleep.
        """

        logging.info("Battery will run for {}ms. Starting!".format(self.n_ms_total))
        stimulus_time_log = StimulusTimeLog()
        stimulus_time_log.start()  # This is totally fine: It happens at time 0 in the stimulus_list AND the full battery.

        t0 = monotonic()
        assay = "xxxxxxxxxxxxx"
        for _ in self.time_range:
            stimulus = self.get_nowait()
            while monotonic() - t0 < stimulus.scheduled_seconds:
                # if i % 20000 == 0: print(monotonic() - t0, stimulus.scheduled_seconds)
                pass

            # Use self._board.digital_write and analog_write because we don't want to perform checks (for performance)
            if stimulus.is_assay_start():
                if stimulus.stimulus != assay:
                    logging.info("Assay: {}".format(stimulus.stimulus))
                    assay = stimulus.stimulus
                    continue
            elif stimulus.is_digital():
                board._board.digital_write(stimulus.pin, stimulus.intensity)
                logging.debug("{} -> {}".format(stimulus.pin, stimulus.intensity))
            elif stimulus.is_analog():
                board._board.analog_write(stimulus.pin, stimulus.intensity)
                logging.debug("{} -> {}".format(stimulus.pin, stimulus.intensity))
            elif stimulus.is_audio():
                try:
                    audio.play(stimulus.audio_obj)  # volume is handled internally
                except Exception as e:
                    logging.exception(
                        "Failed to play audio stimulus {} at {}".format(stimulus, monotonic() - t0)
                    )
            else:
                raise ValueError("Invalid stimulus type %s!" % stimulus.stim_type)

            stimulus_time_log.append(StimulusTimeRecord(stimulus, datetime.datetime.now()))

        # This is critical. Otherwise, the StimulusTimeLog will finish() at the time the last stimulus is applied,
        # not the time the battery ends
        # TODO simplify StimulusTimeLog so that we don't need this wait: It's just start + length
        elapsed_time = (datetime.datetime.now() - stimulus_time_log.start_time).total_seconds()
        logging.debug(
            "Battery finished except for {}ms wait.".format(self.n_ms_total - (elapsed_time * 1000))
        )
        while (
            datetime.datetime.now() - stimulus_time_log.start_time
        ).total_seconds() * 1000 < self.n_ms_total:
            pass
        stimulus_time_log.finish()
        logging.info("Battery finished.")
        return stimulus_time_log  # for trimming camera frames


__all__ = ["ScheduledStimulus", "StimulusTimeLog", "StimulusTimeRecord", "Schedule"]

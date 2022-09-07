import datetime
import logging
import threading
import time
from typing import Optional

from sauronx import clock_start
from sauronx.preview import Previewer, WebcamSnapshotFailed

from .alive import SauronxAlive, StatusValue
from .arduino import Board
from .camera import PointGreyCamera
from .configuration import config
from .global_audio import SauronxAudio
from .paths import *
from .protocol import ProtocolBlock
from .schedule import Schedule, StimulusTimeLog
from .sensors import SensorParams, SensorRegistry, SensorTrigger


class RunArguments:
    """Small class, but keep because we can flexibly add more members."""

    def __init__(
        self, dark_acclimation_override: Optional[int], assume_clean: bool = False
    ) -> None:
        self.dark_acclimation_override = dark_acclimation_override
        self.assume_clean = assume_clean


class CompletedRunInfo:
    """Information from a completed SauronX submit run.
    This is useful because the information returned is somewhat arbitrary.
    """

    def __init__(
        self,
        true_dark_acclimation: float,
        stimulus_timing_log: StimulusTimeLog,
        datetime_acclimation_started: datetime.datetime,
        datetime_capture_finished: datetime.datetime,
        preview_path: str,
    ):
        self.datetime_acclimation_started = datetime_acclimation_started
        self.true_dark_acclimation = true_dark_acclimation
        self.stimulus_timing_log = stimulus_timing_log
        self.datetime_capture_finished = datetime_capture_finished
        self.preview_path = preview_path


class Submitter:
    """Top-level handler for video acquisition and running stimuli."""

    def __init__(
        self,
        sx_alive: SauronxAlive,
        battery: ProtocolBlock,
        args: RunArguments,
        audio: SauronxAudio,
        board: Board,
    ) -> None:
        import valarpy.model as model

        self.sx_alive = sx_alive
        self.submission_hash = sx_alive.submission_hash
        self.submission_obj = sx_alive.submission_obj
        self.dark_acclimation_override = args.dark_acclimation_override
        self.audio = audio
        self.board = board
        self.plots = True
        self.assume_clean = args.assume_clean
        self.battery = battery
        self.keep_camera_on_ms = (
            len(self.battery)
            + config.camera["padding_after_milliseconds"]
            + config.camera["padding_before_milliseconds"]
        )
        self.submission = self.sx_alive.submission_obj
        self.sensors_finished = False
        self.plate_type = (
            model.PlateTypes.select(model.PlateTypes, model.TemplatePlates, model.Experiments)
            .join(model.TemplatePlates)
            .join(model.Experiments)
            .where(model.Experiments.id == self.submission.experiment.id)
            .first()
        )
        self.registry = SensorRegistry(
            SensorParams(self.keep_camera_on_ms, config.get_output_dir(self.submission_hash))
        )
        self.darkness_seconds = (
            self.dark_acclimation_override
            if self.dark_acclimation_override is not None
            else self.submission_obj.acclimation_sec
        )

    def submit(self) -> CompletedRunInfo:
        info = None
        try:
            info = self._run_core()
            self._tear_down()  # we need the sensor data to plot
        except (KeyboardInterrupt, SystemExit) as e:
            self._handle_cancel(e)
        except BaseException as e:
            self._handle_error(e)
        return info

    def plot(self, include_audio: bool) -> None:
        logging.info("Plotting sensor data. Add a concern if it looks wrong or unusual.")
        for sensor in self.registry.fetch():
            if sensor.name() == "microphone" and not include_audio:
                continue
            print("")
            # noinspection PyBroadException
            try:
                p = sensor.plot()
                print(p)
                logging.debug(p)
            except Exception as e:
                logging.error(
                    "Couldn't plot data from sensor {}".format(sensor.sensor_name()), exc_info=True
                )
        print("")

    def _run_core(self) -> CompletedRunInfo:

        battery = self.battery
        plate_type_id = self.plate_type.id
        coll = config.get_coll(self.submission_hash)
        output_dir = config.get_output_dir(self.submission_hash)
        frames_output_dir = config.get_raw_frames_dir(self.submission_hash)
        with PointGreyCamera(
            frames_output_dir,
            coll.raw_snapshot_timing_log_file(),
            self.keep_camera_on_ms,
            plate_type_id,
        ) as camera:
            schedule = Schedule(battery.stimulus_list, len(battery))
            if (
                "sauron.hardware.webcam.enabled" in config
                and config["sauron.hardware.webcam.enabled"]
            ):
                self._webcam(coll, plate_type_id)
            preview_path = self._preview(output_dir, plate_type_id)

            try:
                self.registry.ready(SensorTrigger.EXPERIMENT_START)
            except Exception as e:
                logging.fatal("Failed to ready sensors")
                warn_user("Failed to ready sensors")
                raise e
            try:
                self.registry.start(SensorTrigger.EXPERIMENT_START, self.board)
            except Exception as e:
                logging.fatal("Failed to start sensors")
                warn_user("Failed to start sensors")
                raise e

            datetime_acclimation_started = datetime.datetime.now()
            actual_dark_seconds = self._dark_adapt()
            self.sx_alive.update_status(StatusValue.CAPTURING)
            self.board.flash_ready()
            p = threading.Thread(target=camera.start)
            self.registry.ready(SensorTrigger.CAMERA_START)
            p.start()
            self.registry.start(SensorTrigger.CAMERA_START)

            self.board.ir_on()
            self.board.sleep(config.camera["padding_before_milliseconds"] / 1000)

            stimulus_time_log = schedule.run_scheduled_and_wait(self.board, self.audio)
            p.join()

            datetime_capture_finished = datetime.datetime.now()
            logging.debug("Finished capturing at {}".format(datetime_capture_finished))
            stimulus_time_log.write(coll.stimulus_timing_log_file())

            camera.finish()
            self.board.flash_done()
        return CompletedRunInfo(
            actual_dark_seconds,
            stimulus_time_log,
            datetime_acclimation_started,
            datetime_capture_finished,
            preview_path=preview_path,
        )

    def _webcam(self, coll: SubmissionPathCollection, plate_type_id) -> None:
        if (
            self.dark_acclimation_override is None
            or self.dark_acclimation_override >= config.webcam["min_dark_acclimation_ms"]
        ):
            try:
                Previewer(plate_type_id).webcam_preview(self.board, coll.webcam_snapshot())
            except WebcamSnapshotFailed as e:
                warn_user("Failed taking webcam snapshot!", "Please fix this before the next run.")
                logging.error("Failed taking webcam snapshot", e)
        elif pexists(coll.webcam_snapshot()):
            logging.warning(
                "Using the webcam snapshot from the previous run because --dark was set and was too low."
            )
        else:
            logging.warning("Skipping webcam capture because --dark was set and was too low.")

    def _preview(self, output_dir, plate_type_id) -> str:
        logging.debug("Showing a frame.")
        preview_path = Previewer(plate_type_id).snap_and_show()
        notify_user(
            "Check the ROI, especially the corners for any rotation.",
            "You can cancel by typing CTRL-C.",
        )
        self.board.ir_off()
        return preview_path

    def _dark_adapt(self) -> float:
        """
        Waits for the scheduled period.
        :return: The actual number of seconds of dark acclimation
        """
        elapsed_time = time.monotonic() - clock_start
        if elapsed_time < self.darkness_seconds:
            sleep_time = self.darkness_seconds - (time.monotonic() - clock_start)
            msg = "Sleeping for {}s total dark acclimation time, including setup time".format(
                self.darkness_seconds
            )
            logging.debug(msg)
            print(Fore.BLUE + msg)
            time.sleep(sleep_time)
        else:
            logging.warning(
                "Setup lasted {}s, which is greater than the scheduled dark acclimation time of {}s".format(
                    round(elapsed_time, 3), round(self.darkness_seconds, 3)
                )
            )
        return elapsed_time

    def _tear_down(self) -> None:
        # make this idempotent
        if not self.sensors_finished:
            self.registry.terminate(SensorTrigger.EXPERIMENT_START)
            self.registry.terminate(SensorTrigger.CAMERA_START)
            logging.debug("Sleeping for 1s for sensors to terminate")
            time.sleep(1)  # give the sensors a bit
            logging.debug("Finished sleeping.")
            self.sensors_finished = True

    def _handle_cancel(self, e: BaseException) -> None:
        try:
            logging.info("Received exit/cancel")
            self.sx_alive.update_status(StatusValue.CANCELLED_DURING_CAPTURE)
        except BaseException:
            logging.fatal(
                "Error handling SauronX submission cancellation"
            )  # not important; throw the real error
        warn_user(
            "An exit code was received. Quitting SauronX.",
            "Because the cancellation was during capture, any data is not recoverable.",
        )
        self.board.flash_error()
        raise e

    def _handle_error(self, e: BaseException) -> None:
        logging.fatal("SauronX submission failed")
        try:
            self.sx_alive.update_status(StatusValue.FAILED_DURING_CAPTURE)
        except BaseException:
            logging.fatal(
                "Error handling SauronX submission failure"
            )  # not important; throw the real error
        warn_user(
            "Error: SauronX did not finish capturing.",
            "Because this occurred while capturing, any data is not recoverable.",
            "A stack trace should be shown below.",
        )
        self.board.flash_error()
        raise e

import datetime
import shutil
from abc import ABC

import pandas as pd
from .utils import notify_user, success_to_user, looks_like_submission_hash, plain_timestamp_started,\
    plain_timestamp_started_with_millis, pretty_timestamp_started
from valarpy import Valar

from .alive import SauronxAlive, StatusValue
from .global_audio import SauronxAudio
from .locks import SauronxLock
from .preview import *
from .prototype import Prototyper
from .results import Results
from .runner import *
from .sensors import SensorParams, SensorRegistry, SensorTrigger


class RunMode:
    def run(self, **args) -> None:
        raise NotImplementedError()


class _SubmissionMode(RunMode, ABC):
    """A run mode with a submission hash."""

    def _log_start(self, local: bool, submission_hash: str) -> None:
        notify_user("Starting at {}".format(pretty_timestamp_started))
        logging.info("Submission start time: ".format(plain_timestamp_started_with_millis))

    def _log_finish(self, local: bool, submission_hash: str, halt_after_acquisition: bool) -> None:
        if halt_after_acquisition:
            success_to_user("Exiting. Handing off processing of results.")
        elif local:
            success_to_user(
                "All done! The data will be stored locally.",
                "You can upload the data later with 'sauronx continue'",
            )
        else:
            success_to_user(
                "All done! The data will be in Valar shortly.",
                "You should then visit:",
                "https://valinor.ucsf.edu/submissions/{}".format(submission_hash),
                "to add notes as you start analyzing the data.",
            )


class SubmitMode(_SubmissionMode):
    def run(
        self,
        hashes: List[str],
        dark: Optional[int],
        local: bool,
        overwrite: bool,
        keep_frames: bool,
        store_to: Optional[str],
        assume_clean: bool,
        sensor_plot: bool,
        plot_audio: bool,
        halt_after_acquisition: bool,
        ignore_prior: bool,
        keep_lock: bool,
    ) -> None:
        args = SubmissionRunnerArgs(
            dark=dark,
            local=local,
            overwrite=overwrite,
            keep_frames=keep_frames,
            store_to=store_to,
            assume_clean=assume_clean,
            sensor_plot=sensor_plot,
            plot_audio=plot_audio,
            halt_after_acquisition=halt_after_acquisition,
            ignore_prior=ignore_prior,
        )
        SauronxLock().lock(None)
        try:
            b = Board()
            b.init()
            audio = SauronxAudio()
            audio.start()
            with Valar() as db:
                ss = SubmissionRunner(args, db, audio, b)
                for i, h in enumerate(hashes):
                    # TODO datetime_started only applies to the first hash. Is this really what we want?
                    self._log_start(args.local, h)
                    # we don't need a new process for the last run
                    ss.run(h, i == len(hashes) - 1)
                    self._log_finish(args.local, h, halt_after_acquisition)
        finally:
            if not keep_lock:
                SauronxLock().unlock(ignore_warning=True)


class IncubateMode(RunMode):
    def run(self, duration_seconds: int, with_sensors: bool = False) -> None:
        with SauronxAlive(None) as alive:
            SauronxLock().lock(None)
            b = None
            audio = None
            registry = None
            try:
                notify_user(
                    "Incubating for {}s".format(duration_seconds),
                    "Started at {} and will finish at {}".format(
                        datetime.datetime.now().strftime("%H:%M"),
                        (
                            datetime.datetime.now() + datetime.timedelta(seconds=duration_seconds)
                        ).strftime("%H:%M"),
                    ),
                    "If you didn’t start this, please don’t remove the plate.",
                )
                alive.update_status(StatusValue.STARTED_INCUBATION)
                if with_sensors:
                    audio = SauronxAudio()
                    audio.start()
                    b = Board()
                    b.init()
                    # TODO hacky: -1 s so it doesn't turn off before the sensor data writes
                    registry = SensorRegistry(
                        SensorParams(duration_seconds - 1, config.get_incubation_dir())
                    )
                    registry.ready(SensorTrigger.EXPERIMENT_START)
                    registry.start(SensorTrigger.EXPERIMENT_START, b)
                time.sleep(duration_seconds)
            except:
                alive.update_status(StatusValue.FAILED_INCUBATION)
                raise
            finally:
                SauronxLock().unlock(ignore_warning=True)
                if registry is not None:
                    pass
                if b is not None:
                    b.finish()
                if audio is not None:
                    audio.stop()
            if with_sensors:
                registry.terminate(SensorTrigger.EXPERIMENT_START)
                for sensor in registry.fetch():
                    print("")
                    print(sensor.plot(include_audio=True))
        success_to_user("Finished incubating: You should remove the plate now.")
        alive.update_status(StatusValue.FINISHED_INCUBATION)


class TestMode(RunMode):
    def run(
        self, keep: bool, upload: bool, assume_clean: bool, sensor_plot: bool, plot_audio: bool
    ) -> None:
        submission_hash = str(config["sauron.test_submission_hash"])
        output_dir = config.get_output_dir(submission_hash)
        args = SubmissionRunnerArgs(
            dark=None,
            local=not upload,
            overwrite=True,
            keep_frames=False,
            store_to=None,
            assume_clean=assume_clean,
            sensor_plot=sensor_plot,
            plot_audio=plot_audio,
            halt_after_acquisition=False,
            ignore_prior=True,
        )
        with Valar() as db:
            SauronxLock().lock(None)
            try:
                # these will get shut down afterward
                audio = SauronxAudio()
                audio.start()
                b = Board()
                b.init()
                ss = SubmissionRunner(args, db, audio, b)
                ss.run(submission_hash, True)
                if not keep:
                    shutil.rmtree(output_dir, ignore_errors=True)
            finally:
                SauronxLock().unlock(ignore_warning=True)


class ProceedMode(_SubmissionMode):
    def run(self, path: str, local: bool, ignore_warnings: bool) -> None:
        if looks_like_submission_hash(path):
            coll = config.get_coll(path)
        coll = config.get_coll(path)
        submission_hash = os.path.basename(path)
        # don't lock
        self._log_start(local, submission_hash)
        with SauronxAlive(submission_hash, ignore_warnings=ignore_warnings) as sx_alive:
            results = Results(sx_alive)
            if not coll.snapshot_timing_exists():
                raise ValueError(
                    "Can't proceed; capture didn't complete: Missing {}".format(
                        coll.snapshot_timing_log_file()
                    )
                )
            if not coll.avi_exists():
                results.make_video()
            if not local:
                results.upload()
        self._log_finish(local, submission_hash, False)


class PrototypeMode(RunMode):
    def run(self, plate_type: int) -> None:
        with SauronxAlive(None):
            SauronxLock().lock(None)
            prototyper = Prototyper(plate_type)
            try:
                prototyper.init()
                prototyper.cmdloop()
            finally:
                prototyper.finish()
                SauronxLock().unlock()


class LivePreviewMode:
    def run(self, plate_type: int) -> None:
        with SauronxAlive(None):
            b = None
            SauronxLock().lock(None)
            try:
                b = Board()
                b.init()
                Previewer(plate_type).live_preview()
            finally:
                if b is not None:
                    b.finish()
                SauronxLock().unlock()


class SnapshotMode:
    def run(self, plate_type: int) -> None:
        with SauronxAlive(None):
            b = None
            SauronxLock().lock(None)
            try:
                b = Board()
                b.init()
                Previewer(plate_type).preview(b)
            finally:
                if b is not None:
                    b.finish()
                SauronxLock().unlock()


class CalibrateMode:
    def run(self, sensor: str, sampling_seconds: float) -> None:
        sensor = sensor.lower()
        if sensor == "microphone":
            raise ValueError("Microphone is not yet supported for calibration")
        with SauronxAlive(None):
            b = None
            registry = None
            SauronxLock().lock(None)
            directory = pjoin(config.output_dir_root, "calibration", sensor)
            make_dirs(directory)
            path = pjoin(directory, plain_timestamp_started + ".csv")
            notify_user("Saving to {}".format(path))
            try:
                b = Board()
                b.init()
                registry = SensorRegistry(SensorParams(3600, directory))
                registry.ready(SensorTrigger.LIGHT_TEST)
                values = []
                tmp_file = pjoin(directory, "sensors", "photometer_log.csv")
                while True:
                    value = input("Enter real value or 'exit':  ")
                    if value.strip().lower() == "exit":
                        break
                    registry.start(SensorTrigger.LIGHT_TEST, board=b)
                    b.sleep(sampling_seconds)
                    registry.terminate(SensorTrigger.LIGHT_TEST)
                    measured = pd.read_csv(tmp_file).Value.mean()
                    std = pd.read_csv(tmp_file).Value.std()
                    now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    print("Measured {} for value {}".format(measured, value))
                    values.append(
                        pd.Series({"real": value, "measured": measured, "std": std, "time": now})
                    )
                    pd.DataFrame(values).to_csv(path)
                notify_user("Done. Saved to {}".format(path))
            finally:
                if b is not None:
                    b.finish()
                if registry is not None:
                    pass
                SauronxLock().unlock()


class WebcamSnapshotMode:
    def run(self) -> None:
        with SauronxAlive(None):
            b = None
            SauronxLock().lock(None)
            try:
                b = Board()
                b.init()
                Previewer(1).webcam_preview(b)
                b.finish()
            finally:
                if b is not None:
                    b.finish()
                SauronxLock().unlock()


__all__ = [
    "SubmitMode",
    "TestMode",
    "ProceedMode",
    "IncubateMode",
    "PrototypeMode",
    "LivePreviewMode",
    "SnapshotMode",
    "WebcamSnapshotMode",
    "CalibrateMode",
]

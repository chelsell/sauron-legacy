from datetime import datetime, timedelta
from multiprocessing import Process

from valarpy.Valar import Valar

from .alive import SauronxAlive, StatusValue
from .global_audio import SauronxAudio
from .locks import SauronxLock
from .preview import *
from .protocol import ProtocolBlock
from .results import Results
from .submission import CompletedRunInfo, RunArguments, Submitter


class SubmissionRunnerArgs:
    def __init__(
        self,
        local: bool,
        dark: Optional[float],
        overwrite: bool,
        keep_frames: bool,
        store_to: Optional[str],
        assume_clean: bool,
        sensor_plot: bool,
        plot_audio: bool,
        halt_after_acquisition: bool,
        ignore_prior: bool,
    ):
        self.local = local
        self.dark = dark
        self.overwrite = overwrite
        self.keep_frames = keep_frames
        self.store_to = store_to
        self.assume_clean = assume_clean
        self.sensor_plot = sensor_plot
        self.plot_audio = plot_audio
        self.halt_after_acquisition = halt_after_acquisition
        self.ignore_prior = ignore_prior


class SubmissionRunner:
    def __init__(
        self, args: SubmissionRunnerArgs, db: Valar, audio: SauronxAudio, b: Board
    ) -> None:
        self._args = args
        self._db = db
        self._audio = audio
        self._board = b

    def run(self, submission_hash: str, last_run: bool):
        output_dir = config.get_output_dir(submission_hash)
        raw_frames_output_dir = config.get_raw_frames_dir(submission_hash)
        self._ensure_sufficient_storage(submission_hash)
        logging.debug("Will {}start new process".format("" if not last_run else "not "))
        logging.debug(
            "Will {}shut board and audio down after capture finishes".format(
                "" if last_run else "not "
            )
        )
        # okay, there's a brief moment where SauronX is unlocked if this fn is run in a loop
        # the DB connection is only opened once (outside the loop), so this should be milliseconds only
        with SauronxAlive(
            submission_hash, acquisition_start=True, ignore_warnings=self._args.ignore_prior
        ) as alive:
            battery = (
                config["sauron.test_battery"]
                if alive.is_test
                else alive.submission_obj.experiment.battery_id
            )
            battery = ProtocolBlock(battery)
            run_args = RunArguments(self._args.dark, assume_clean=self._args.assume_clean)
            self._prompt(alive, battery, run_args)
            # Give the option to overwrite only after we've checked for prior successful submissions:
            self._handle_already_exists(
                output_dir, raw_frames_output_dir
            )  # in case we're choosing to overwrite
            # switch over to new submission quietly, and don't let the lock up even for a microsecond
            SauronxLock().engage(submission_hash, replace=True)
            with Results(
                alive, keep_raw_frames=self._args.keep_frames, assume_clean=self._args.assume_clean
            ) as results:
                results.initialize_dir()
                self._run_single(alive, battery, run_args, results, last_run)

    def _prompt(self, alive: SauronxAlive, battery: ProtocolBlock, run_args: RunArguments):
        darkness_seconds = (
            run_args.dark_acclimation_override
            if run_args.dark_acclimation_override is not None
            else alive.submission_obj.acclimation_sec
        )
        notify_user(
            "Submitting {} ({}).".format(alive.submission_hash, alive.submission_obj.description),
            'for experiment "{}".'.format(alive.submission_obj.experiment.name),
            'Using battery "{}" (ID {}),'.format(battery.valar_obj.name, battery.valar_obj.id),
            "which will run for {} with {} events.".format(
                nice_time(len(battery)), len(battery.stimulus_list)
            ),
            "",
            "~~Running camera at {} FPS.~~".format(config.fps),
            "Started at {} and will finish at {}.".format(
                datetime.now().strftime("%H:%M"),
                (
                    datetime.now() + timedelta(milliseconds=len(battery) + darkness_seconds * 1000)
                ).strftime("%H:%M"),
            ),
        )
        if not prompt_yes_no("Continue? [yes/no]"):
            raise RefusingRequestException("User chose not to continue.")

    def _ensure_sufficient_storage(self, submission_hash: str) -> None:
        import valarpy.model as model

        battery = (
            model.Submissions.select()
            .where(model.Submissions.lookup_hash == submission_hash)
            .first()
            .experiment.battery
        )
        n_frames = battery.length / 1000 * config.camera["frames_per_second"]
        expected = 1024 * config.storage["max_kb_per_frame"] * n_frames
        free = psutil.disk_usage(config.raw_frames_root).free
        if expected > free:
            if self._args.assume_clean:
                msg = (
                    "There are {} of storage free on {}, but {} are expected to be needed.\n"
                    "Continuing anyway because --assume-clean is set."
                ).format(filesize.size(free), config.raw_frames_disk, filesize.size(expected))
                logging.warning(msg)
            else:
                msg = "Refusing to proceed: there are {} of storage free on {}, but {} are expected to be needed".format(
                    filesize.size(free), config.raw_frames_disk, filesize.size(expected)
                )
                warn_user(
                    msg,
                    "Consider running `sauronx clean` to see what you can delete.",
                    "The raw frames are stored under {}.".format(config.raw_frames_root),
                )
                raise RefusingRequestException(msg)
        logging.info(
            "There are {} of storage free on disk {} with {} expected to be needed".format(
                filesize.size(free), config.raw_frames_disk, filesize.size(expected)
            )
        )

    def _run_single(
        self,
        alive: SauronxAlive,
        battery: ProtocolBlock,
        run_args: RunArguments,
        results: Results,
        last_run: bool,
    ):
        b = self._board
        audio = self._audio
        # turning the IR off while it's not using will reduce heating
        try:
            b.ir_on()
            submitter = Submitter(alive, battery, run_args, audio, b)
            run_info = submitter.submit()  # type: CompletedRunInfo
            # Save the timing info ASAP; we can't in proceed().
            # It would be nice to shut everything down earlier, but preserve the data at all costs.
            results.finalize(run_info)
            alive.update_status(StatusValue.COMPRESSING)
            if self._args.sensor_plot:
                submitter.plot(include_audio=self._args.plot_audio)
            b.ir_off()
        except:
            # don't do this after unlocking because shutting down the board and audio
            # could interfere with another process that gets run after the unlock!!!
            b.finish()
            audio.stop()
            raise
        # we need to handle these cases separately
        if last_run:
            # don't do this after unlocking because shutting down the board and audio
            # could interfere with another process that gets run after the unlock!!!
            b.finish()
            audio.stop()
            SauronxLock().unlock()
            if not self._args.halt_after_acquisition:
                self._handle_results(results, alive)
        elif not self._args.halt_after_acquisition:
            p = Process(target=self._handle_results, args=(results,))
            p.start()

    def _handle_already_exists(self, output_dir: str, raw_frames_output_dir: str):
        if self._args.overwrite and (
            os.path.exists(output_dir) or os.path.exists(raw_frames_output_dir)
        ):
            logging.info("Deleting previous run at {}".format(output_dir))
            if os.path.exists(output_dir):
                slow_delete(output_dir, 3)
            if os.path.exists(raw_frames_output_dir) and not self._args.assume_clean:
                slow_delete(raw_frames_output_dir, 3)

    def _handle_results(self, results: Results, alive: SauronxAlive) -> None:
        if self._args.store_to is None:
            results.make_video()
            if not self._args.local:
                results.upload()
        else:
            results.copy_raw_to(self._args.store_to)


__all__ = ["SubmissionRunner", "SubmissionRunnerArgs"]

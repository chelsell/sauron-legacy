import csv
import hashlib
import logging
import shutil
from datetime import datetime, timedelta
from ntpath import basename
from typing import Dict

from colorama import Fore
from dateutil import parser

from sauronx import append_log_to_submission_log, stamp

from .alive import SauronxAlive, StatusValue
from .configuration import config
from .submission import CompletedRunInfo


def make_dirs_perm(pathname):
    make_dirs(pathname)
    os.chmod(pathname, 0o777)


class Results:
    """
    Keeps track of frames and metadata in a SauronX submission.
    Also uploads the data and notifies if requested.
    The recommended usage is:
            with Results() as results:
                    # let the camera write
                    results.upload()
    """

    def __init__(
        self, sx_alive: SauronxAlive, keep_raw_frames: bool = False, assume_clean: bool = False
    ) -> None:
        self.coll = config.get_coll(sx_alive.submission_hash)
        self.sx_alive = sx_alive
        self.submission_hash = self.sx_alive.submission_hash
        self.upload_params = config["connection.upload"]
        self.notify_params = config["connection.notification"]
        self.output_dir = self.coll.output_dir()
        self.raw_frames_output_dir = self.coll.outer_frames_dir()
        self.fps = config["sauron.hardware.camera.frames_per_second"]
        plate_type_id = sx_alive.submission_obj.experiment.template_plate.plate_type.id
        roi = config.camera_roi(plate_type_id)
        self.frame_width = roi.x1 - roi.x0
        self.frame_height = roi.y1 - roi.y0
        # this gets uploaded to a 'pending' dir on valinor for notification
        self.video_file = self.coll.avi_file()
        self.qp = config["sauron.data.video.qp"]
        self.x265_params = None
        self.keyframe_interval = config["sauron.data.video.keyframe_interval"]
        self.extra_x265_options = config["sauron.data.video.extra_x265_params"]
        self.submission_log_file = append_log_to_submission_log(self.submission_hash)
        self.file_hasher = FileHasher(algorithm=hashlib.sha256, extension=".sha256")
        self.keep_raw_frames = keep_raw_frames
        self.assume_clean = assume_clean

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    def initialize_dir(self) -> None:
        def change_perm(action, name, exc):
            os.chmod(name, 0o777)

        tmp_webcam_snap = ".{}.snap.tmp.jpg".format(self.submission_hash)
        if os.path.exists(self.output_dir):
            warn_user(
                "Refusing to initialize output directory:",
                self.output_dir,
                "The path already exists.",
            )
            print(Fore.RED + "Overwrite? [yes/no]", end="")
            if prompt_yes_no(""):
                # a little weird, but copy webcam file first
                # this is useful if --dark and --override are both set
                if pexists(self.coll.webcam_snapshot()):
                    shutil.copy(self.coll.webcam_snapshot(), tmp_webcam_snap)
                print("")
                shutil.rmtree(self.output_dir, onerror=change_perm)
                if os.path.exists(self.raw_frames_output_dir):
                    logging.info("Deleting raw frames at {}".format(self.raw_frames_output_dir))
                    if self.assume_clean:
                        logging.warning(
                            "Since --assume-clean is set, will not delete previous frames."
                        )
                    else:
                        shutil.rmtree(self.raw_frames_output_dir, onerror=change_perm)
            else:
                raise RefusingRequestException(
                    "The path {} already exists; refusing to proceed.".format(self.output_dir)
                )
            logging.info("Finished deleting")

        make_dirs_perm(self.output_dir)
        make_dirs_perm(self.raw_frames_output_dir)
        make_dirs_perm(pjoin(self.output_dir, "timing"))
        make_dirs_perm(pjoin(self.output_dir, "sensors"))
        if pexists(tmp_webcam_snap) and os.path.getsize(tmp_webcam_snap) > 0:
            logging.warning(
                "Keeping webcam snapshot from previous run. It will be overwritten if a new capture is taken."
            )
            shutil.move(tmp_webcam_snap, self.coll.webcam_snapshot())

        with open(pjoin(self.output_dir, "submission_hash.txt"), "w", encoding="utf8") as f:
            f.write(self.sx_alive.submission_hash)
        shutil.copyfile(os.environ["SAURONX_CONFIG_PATH"], self.coll.toml_file())

        # copy os info, git hash, etc.
        with open(self.coll.env_file(), "w", encoding="utf8") as f:
            for key, value in config.environment_info.items():
                f.write(key + "=" + value + "\n")

        logging.info("Prepared output directory {}".format(self.output_dir))

        if pexists(self.coll.log_file()):
            logging.warning("The log file at {} already exists".format(self.coll.log_file()))
        else:
            os.symlink(self.submission_log_file, self.coll.log_file())

    def finalize(self, run_info: CompletedRunInfo) -> None:
        import valarpy.model as model

        with open(self.coll.env_file(), "a", encoding="utf8") as f:

            def write(key: str, value: str) -> None:  # TODO strip control chars, etc, too
                f.write(key + "=" + escape_for_properties(value) + "\n")

            sub_obj = self.sx_alive.submission_obj
            exp = sub_obj.experiment
            # this is the critical start time, which is used to fill in runs.datetime_run
            write("datetime_started", stamp(run_info.datetime_acclimation_started))
            # and this end time is critical too
            write("datetime_capture_finished", stamp(run_info.datetime_capture_finished))
            write("original:experiment_id", exp.id)
            write("original:experiment_name", exp.name)
            write("original:description", sub_obj.description)
            write("original:continuing_id", sub_obj.continuing_id)
            write("original:datetime_plated", sub_obj.datetime_plated)
            write("original:datetime_dosed", sub_obj.datetime_dosed)
            write("original:notes", sub_obj.notes)
            write("original:person_submitted", sub_obj.user_id)
            write("original:battery", exp.battery_id)
            write("original:template_plate", exp.template_plate_id)
            for param in model.SubmissionParams.select(model.SubmissionParams).where(
                model.SubmissionParams.submission == sub_obj.id
            ):
                write("param:" + param.param_type + ":" + param.name, param.value)
            write("datetime_environment_written", stamp(datetime.now()))
            write("ffmpeg_version", self.find_ffmpeg_version())
        try:
            if os.path.exists(run_info.preview_path):
                shutil.copyfile(run_info.preview_path, self.coll.preview_snapshot())
            else:
                logging.error("Missing preview snapshot {}".format(run_info.preview_path))
        except:
            logging.exception("Failed to copy preview frame at {}".format(run_info.preview_path))
        success_to_user("Finalized run. All of the necessary data is now present.")

    def find_ffmpeg_version(self):
        out, err = wrap_cmd_call(["ffmpeg", "-version"])
        return out

    def upload(self) -> None:
        try:
            self.sx_alive.update_status(StatusValue.UPLOADING)
            # noinspection PyTypeChecker
            for i in range(0, int(self.upload_params["max_attempts"])):
                try:
                    self._attempt_upload()
                    break
                except (SCPException, ExternalCommandFailed) as e:
                    # noinspection PyTypeChecker
                    if i < int(self.upload_params["max_attempts"]) - 1:
                        logging.error("Upload failed (attempt {})".format(i), e)
                        warn_user("Upload failed (attempt {})".format(i))
                    else:
                        raise e
            self.sx_alive.update_status(StatusValue.UPLOADED)
        except Exception:
            self.sx_alive.update_status(StatusValue.FAILED_DURING_UPLOAD)
            raise

    def copy_raw_to(self, path: str) -> None:
        msg = "Moving raw frames to {}".format(path)
        logging.warning(msg)
        warn_user(msg, "==DO NOT INTERRUPT OR CANCEL==")
        try:
            shutil.move(self.raw_frames_output_dir, path)
        except:
            logging.fatal(
                "Moving raw frames stopped partway. They are split between {} and {}".format(
                    self.raw_frames_output_dir, path
                )
            )
            raise
        warn_user(
            "Moved raw frames to {}.".format(path, self.submission_hash),
            "You will need to copy them back and",
            "finish the submission with `sauronx continue {}`.",
        )

    def make_video(self) -> None:
        try:
            self._parse_frame_timing_file()
            self._trim_frames()
            logging.info(
                "Making primary video with ffmpeg. At high framerates, this should take about as long as the duration of the run"
            )
            self._run_ffmpeg(self.raw_frames_output_dir, self.video_file)
            logging.info("Compressing microphone recording.")
            self._convert_microphone()
        except Exception:
            self.sx_alive.update_status(StatusValue.FAILED_DURING_POSTPROCESSING)
            raise

    def _run_ffmpeg(self, path, output_video):
        make_dirs_perm(os.path.dirname(output_video))
        if not pdir(path):
            raise ValueError("Directory {} does not exist".format(path))
        first_real_frame = self._first_frame(path)
        # TODO change log level back to info
        stream_cmd_call(
            [
                "ffmpeg",
                "-loglevel",
                "warning",
                "-hwaccel",
                "qsv",
                "-f",
                "image2",
                "-nostdin",
                "-c:v",
                "rawvideo",
                "-framerate",
                str(self.fps),
                "-video_size",
                "{}x{}".format(self.frame_width, self.frame_height),
                "-pixel_format",
                "gray",
                "-start_number",
                str(first_real_frame),
                "-i",
                pjoin(path, "%08d.raw"),
                "-y",
                "-c:v",
                "hevc_qsv",
                "-g",
                str(self.keyframe_interval),
                "-q:v",
                str(self.qp),
                "-preset",
                config["sauron.data.video.preset"],
                "-load_plugin",
                "2",
                "-r",
                str(self.fps),
                output_video,
            ]
        )

        self.file_hasher.add_hash(output_video)
        if not self.keep_raw_frames:
            slow_delete(path, 3)

    def _first_frame(self, path: str):
        assert pexists(path), "The frame directory does not exist"
        prop_files = list(sorted(scan_for_proper_files(path)))
        if len(prop_files) == 0:
            warn_user("No frames were found in {}".format(path))
            raise ValueError("No frames were found in {}".format(path))
        return basename(prop_files[0].rstrip(".raw"))

    def _x265_params(self):
        if self.x265_params is not None:
            return self.x265_params
        self.x265_params = "qp={}:keyint={}:min-keyint={}".format(
            str(self.qp), self.keyframe_interval, self.keyframe_interval
        )
        if self.extra_x265_options is not None and len(self.extra_x265_options) > 0:
            self.x265_params += ":" + ":".join(
                [
                    str(k) + "=" + config.parse_path_format(v, self.output_dir)
                    for k, v in self.extra_x265_options.items()
                ]
            )
        logging.info(
            "Encoding with framerate {} and x265 params '{}'".format(self.fps, self.x265_params)
        )
        return self.x265_params

    def _convert_microphone(self) -> None:
        microphone_input = self.coll.microphone_wav_path()
        microphone_output = self.coll.microphone_flac_path()
        if pexists(microphone_input):
            logging.info("Compressing microphone data.")
            stream_cmd_call(
                [
                    "ffmpeg",
                    "-i",
                    microphone_input,
                    "-compression_level",
                    config["sauron.data.audio.flac_compression_level"],
                    "-c:a",
                    "flac",
                    microphone_output,
                ]
            )
            self.file_hasher.add_hash(microphone_output)
            os.remove(microphone_input)

    def _trim_frames(self) -> None:
        """Trims the frames that were captured before the first stimulus or after the last.
        This works because StimulusTimeLog is defined to have its head be the start of the run and its tail be the end of the run, regardless of the stimuli.
        To fulfill this definition, Board.run_scheduled_and_wait appends a stimulus for ID 0 at the beginning, and another at the end.
        """
        if not self.coll.stimulus_timing_exists():
            raise MissingResourceException(
                "Cannot proceed: the stimulus timing log at {} is missing".format(
                    self.coll.stimulus_timing_log_file()
                )
            )

        # first, check that we didn't fail partway through trimming
        # this could be bad; let's fix that before making the trimming videos or the main video
        def fixit(name: str):
            output_video = pjoin(self.coll.trimmed_dir(), name + ".mkv")
            hash_file = output_video + ".sha256"
            tmpdir = pjoin(self.output_dir, name + "-trimmings")
            if pexists(tmpdir) and not pexists(hash_file):
                warn_user("Moving {} trimmed frames back".format(name))
                logging.warning("Moving {} trimmed frames back".format(name))
                for f in os.listdir(tmpdir):
                    if os.path.isdir(
                        self.coll.outer_frames_dir()
                    ):  # If directory exists, copy overwrites existing files in directory, move does not.
                        shutil.copy(pjoin(tmpdir, f), self.coll.outer_frames_dir())
                        os.remove(pjoin(tmpdir, f))
                    else:
                        shutil.move(pjoin(tmpdir, f), self.coll.outer_frames_dir())
            elif pexists(tmpdir):
                pass

        fixit("start")
        fixit("end")

        stimulus_time_log = self._parse_stimulus_timing_file(self.coll.stimulus_timing_log_file())
        if len(stimulus_time_log) == 0:
            return  # ok; nothing to remove
        snapshots = [
            parse_local_iso_datetime(snap) for snap in lines(self.coll.snapshot_timing_log_file())
        ]
        first_stimulus = stimulus_time_log[0]  # type: datetime
        last_stimulus = stimulus_time_log[-1]  # type: datetime
        trimmings_start = []
        trimmings_end = []
        ran_off_end = 0
        my_files = enumerate(sorted(scan_for_proper_files(self.coll.outer_frames_dir())))
        for i, frame in my_files:
            if i >= len(snapshots):
                ran_off_end += 1
            elif snapshots[i] < first_stimulus:
                trimmings_start.append(frame)
            elif snapshots[i] > last_stimulus:
                trimmings_end.append(frame)
        if ran_off_end > 0:
            logging.error("{} stimuli occurred after the last snapshot!")
            warn_user("{} stimuli occurred after the last snapshot!")

        make_dirs_perm(self.coll.trimmed_dir())
        self._make_trimmings_video(trimmings_start, "start")
        self._make_trimmings_video(trimmings_end, "end")

    def _make_trimmings_video(self, trimmings, name):
        output_video = (
            self.coll.trimmed_start_video() if name == "start" else self.coll.trimmed_end_video()
        )
        hash_file = output_video + ".sha256"
        tmpdir = pjoin(self.output_dir, name + "-trimmings")
        if os.path.exists(hash_file):
            # TODO will fail if interrupted WHILE moving frames
            logging.warning(
                "{} trimmed frames video already exists at {}".format(name, output_video)
            )
            return
        if os.path.exists(output_video) or os.path.exists(tmpdir):
            warn_user(
                "Making {} trimmed frames video failed partway through.".format(name),
                "Deleting and remaking.",
            )
            logging.error(
                "Making {} trimmed frames video failed partway through. Deleting and remaking.".format(
                    name
                )
            )
        if len(trimmings) == 0:
            logging.error("No {} trimmed frames".format(name))
            warn_user(
                "No {} trimmed frames.".format(name),
                "Increase {} in {} to ensure that frames aren't lost.".format(
                    "padding_before_milliseconds"
                    if name == "start"
                    else "padding_after_milliseconds",
                    config.path,
                ),
            )
            return
        # moving to another disk is a little slower
        # but we don't want these deleted if sauronx fails
        # tmpdir = pjoin(config.temp_dir(), name + '-trimmings')
        logging.info("Trimmed {} {} frames. Compressing.".format(len(trimmings), name))
        make_dirs_perm(tmpdir)
        logging.debug("Created temp dir at {}".format(tmpdir))
        for frame in trimmings:
            if not pexists(pjoin(tmpdir, os.path.basename(frame))):
                shutil.move(
                    frame, tmpdir
                )  # we HAVE to move here so they're not seen when making the primary video
        self._run_ffmpeg(tmpdir, output_video)

    def _parse_stimulus_timing_file(self, path: str) -> List[datetime]:
        # datetime,id,intensity
        return [parse_local_iso_datetime(line.split(",")[0]) for line in list(lines(path))[1:]]

    def _parse_frame_timing_file(self):
        strftime_fmt = "%Y-%m-%dT%H:%M:%S.%f"
        raw_timing_file_path = self.coll.raw_snapshot_timing_log_file()
        proc_timing_file_path = self.coll.snapshot_timing_log_file()
        stream_cmd_call(["sudo", "chmod", "777", raw_timing_file_path])
        with open(raw_timing_file_path, "r+", encoding="utf8") as f:
            with open(proc_timing_file_path, "w", encoding="utf8") as o:
                reader = csv.reader(f)
                # get the two header lines?
                prev_datetime = parser.parse(next(reader)[0])
                # o.write("{}\n".format(prev_datetime.strftime(strftime_fmt))) # 20180920 added acquisition of an extra, unsaved frame before main acquisition loop
                prev_us = int(next(reader)[0]) / 1000
                for row in reader:
                    curr_us = int(row[0]) / 1000
                    diff_us = curr_us - prev_us
                    new_datetime = prev_datetime + timedelta(microseconds=diff_us)
                    o.write("{}\n".format(new_datetime.strftime(strftime_fmt)))
                    prev_datetime = new_datetime
                    prev_us = curr_us

    def _attempt_upload(self) -> None:
        logging.info("Uploading data via SSH...")
        self._scp_files()
        logging.info("Finished uploading data via SSH")

    def _scp_files(self) -> None:
        stream_cmd_call(
            [
                "scp",
                "-r",
                "-C",
                os.path.normpath(self.output_dir),
                str(self.upload_params["ssh_username"])
                + "@"
                + str(self.upload_params["hostname"])
                + ":"
                + self._remote_upload_dir(),
            ]
        )
        # noinspection PyBroadException
        try:
            self.sx_alive.notify_finished()
        except:
            warn_user("Failed to notify")
            logging.error("Failed to notify")

    def _remote_upload_dir(self) -> str:
        remote_dir = self.upload_params["remote_upload_path"]  # type: str
        return (
            str(self.upload_params["ssh_username"])
            + "@"
            + str(self.upload_params["hostname"])
            + ":"
            + remote_dir
            if remote_dir.endswith(os.sep)
            else remote_dir + os.sep
        )


__all__ = ["Results"]

import os
from pathlib import Path
from .utils import pexists, psize

sauronx_home = os.environ["SAURONX_HOME"]

lock_file = Path(sauronx_home, ".lock")


def processing_file(submission_hash: str) -> Path:
    return Path(sauronx_home, ".processing-" + submission_hash)


def processing_submission_hash_from_file(submission_hash: str) -> Path:
    return Path(submission_hash[len(".processing-"):])


def component_check_path(output_dir: str, trigger: str) -> Path:
    return Path(output_dir, trigger.lower())


def component_check_log_path(output_dir: str, trigger: str, filename: str) -> Path:
    return Path(output_dir, trigger.lower(), filename)


class SubmissionPathCollection:
    def __init__(self, path: Path, raw_frames_path: Path, submission_hash: Path):
        self.__path = path
        self.__raw_frames_path = raw_frames_path
        self.__submission_hash = submission_hash

    @property
    def output_dir(self):
        return self.__path

    @property
    def submission_hash(self) -> Path:
        return self.__submission_hash

    @property
    def webcam_snapshot(self) -> Path:
        return Path(self.__path, "sensors", "snap.jpg")

    @property
    def preview_snapshot(self) -> Path:
        return Path(self.__path, "sensors", "preview.jpg")

    @property
    def microphone_wav_path(self) -> Path:
        return Path(self.__path, "sensors", "microphone_log.wav")

    @property
    def microphone_flac_path(self) -> Path:
        return Path(self.__path, "sensors", "microphone_log.flac")

    @property
    def microphone_timestamps_path(self) -> Path:
        return Path(self.__path, "sensors", "microphone_times.txt")

    @property
    def avi_file(self) -> Path:
        return Path(self.__path, "camera", "x265-crf15", "x265-crf15.mkv")

    @property
    def toml_file(self) -> Path:
        return Path(self.__path, "config.toml")

    @property
    def env_file(self) -> Path:
        return Path(self.__path, "environment.properties")

    @property
    def log_file(self) -> Path:
        return Path(self.__path, "sauronx.log")

    @property
    def outer_frames_dir(self) -> Path:
        return Path(self.__raw_frames_path)

    @property
    def trimmed_dir(self) -> Path:
        return Path(self.__path, "trimmed_frames")

    @property
    def trimmed_start_video(self) -> Path:
        return Path(self.__path, "trimmed_frames", "start.mkv")

    @property
    def trimmed_end_video(self) -> Path:
        return Path(self.__path, "trimmed_frames", "end.mkv")

    @property
    def shasum_file(self) -> Path:
        return Path(self.__path, "frames.7z.sha256")

    @property
    def stimulus_timing_log_file(self):
        return Path(self.__path, "timing", "stimuli.csv")

    @property
    def raw_snapshot_timing_log_file(self):
        return Path(self.__path, "timing", "raw_camera_timing.csv")

    @property
    def snapshot_timing_log_file(self):
        return Path(self.__path, "timing", "snapshots.list.csv")

    @property
    def start_events_log_file(self):
        return Path(self.__path, "timing", "start_events.csv")

    @property
    def end_events_log_file(self):
        return Path(self.__path, "timing", "end_events.csv")

    def avi_exists(self) -> bool:
        return (
                        self.avi_file.exists()
                        and os.path.getsize(self.avi_file) > 0
                        and os.path.getsize(self.shasum_file) > 0
                        and pexists(os.path.join(self.avi_file, ".sha256")
                        and psize(self.avi_file) > 0
                        and psize(os.path.join(self.avi_file, ".sha256"))) > 0
        )

    def snapshot_timing_exists(self) -> bool:
        return (
            self.snapshot_timing_log_file.exists()
            and psize(self.snapshot_timing_log_file) > 0
            or pexists(self.raw_snapshot_timing_log_file)
            and psize(self.raw_snapshot_timing_log_file) > 0
        )

    def stimulus_timing_exists(self) -> bool:
        return (
            pexists(self.stimulus_timing_log_file) and psize(self.stimulus_timing_log_file) > 0
        )

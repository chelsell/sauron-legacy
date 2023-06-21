import io
import logging

from pocketutils.tools.call_tools import CallTools

from .configuration import config
from .utils import warn_user

class PointGreyCamera:
    def __init__(
        self, raw_frames_dir: str, snapshots_path: str, n_milliseconds: float, plate_type_id: int
    ) -> None:
        self.raw_frames_dir = raw_frames_dir
        self.snapshots_path = snapshots_path
        self.n_milliseconds = n_milliseconds
        self.framerate = config.camera["frames_per_second"]
        self.stdout = io.StringIO()
        self.plate_type_id = plate_type_id
        roi = config.camera_roi(plate_type_id)
        self.x_offset = roi.x0
        self.y_offset = roi.y0
        self.width = roi.x1 - roi.x0
        self.height = roi.y1 - roi.y0
        self.camera_executable = config.executables["pointgrey_acquisition"]

    def __enter__(self):
        self.setup()
        return self

    def __exit__(self, type, value, traceback) -> None:
        return None

    # Commenting out this method because the PGR script doesn't require much set-up time, but we may want to implement a setup step later
    def setup(self) -> None:
        """Only call this if you're not using Camera in a with statement."""
        pass  # logging.info("Starting camera setup..")

    def stream(self) -> None:
        raise NotImplementedError()

    def start(self) -> None:
        logging.info("Camera will capture for {}ms. Starting!".format(self.n_milliseconds))
        cmd = [
            "sudo",
            str(self.camera_executable),
            str(self.n_milliseconds),
            str(self.framerate),
            str(self.x_offset),
            str(self.y_offset),
            str(self.width),
            str(self.height),
            self.snapshots_path,
            self.raw_frames_dir,
        ]
        try:
            CallTools.stream_cmd_call(cmd)
        except Exception as e:
            logging.fatal("Camera failed.")
            warn_user("Failed calling camera. Is it connected?")
            raise e
        logging.info("Camera finished capturing.")

    def finish(self) -> None:
        pass


__all__ = ["PointGreyCamera"]

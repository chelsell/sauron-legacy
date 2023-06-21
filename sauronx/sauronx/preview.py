import io
import logging
import os
import sys
import time
import tkinter as tk
from subprocess import SubprocessError, check_call
from tkinter import PhotoImage
from typing import Callable, List, Optional
from pocketutils.core.exceptions import DirDoesNotExistError, FileDoesNotExistError
from pocketutils.tools.call_tools import CallTools
import cv2
from PIL import Image, ImageDraw, ImageTk

from .utils import plain_timestamp_started_with_millis, pjoin, make_dirs, pdir, warn_user

from .arduino import Board
from .configuration import Config, config

stderr = io.StringIO()


class WebcamSnapshotFailed(Exception):
    pass


class Previewer:
    def __init__(
        self, plate_type_id: int, temp_dir: Optional[str] = None, silence: bool = False
    ) -> None:
        if temp_dir is None:
            temp_dir = pjoin(config.temp_dir(), "snap")
        self.temp_dir = temp_dir
        make_dirs(self.temp_dir)
        if not pdir(self.temp_dir):
            raise DirDoesNotExistError("Temporary dir {} does not exist".format(self.temp_dir))
        self.plate_type_id = plate_type_id
        roi = config.camera_roi(plate_type_id)
        self.x_offset = str(roi.x0)
        self.y_offset = str(roi.y0)
        self.width = str(roi.x1 - roi.x0)
        self.height = str(roi.y1 - roi.y0)
        self.silence = silence
        self.executable = config.executables["pointgrey_snapshot"]

    def webcam_preview(self, board, path: Optional[str] = None) -> None:
        if path is None:
            path = pjoin("webcam-{}.jpg".format(plain_timestamp_started_with_millis))
        self.full_webcam_snapshot(path, board)
        if not os.path.exists(path):
            raise WebcamSnapshotFailed("The webcam snapshot at {} does not exist".format(path))
        if os.path.getsize(path) == 0:
            raise WebcamSnapshotFailed("The webcam snapshot at {} is empty".format(path))
        Image.open(path).show()

    def full_webcam_snapshot(self, webcam_path, b):
        stimuli = config["sauron.hardware.webcam.stimuli"]
        logging.info("Flashing {} to take webcam snapshot".format(", ".join(stimuli)))
        b.ir_off()
        for s, v in stimuli.items():
            b.set_stimulus(s, v)
        self.webcam_snapshot(webcam_path)
        b.ir_on()
        for s in stimuli:
            b.set_stimulus(s, 0)
        logging.info("Done.")
        return webcam_path

    def webcam_snapshot(self, path):
        cfg = config["sauron.hardware.webcam"]
        cap = cv2.VideoCapture(cfg["device_index"])
        cap.set(6, cv2.VideoWriter.fourcc("M", "J", "P", "G"))
        cap.set(3, cfg["width"])
        cap.set(4, cfg["height"])
        cap.set(15, cfg["exposure"])
        for i in range(0, 18):
            try:
                logging.debug("Webcam {}={}".format(i, cap.get(i)))
            except:
                logging.debug("Failed to read webcam {}".format(i))
        ret, frame = cap.read()
        cv2.imwrite(path, frame)

    def find_img(self, path: str, looping: bool) -> (str, Image):
        filee = self._last_snapshot(path)
        logging.debug("Found snapshot at {}".format(filee))
        img = self.make_img(filee, looping)
        return filee, img

    def make_img(self, path: str, looping: bool) -> Image:
        global config
        with CallTools.silenced(no_stdout=self.silence, no_stderr=False):
            if looping:
                config = Config()  # reload each time
            img = Image.open(path)
            draw = ImageDraw.Draw(img)
            for w in config.get_roi_coordinates(self.plate_type_id):
                draw.rectangle((w.x0, w.y0, w.x1, w.y1))
        return img

    def preview(self, b: Board) -> None:
        def task(snapshot):
            snapshot()
            path, img = self.find_img(self._snapshot_dir(), False)
            img.show()

        self._wrap(task)

    def snap_and_show(self) -> str:
        self._snapshot()
        path, img = self.find_img(self._snapshot_dir(), False)
        img.show()
        return path

    def live_preview(self, delay_ms: int = 200) -> None:
        root = tk.Tk()
        label = tk.Label(root)
        label.pack()
        # needs to be mutable and something something
        tkimg = [None]  # type: List[PhotoImage]
        logging.info("Entering live preview...")

        def task(snapshot):
            def loop():
                snapshot()  # capture the next frame, nothing more
                p, img = self.find_img(self._snapshot_dir(), looping=False)
                ix = ImageTk.PhotoImage(img)
                tkimg[0] = ix
                label.config(image=tkimg[0])
                root.update_idletasks()
                root.after(delay_ms, loop)

            loop()
            root.mainloop()

        self._wrap(task)

    def _wrap(self, task: Callable[[Callable[[None], None]], None]):
        """Run a task with everything set up to take a snapshot.
        :param task: A function that takes a 'snapshot' function to capture a new shot from the camera, and does something.
        """

        def snapshot() -> None:
            self._snapshot()

        time.sleep(0.1)  # probably unnecessary
        task(snapshot)

    def _snapshot(self):

        make_dirs(self._snapshot_dir())
        try:
            check_call(
                [
                    "sudo",
                    "{}".format(self.executable),
                    self._snapshot_dir(),
                    "0",
                    self.x_offset,
                    self.y_offset,
                    self.width,
                    self.height,
                ]
            )
        except SubprocessError:
            warn_user("Failed to start camera. Check the connection or restart the computer.")

    def _last_snapshot(self, path: str):
        matches = sorted(
            (
                pjoin(self._snapshot_dir(), f)
                for f in os.listdir(path)
                if os.path.isfile(os.path.join(path, f))
                and f.endswith(".jpg")
                and f.startswith("snapshot")
            ),
            reverse=True,
        )
        if len(matches) > 0:
            return matches[0]
        else:
            raise FileDoesNotExistError("No snapshot exists in {}".format(path))

    def _ml_roi(self) -> str:
        return " ".join([str(j) for j in config.camera["plate.{}.roi".format(self.plate_type_id)]])

    def _snapshot_dir(self) -> str:
        return self.temp_dir


if __name__ == "__main__":
    if len(sys.argv) > 1:
        Previewer(1).find_img(sys.argv[1], False)
    else:
        with Board() as board:
            Previewer(1).preview(board)

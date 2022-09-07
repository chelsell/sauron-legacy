"""
Non-changing settings tied to SauronX and the Shire.
"""
import hashlib
from pathlib import PurePath

from sauronlab.core._tools import InternalTools
from sauronlab.core.valar_singleton import *


class VideoCore:
    """"""

    shasum_filename: str = InternalTools.load_resource("core", "videos.json")["shasum_filename"]
    sha_algorithm = InternalTools.load_resource("core", "videos.json")["shasum_algorithm"]
    shire_crf: int = int(InternalTools.load_resource("core", "videos.json")["crf"])
    video_ext: str = InternalTools.load_resource("core", "videos.json")["ext"]
    codec: str = InternalTools.load_resource("core", "videos.json")["codec"]
    bitrate: str = InternalTools.load_resource("core", "videos.json")["bitrate"]
    filename: str = InternalTools.load_resource("core", "videos.json")["filename"]
    path: str = InternalTools.load_resource("core", "videos.json")["path"]
    hevc_params: str = InternalTools.load_resource("core", "videos.json")["hevc_params"]
    mp4_params: str = InternalTools.load_resource("core", "videos.json")["mp4_params"]

    @classmethod
    def get_remote_path(cls, run: Runs) -> PurePath:
        """

        Args:
            run: The runs instance

        Returns:
            The path to the video MKV file relative to (and under) the Shire.

        """
        # TODO hardcoded
        run = Runs.fetch(run)
        year = str(run.datetime_run.year).zfill(4)
        month = str(run.datetime_run.month).zfill(2)
        return PurePath(
            year,
            month,
            run.tag,
            *VideoCore.path.split("/"),
        )


__all__ = ["VideoCore"]

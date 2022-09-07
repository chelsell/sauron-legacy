"""
Contains the lowest-level code in Sauronlab.
This package cannot not depend on any other packages in Sauronlab.
"""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

from loguru import logger

# noinspection PyProtectedMember
from loguru._logger import Logger
from pocketutils.misc.loguru_utils import FancyLoguru, FANCY_LOGURU_DEFAULTS

from sauronlab import version as sauronlab_version


def _notice(__message: str, *args, **kwargs) -> None:
    logger.log("NOTICE", __message, *args, **kwargs)


def _caution(__message: str, *args, **kwargs):
    logger.log("CAUTION", __message, *args, **kwargs)


class MyLogger(Logger):
    """
    A wrapper that has fake methods to trick static analysis.
    """

    def notice(self, __message: str, *args, **kwargs):
        raise NotImplementedError()  # not real

    def caution(self, __message: str, *args, **kwargs):
        raise NotImplementedError()  # not real


class SauronlabResources:
    """ """

    @classmethod
    def path(cls, *parts) -> Path:
        return Path(Path(__file__).parent.parent, "resources", *parts)

    @classmethod
    def text(cls, *parts) -> str:
        return SauronlabResources.path(*parts).read_text(encoding="utf8")

    @classmethod
    def binary(cls, *parts) -> bytes:
        return SauronlabResources.path(*parts).read_bytes()


# WEIRD AS HELL, but it works
# noinspection PyTypeChecker
logger: MyLogger = logger
logger.notice = _notice
logger.caution = _caution
log_setup = FancyLoguru(logger).config_levels(colors=FANCY_LOGURU_DEFAULTS.colors_red_green_safe)

sauronlab_start_time = datetime.now()
sauronlab_start_clock = time.monotonic()


__all__ = [
    "sauronlab_version",
    "sauronlab_start_time",
    "sauronlab_start_clock",
    "log_setup",
    "SauronlabResources",
    "logger",
]

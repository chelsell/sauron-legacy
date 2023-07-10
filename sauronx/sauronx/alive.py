import datetime
import json
import logging
import os, sys, re
from enum import Enum
from typing import List, Optional

from pocketutils.full import Tools
from pocketutils.tools.call_tools import CallTools
from valarpy import Valar
from pocketutils.core.exceptions import LockedError, RefusingRequestError
from terminaltables import AsciiTable
from loguru import logger
from colorama import Fore
Valar().open()
from valarpy.model import *

from .utils import datetime_started_raw, warn_user

from .configuration import config
from .locks import ProcessingList, ProcessingSubmission, SauronxLock


class InterceptHandler(logging.Handler):
    """
    Redirects standard logging to loguru.
    """

    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def _notice(__message: str, *args, **kwargs):
    return logger.log("NOTICE", __message, *args, **kwargs)


class SauronxLogging:
    # this is required for mandos to run
    try:
        logger.level("NOTICE", no=35)
    except TypeError:
        # this happens if it's already been added (e.g. from an outside library)
        # if we don't have it set after this, we'll find out soon enough
        logger.debug("Could not add 'NOTICE' loguru level. Did you already set it?")
    logger.notice = _notice

    @classmethod
    def init(cls) -> None:
        """
        Sets an initial configuration.
        """
        cls.redirect_std_logging()
        cls.set_log_level("INFO", None)

    @classmethod
    def redirect_std_logging(cls, level: int = 10) -> None:
        # 10 b/c we're really never going to want trace output
        logging.basicConfig(handlers=[InterceptHandler()], level=level)

    @classmethod
    def set_log_level(cls, level: str, path: Optional[os.PathLike]) -> None:
        """
        This function will control all aspects of the logging as set via command-line.

        Args:
            level: The level to use for output to stderr
            path: If set, the path to a file. Can be prefixed with ``:level:`` to set the level
                  (e.g. ``:INFO:mandos-run.log.gz``). Can serialize to JSON if .json is used
                  instead of .log.
        """
        logger.remove()
        logger.add(sys.stderr, level=level)
        cls._add_path_logger(path)

    @classmethod
    def _add_path_logger(cls, path: os.PathLike) -> None:
        if path is None:
            return
        match = re.compile(r"(?:[A-Z]+:)??(.*)").match(str(path))
        level = "DEBUG" if match.group(1) is None else match.group(1)
        path = os.PathLike(match.group(2))
        for e, c in dict(gz="gzip", zip="zip", bz2="bzip2", xz="xz"):
            if str(path).endswith("." + e):
                serialize = True if path.suffix == f".json.{e}" else False
                logger.add(
                    str(path),
                    level=level,
                    compression=c,
                    serialize=serialize,
                    backtrace=True,
                    diagnose=True,
                )


valarpy_config_env_variable_name = "SAURONX_VALARPY_CONFIG"  # type: str


def _table(headers: List[str], rows: List[list], title=None) -> str:
    data = [headers]
    data.extend(rows)
    return AsciiTable(data, title=title).table


class StatusValue(Enum):
    # general status (in Valar)
    STARTING = 1
    CAPTURING = 2
    FINISHED_CAPTURE = 3
    UPLOADED = 4
    # failure codes (in Valar)
    FAILED_DURING_INITIALIZATION = 10
    CANCELLED_DURING_INITIALIZATION = 11
    FAILED_DURING_CAPTURE = 12
    CANCELLED_DURING_CAPTURE = 13
    FAILED_DURING_POSTPROCESSING = 14
    CANCELLED_DURING_POSTPROCESSING = 15
    FAILED_DURING_UPLOAD = 16
    CANCELLED_DURING_UPLOAD = 17
    # generic codes (in Valar)
    FAILED = 20
    CANCELLED = 21
    # debug statues
    COMPRESSING = 101
    UPLOADING = 102
    FAILED_CHECKS = 110
    STARTED_INCUBATION = 111
    FINISHED_INCUBATION = 112
    FAILED_INCUBATION = 113


# these correspond to the submission_records.status enum
IN_PROGRESS = {
    "starting",
    "capturing",
}
LOCALLY_FAILED = {
    "failed",
    "cancelled",
    "failed_during_initialization",
    "failed_during_capture",
    "failed_during_postprocessing",
    "failed_during_upload",
    "cancelled_during_capture",
}
POST_CAPTURE = {"finished_capture", "extracting", "compressing", "uploading"}
REMOTE = {
    "uploaded",
    "inserting",
    "inserting features",
    "inserting sensors",
    "insert failed",
    "available",
}


class SauronxAlive:
    """Handles a database connection from VALARPY_CONFIG and processing (submission) locks.
    For example, you can't prototype and submit at the same time.
    This should be reserved for commands that need the camera or Arduino board.
    """

    def __init__(
        self,
        submission_hash: Optional[str],
        db: Optional[Valar] = None,
        acquisition_start: bool = False,
        ignore_warnings: bool = False,
    ) -> None:
        """If submission_hash is None, don't try to access submission_obj or status_obj or call update_status."""
        self.db = None  # type: Valar
        self._internal_db = None  # type: bool
        self.submission_hash = None  # type: Optional[str]
        self.submission_obj = None  # type: Submissions
        self.sauron_obj = None  # type: Saurons
        self.status_obj = None  # type: Optional[SubmissionRecords]
        self._internal_db = db is None  # don't close if it was built outside
        self.ignore_warnings = ignore_warnings
        self.acquisition_start = acquisition_start
        self.submission_hash = submission_hash
        if self.submission_hash is not None:
            processing_list = ProcessingList.now()
            if self.submission_hash in processing_list:
                warn_user(
                    "Refusing to touch {}:".format(submission_hash),
                    "Another SauronX process appears to be handling it.",
                    "If this is wrong, run 'sauronx clear {}' to continue.".format(submission_hash),
                )
                raise LockedError(
                    "Refusing to touch {}: Another SauronX process appears to be handling it.".format(
                        submission_hash
                    )
                )
        if db is None:
            self.db = Valar()
        else:
            self.db = db
        try:
            if "connection.notification.slack_info_file" in config:
                with open(str(config["connection.notification.slack_info_file"]), "r") as file:
                    self._slack_hook = file.readline()
                    self._slack_user_dict = json.loads(file.readline())
        except Exception:
            warn_user("Failed to call notification")
            logger.error("Failed to call notification", exc_info=True)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, t, value, traceback):
        self.finish()

    def start(self):
        if self._internal_db: self.db.open()
        self.sauron_obj = self._fetch_sauron()
        if self.submission_hash is not None:
            ProcessingSubmission.from_hash(self.submission_hash).create()
            try:
                self.submission_obj = self._fetch_submission()
                if self.is_test:
                    self.username = "cole"
                else:
                    self.username = Users.select().where(Users.id == self.submission_obj.user_id).first().username
                self._init_status()
            except:
                ProcessingSubmission.from_hash(self.submission_hash).destroy()
                raise

    @property
    def is_test(self):
        return self.submission_hash == "_" * 12

    def finish(self):
        if self.submission_hash is not None:
            ProcessingSubmission.from_hash(self.submission_hash).destroy()
        if self._internal_db:
            self.db.close()

    def update_status(self, stat: StatusValue) -> None:
        if self.submission_hash is not None:
            try:
                if not self.is_test:
                    self.status_obj = SubmissionRecords(
                        submission=self.submission_obj,
                        created=datetime_started_raw,
                        datetime_modified=datetime.datetime.now(),
                        sauron=self.sauron_obj.id,
                        status=stat.name.lower()
                    )
                    self.status_obj.save()
                    description = self.submission_obj.description
                else:
                    description = "test"
                user = self._slack_user_dict[self.username]
                payload = '{{"text":"<@{}> S{} {} {} ({})"}}'.format(user, self.sauron_obj.id, stat.name.lower(),
                                                                     self.submission_hash, description)
                CallTools.stream_cmd_call(['curl', '-X', "POST", "-H", "'Content-type: application/json'", "--data", payload,
                               self._slack_hook.rstrip("\n")])
            except:
                warn_user("Failed to update status to {}".format(stat))
                logger.warning("Failed to update status to {}".format(stat))

    def notify_finished(self) -> None:
        pass

    def _fetch_sauron(self):
        import valarpy.model as model

        matches = list(model.Saurons.select().where(model.Saurons.id == config.sauron_id))
        if len(matches) != 1:
            raise ValueError("No Sauron with number {} exists!".format(config.sauron_name))
        return matches[0]

    def _fetch_submission(self):
        import valarpy.model as model

        sub = (
            model.Submissions.select(model.Submissions, model.Experiments, model.Users)
            .join(model.Users, on=(model.Submissions.user_id == model.Users.id))
            .switch(model.Submissions)
            .join(model.Experiments)
            .join(model.TemplatePlates)
            .join(model.PlateTypes)
            .switch(model.Experiments)
            .join(model.Batteries)
            .where(model.Submissions.lookup_hash == self.submission_hash)
            .first()
        )
        if self.is_test:
            return sub
        if sub is None:
            raise ValarLookupError(
                "No SauronX submission exists in Valar with submission hash {}".format(
                    self.submission_hash
                )
            )
        # make sure it wasn't already used
        matching_run = (
            model.Runs.select(model.Runs, model.Submissions)
            .join(model.Submissions)
            .where(model.Submissions.id == sub.id)
            .first()
        )
        if matching_run is not None:
            warn_user(
                "Can't continue: {} was already used for run r{}".format(
                    self.submission_hash, matching_run
                )
            )
            raise ValueError(
                "Submission hash {} was already used for run r{} ".format(
                    self.submission_hash, matching_run
                )
            )
        return sub

    def _init_status(self) -> None:
        if self.is_test:
            matches = None
            prev_run = None
            has_remote = 0
            has_post_capture = 0
            acquisition_starts = None
        else:
            matches = list(
                SubmissionRecords.select(SubmissionRecords) \
                    .where(SubmissionRecords.submission == self.submission_obj.id)
                    .order_by(SubmissionRecords.created.desc())
            )  # type: List[SubmissionRecords]
            # warn about prior runs
            prev_run = Runs.select().where(Runs.submission == self.submission_obj).first()
            has_remote = any(m.status in REMOTE for m in matches)
            has_post_capture = any(m.status in POST_CAPTURE for m in matches)
            acquisition_starts = [m.created for m in matches if m.status is StatusValue.CAPTURING]
        # TODO warn if n_acquisition_starts > 0
        if not self.ignore_warnings:
            if len(matches) > 0 and not SauronxLock().is_running_test():
                logging.warning(
                    "There are already {} submission record(s):\n{}\n".format(
                        len(matches),
                        _table(
                            ["id", "status", "inserted", "run_started"],
                            [[r.id, r.status, r.datetime_modified, r.created] for r in matches],
                        ),
                    )
                )
            msg = None  # keep only the highest precedence warning, using elif
            if prev_run is not None:
                msg = "The submission is already attached to run r{}".format(prev_run.id)
            elif has_remote:
                msg = "The submission was captured and already uploaded to Valinor."
            elif has_post_capture and self.acquisition_start:  # only worry if we're starting fresh
                msg = "The submission was already successfully captured."
            if msg is not None:
                warn_user("Refusing:", msg)
                print(Fore.RED + "Continue anyway? Not recommended. [yes/no]", end="")
                try:
                    ans = Tools.prompt_yes_no("")
                except KeyboardInterrupt:
                    raise RefusingRequestError(msg)
                if ans:
                    logging.warning(msg)
                else:
                    raise RefusingRequestError(msg)
            if len(acquisition_starts) > 0:
                logging.warning(
                    "Acquisition started {} times before: {}".format(
                        len(acquisition_starts), ", ".join(acquisition_starts)
                    )
                )
        self.update_status(StatusValue.STARTING)


__all__ = ["StatusValue", "SauronxAlive"]

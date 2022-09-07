import enum
import logging
import os
from typing import Iterator, Optional, Set

from sauronx import is_process_running, looks_like_submission_hash

from .paths import lock_file, processing_file, processing_submission_hash_from_file, sauronx_home

_generic_lock_string = "None"
_forced_lock_string = "--locked--"


class LockType(enum.Enum):
    DISENGAGED = 1
    SUBMISSION = 2
    GENERIC = 3
    FORCED = 4


class SauronxLock:
    """
    This is not global because other SauronX processes can change it.
    """

    def __init__(self) -> None:
        self.submission_hash = None  # type: str
        self.lock_type = None  # type: LockType
        self._read()
        if not self.is_engaged():
            self.lock_type = LockType.DISENGAGED
        elif self.submission_hash == _forced_lock_string:
            self.lock_type = LockType.FORCED
        elif self.submission_hash == _generic_lock_string:
            self.lock_type = LockType.GENERIC
        else:
            self.lock_type = LockType.SUBMISSION

    def __contains__(self, item: str):
        return self.is_engaged() and self.submission_hash == item

    # TODO distinguish between is and was locked

    def is_engaged(self) -> bool:
        return self.submission_hash is not None

    def is_running_submission(self) -> bool:
        """Is running a submission or test."""
        return self.submission_hash is not None and self.submission_hash != _generic_lock_string

    def is_running_generic(self) -> bool:
        """Generally means running in incubation."""
        return self.submission_hash is not None and self.submission_hash == _generic_lock_string

    def is_running_test(self) -> bool:
        return self.submission_hash is not None and self.submission_hash.startswith("_")

    def is_running_forced(self) -> bool:
        return self.submission_hash is not None and self.submission_hash == _forced_lock_string

    def engage(self, submission_hash: Optional[str], replace: bool = False) -> None:
        if self.is_engaged() and not replace:
            raise LockedException("Appears locked with {}".format(self.submission_hash))
        self.submission_hash = submission_hash
        with open(lock_file, "w") as f:
            f.write(str(self.submission_hash))
        logging.debug("Engaged lock with submission {}".format(self.submission_hash))

    def engage_forced(self, replace: bool = False):
        self.engage(_forced_lock_string, replace=replace)

    def engage_generic(self, replace: bool = False):
        self.engage(_generic_lock_string, replace=replace)

    def disengage(self) -> None:
        prev = self.submission_hash
        os.remove(lock_file)
        logging.debug("Disengaged lock (had submission {})".format(prev))

    def _read(self) -> None:
        if os.path.exists(lock_file):
            with open(lock_file) as f:
                self.submission_hash = f.read().replace("\n", "")
        else:
            self.submission_hash = None

    def lock(self, submission_hash: Optional[str], replace: bool = False):
        """
        Higher-level than engage(). Notifies the user and makes sure the lock isn't already engaged.
        :param submission_hash: Can be None for generic lock types
        :param replace: Force a new lock on
        """
        if SauronxLock().is_engaged():
            if is_process_running():
                warn_user(
                    "SauronX appears to be locked, and a SauronX process is running.",
                    "If this is wrong, run 'sauronx unlock'",
                )
                raise LockedException("SauronX appears to be locked by another SauronX process.")
            else:
                warn_user(
                    "SauronX is locked but there is no SauronX process running!",
                    "Confirm this and run 'sauronx unlock' to proceed.",
                )
                raise LockedException("SauronX is locked but there is no SauronX process running!")
        SauronxLock().engage(submission_hash, replace=replace)
        notify_user(
            "SauronX lock acquired. You cannot run submit, prototype, or preview until it is released.",
            "If you need to cancel SauronX, type CTRL-C exactly once (then be patient).",
        )

    def unlock(self, ignore_warning: bool = False) -> None:
        """
        Higher-level than disengage(). Notifies the user.
        """
        if SauronxLock().is_engaged():
            # logging.info("Freeing the SauronX lock")
            SauronxLock().disengage()
            notify_user("SauronX lock released. You can now run any SauronX command.")
        elif not ignore_warning:
            logging.warning(
                "Requested lock disengagement, but SauronX is not locked. This is potentially a mistake in the code."
            )


class ProcessingSubmission:
    def __init__(self, submission_hash: str, file: str):
        assert looks_like_submission_hash(
            submission_hash
        ), "{} does not look like a submission hash".format(submission_hash)
        self.submission_hash = submission_hash
        self.file = file

    def __hash__(self):
        return self.submission_hash.__hash__()

    def __str__(self):
        return self.submission_hash

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.submission_hash == other.submission_hash

    def create(self):
        with open(processing_file(self.submission_hash), "w") as f:
            f.write("")

    def destroy(self):
        if os.path.exists(self.file):
            os.remove(self.file)

    @staticmethod
    def from_file(path: str):
        return ProcessingSubmission(processing_submission_hash_from_file(path), path)

    @staticmethod
    def from_hash(submission_hash: str):
        return ProcessingSubmission(submission_hash, processing_file(submission_hash))


class ProcessingList:
    def __init__(self, submissions: Set[ProcessingSubmission]):
        self.submissions = submissions

    def __str__(self):
        return ", ".join([str(s) for s in self.submissions])

    def __len__(self):
        return len(self.submissions)

    def __contains__(self, item: ProcessingSubmission):
        if isinstance(item, str):
            return len([i for i in self.submissions if i.submission_hash == item]) > 0
        elif isinstance(item, ProcessingSubmission):
            return item in self.submissions
        else:
            raise TypeError("Invalid type {} for {}".format(type(item), item))

    def __iter__(self) -> Iterator[ProcessingSubmission]:
        return iter(self.submissions)

    def __iadd__(self, other: ProcessingSubmission):
        self.submissions.add(other)
        other.create()

    def __isub__(self, other: ProcessingSubmission):
        other.destroy()
        self.submissions.remove(other)

    @staticmethod
    def now():
        return ProcessingList(
            {
                ProcessingSubmission.from_file(f)
                for f in os.listdir(sauronx_home)
                if f.startswith(".processing-")
            }
        )


__all__ = ["ProcessingList", "ProcessingSubmission", "SauronxLock"]

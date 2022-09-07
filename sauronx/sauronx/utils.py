import datetime
import logging
import os
import re
import time
from typing import List

from pocketutils.misc.fancy_console import ColorMessages


def stamp(dt):
    # workaround for https://bugs.python.org/issue19475
    s = dt.isoformat()  # can't do timespec='microseconds' till Python 3.6
    return s if "." in s else s + "." + (6 * "0")


def is_process_running() -> bool:
    # we're already running one process, so check for two
    return len(list(os.popen('ps ax | grep "/bin/bash .* sauronx.main" | grep -v grep'))) > 1


# TODO how are timezones handled?
clock_start = time.monotonic()
datetime_started_raw = datetime.datetime.now()  # type: datetime.datetime
plain_timestamp_started = datetime_started_raw.strftime("%Y-%m-%d_%H-%M-%S")  # type: str
pretty_timestamp_started = datetime_started_raw.strftime("%Y-%m-%d %H:%M:%S")  # type: str
pretty_timestamp_started_with_millis = stamp(datetime_started_raw).replace("T", " ")  # type: str
plain_timestamp_started_with_millis = (
    stamp(datetime_started_raw).replace("T", "_").replace(":", "_")
)  # type: str
iso_timestamp_started = stamp(datetime_started_raw)  # type: str

_hash_regex = re.compile("[0-9a-f]{12}")


def looks_like_submission_hash(submission_hash: str) -> bool:
    # use regex rather than int(submission_hash, 16) so we can require lowercase like Valinor spits out
    return submission_hash == "_" * 12 or _hash_regex.match(submission_hash) is not None


log_dir = fix_path(os.environ["SAURONX_LOG_DIR"])  # type: str
make_dirs(log_dir)
log_path = pjoin(log_dir, "sauronx-{}.log".format(plain_timestamp_started))  # type: str
init_logger(log_path)
# make a 90x90 box in the log file to make restarts obvious
logging.debug("\n")
logging.debug("/" + ("—" * 88) + "\\")
for i in range(0, 90):
    logging.debug("|" + ("*" * 88) + "|")
logging.debug("\\" + ("—" * 88) + "/")
logging.debug("\n")
logging.info(
    " Starting SauronX {} at {} ".format(
        sauronx_version, pretty_timestamp_started_with_millis
    ).center(90, "-")
)
logging.debug("Testing logging at debug level")
logging.getLogger("peewee").setLevel(logging.WARNING)
logging.getLogger("klgists").setLevel(logging.DEBUG)
logging.getLogger("asyncio").setLevel(logging.DEBUG)
# logging.basicConfig(level=logging.DEBUG)
# logging.getLogger("klgists.files").setLevel(logging.DEBUG)


# TODO this is hacky
def append_log_to_submission_log(submission_hash: str) -> str:
    # We'll now log to this file, too
    # But we also want to copy what we already logged
    new_log_path = pjoin(log_dir, "sx-submission-{}.log".format(submission_hash))  # type: str
    logging.info("Will switch {} ---> {}".format(log_path, new_log_path))
    with open(log_path) as old, open(new_log_path, "a") as new:
        for line in old:
            new.write(line)
    init_logger(new_log_path, to_std=False)
    logging.info("Switched {} ---> {}".format(log_path, new_log_path))
    logging.debug("Testing logging at debug level")
    return new_log_path


def show_table(headers: List[str], rows: List[list], title=None) -> str:
    data = [headers]
    data.extend(rows)
    return AsciiTable(data, title=title).table


class ImmutableModificationError(Exception):
    pass


class Immutable:
    def __setattr__(self, *args):
        raise ImmutableModificationError()

    def __delattr__(self, *args):
        raise ImmutableModificationError()


class Mutable:
    pass


def prompt_yes_no(msg: str) -> bool:
    try:
        while True:
            print(Fore.BLUE + msg + " ", end="")
            command = input("")
            if command.lower() == "yes":
                return True
            elif command.lower() == "no":
                return False
            else:
                print(Fore.BLUE + "Enter 'yes' or 'no'.")
    except KeyboardInterrupt:
        return False

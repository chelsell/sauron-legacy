import datetime
import logging
import os
import re
import time
import stat
from typing import List, Optional, Callable, Any, Union, Iterable, Iterator
from colorama import Fore, Style
from pocketutils.tools.path_tools import PathTools
from terminaltables import AsciiTable
from sauronx import sauronx_version
import argparse
import shutil
from pocketutils.core.exceptions import PathError, NaturalExpectedError, RefusingRequestError
from subprocess import Popen, PIPE
from enum import Enum
import numpy as np
import struct
import hashlib
import io
import gzip
from itertools import chain

logger = logging.getLogger(__name__)
pjoin = os.path.join
pexists = os.path.exists
pdir = os.path.isdir
pfile = os.path.isfile
pis_dir = os.path.isdir
psize = os.path.getsize


def fsize(num):
    """
    this function will convert bytes to MB.... GB... etc
    """
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0


def stamp(dt):
    # workaround for https://bugs.python.org/issue19475
    s = dt.isoformat()  # can't do timespec='microseconds' till Python 3.6
    return s if "." in s else s + "." + (6 * "0")


def is_process_running() -> bool:
    # we're already running one process, so check for two
    return len(list(os.popen('ps ax | grep "/bin/bash .* sauronx.main" | grep -v grep'))) > 1


def make_dirs(output_dir: str):
    """Makes a directory if it doesn't exist.
    May raise a PathIsNotADirError.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    elif not os.path.isdir(output_dir):
        raise PathError("{} already exists and is not a directory".format(output_dir))


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


log_dir = PathTools.sanitize_path(os.environ["SAURONX_LOG_DIR"])  # type: str
make_dirs(log_dir)
log_path = pjoin(log_dir, "sauronx-{}.log".format(plain_timestamp_started))  # type: str
# init_logger(log_path)
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
    if pexists(log_path):
        with open(log_path) as old, open(new_log_path, "a") as new:
            for line in old:
                new.write(line)
        # init_logger(new_log_path, to_std=False)
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


def remake_dirs(output_dir: str):
    """Makes a directory, remaking it if it already exists.
    May raise a PathIsNotADirError.
    """
    if os.path.exists(output_dir) and os.path.isdir(output_dir):
        shutil.rmtree(output_dir)
    elif os.path.exists(output_dir):
        raise PathError("{} already exists and is not a directory".format(output_dir))
    make_dirs(output_dir)


class SubcommandHandler:
    """A convenient wrapper for a program that uses command-line subcommands.
    Calls any method that belongs to the target
    :param parser: Should contain a description and help text, but should NOT contain any arguments.
    :param target: An object (or type) that contains a method for each subcommand; a dash (-) in the argument is converted to an underscore.
    :param temp_dir: A temporary directory
    :param error_handler: Called logging any exception except for KeyboardInterrupt or SystemExit (exceptions in here are ignored)
    :param cancel_handler: Called after logging a KeyboardInterrupt or SystemExit (exceptions in here are ignored)
    """

    def __init__(self,
                 parser: argparse.ArgumentParser, target: Any,
                 temp_dir: Optional[str] = None,
                 error_handler: Callable[[BaseException], None] = lambda e: None,
                 cancel_handler: Callable[[Union[KeyboardInterrupt, SystemExit]], None] = lambda e: None
                 ) -> None:
        parser.add_argument('subcommand', help='Subcommand to run')
        self.parser = parser
        self.target = target
        self.temp_dir = temp_dir
        self.error_handler = error_handler
        self.cancel_handler = cancel_handler

    def run(self, args: List[str]) -> None:

        full_args = self.parser.parse_args(args[1:2])
        subcommand = full_args.subcommand.replace('-', '_')

        if not hasattr(self.target, subcommand) and not subcommand.startswith('_'):
            print(Fore.RED + 'Unrecognized subcommand {}'.format(subcommand))
            self.parser.print_help()
            return

        # clever; from Chase Seibert: https://chase-seibert.github.io/blog/2014/03/21/python-multilevel-argparse.html
        # use dispatch pattern to invoke method with same name
        try:
            if self.temp_dir is not None:
                if pexists(self.temp_dir) and pdir(self.temp_dir):
                    shutil.rmtree(self.temp_dir)
                elif pexists(self.temp_dir):
                    raise PathError(self.temp_dir)
                remake_dirs(self.temp_dir)
                logger.debug("Created temp dir at {}".format(self.temp_dir))
            getattr(self.target, subcommand)()
        except NaturalExpectedError as e:
            pass  # ignore totally
        except KeyboardInterrupt as e:
            try:
                logger.fatal("Received cancellation signal", exc_info=True)
                self.cancel_handler(e)
            except BaseException:
                pass
            raise e
        except SystemExit as e:
            try:
                logger.fatal("Received system exit signal", exc_info=True)
                self.cancel_handler(e)
            except BaseException:
                pass
            raise e
        except BaseException as e:
            try:
                logger.fatal("{} failed!".format(self.parser.prog), exc_info=True)
                self.error_handler(e)
            except BaseException:
                pass
            raise e
        finally:
            if self.temp_dir is not None:
                if pexists(self.temp_dir):
                    logger.debug("Deleted temp dir at {}".format(self.temp_dir))
                    shutil.rmtree(self.temp_dir)
                    try:
                        os.remove(self.temp_dir)
                    except IOError:
                        pass


def warn_user(*lines: str):
    print()
    warn_thin(*lines)
    print()


def warn_thin(*lines: str):
    print_to_user(['', *lines, ''], Fore.RED)


def notify_user(*lines: str):
    print()
    notify_thin(*lines)
    print()


def notify_thin(*lines: str):
    print_to_user(['', *lines, ''], Fore.BLUE)


def success_to_user(*lines: str):
    print()
    success_to_user_thin(*lines)
    print()


def success_to_user_thin(*lines: str):
    print_to_user(['', *lines, ''], Fore.GREEN)


def concern_to_user(*lines: str):
    print()
    concern_to_user_thin(*lines)
    print()


def concern_to_user_thin(*lines: str):
    print_to_user(['', *lines, ''], Fore.MAGENTA)


def notify_user_light(*lines: str):
    print()
    notify_light_thin(*lines)
    print()


def notify_light_thin(*lines: str):
    print_to_user(['', *lines, ''], Style.BRIGHT, sides='')


def header_to_user(*lines: str):
    print_to_user(lines, Style.BRIGHT)


def print_to_user(lines: Iterable[str], color: int, top: str = '_', bottom: str = '_', sides: str = '',
                  line_length: int = 100):
    def cl(text: str): print(str(color) + sides + text.center(line_length - 2 * len(sides)) + sides)

    print(str(color) + top * line_length)
    logger.debug(top * line_length)
    for line in lines:
        logger.debug(line)
        cl(line)
    print(str(color) + bottom * line_length)
    logger.debug(bottom * line_length)


def git_commit_hash(git_repo_dir: str = '.') -> str:
    """Gets the hex of the most recent Git commit hash in git_repo_dir."""
    p = Popen(['git', 'rev-parse', 'HEAD'], stdout=PIPE, cwd=git_repo_dir)
    (out, err) = p.communicate()
    exit_code = p.wait()
    if exit_code != 0: raise ValueError("Got nonzero exit code {} from git rev-parse".format(exit_code))
    return out.decode('utf-8').rstrip()


def is_process_running() -> bool:
    # we're already running one process, so check for two
    return len(list(os.popen("ps ax | grep \"/bin/bash .* sauronx.main\" | grep -v grep"))) > 1


def show_table(headers: List[str], rows: List[list], title=None) -> str:
    data = [headers]
    data.extend(rows)
    return AsciiTable(data, title=title).table


class Deletion(Enum):
    NO = 1
    TRASH = 2
    HARD = 3


def deletion_fn(path) -> Optional[Exception]:
    """
    Deletes files or directories, which should work even in Windows.
    :return Returns None, or an Exception for minor warnings
    """
    # we need this because of Windows
    chmod_err = None
    try:
        os.chmod(path, stat.S_IRWXU)
    except Exception as e:
        chmod_err = e
    # another reason for returning exception:
    # We don't want to interrupt the current line being printed like in slow_delete
    if os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)  # ignore_errors because of Windows
        try:
            os.remove(path)  # again, because of Windows
        except IOError:
            pass  # almost definitely because it doesn't exist
    else:
        os.remove(path)
    logger.debug("Permanently deleted {}".format(path))
    return chmod_err


def prompt_and_delete(
    path: str,
    trash_dir: str = os.path.join(os.environ['HOME'], '.Trash'),
    allow_dirs: bool = True,
    show_confirmation: bool = True,
    dry: bool = False,
    allow_ignore: bool = True,
    delete_fn: Callable[[str], None] = deletion_fn
) -> Deletion:
    """

    :param path:
    :param trash_dir: The directory of a trashbin ('~/.Trash' by default)
    :param allow_dirs: Allow deleting full directory trees; set to False for safety
    :param show_confirmation: Print the action to stdout (ex: 'Trashed abc.txt to ~/.Trash')
    :param dry: If True, will only return the Deletion object to be handled outside
    :param allow_ignore: Allow entering an empty string to mean ignore
    :return: A Deletion enum reflecting the chosen action
    :param delete_fn: Function that actually deletes
    """

    if not allow_dirs and os.path.isdir(path):
        raise RefusingRequestError('Cannot delete directory {}; only files are allowed'.format(path))

    choices = [Deletion.NO.name.lower(), Deletion.TRASH.name.lower(), Deletion.HARD.name.lower()]

    def poll(command: str) -> Deletion:

        if command.lower() == Deletion.HARD.name.lower():
            if show_confirmation: print(Style.BRIGHT + "Permanently deleted {}".format(path))
            if dry:
                logger.debug("Operating in dry mode. Would otherwise have deleted {}".format(path))
            else:
                delete_fn(path)
                logger.debug("Permanently deleted {}".format(path))
            return Deletion.HARD

        elif command.lower() == Deletion.TRASH.name.lower():
            if dry:
                logger.debug("Operating in dry mode. Would otherwise have trashed {} to {}".format(path, trash_dir))
            else:
                shutil.move(path, trash_dir)
                logger.debug("Trashed {} to {}".format(path, trash_dir))
            if show_confirmation: print(Style.BRIGHT + "Trashed {} to {}".format(path, trash_dir))
            return Deletion.TRASH

        elif command.lower() == Deletion.NO.name.lower() or len(command) == 0 and allow_ignore:
            logger.debug("Will not delete {}".format(path))
            return Deletion.NO

        else:
            print(Fore.RED + "Enter {}".format(' or '.join(choices)))
            return None

    while True:
        print(Fore.BLUE + "Delete? [{}]".format('/'.join(choices)), end='')
        command = input('').strip()
        # logger.debug("Received user input {}".format(command))
        polled = poll(command)
        if polled is not None: return polled


def scan_for_files(path: str, follow_symlinks: bool = False) -> Iterator[str]:
    """
    Using a generator, list all files in a directory or one of its subdirectories.
    Useful for iterating over files in a directory recursively if there are thousands of file.
    Warning: If there are looping symlinks, follow_symlinks will return an infinite generator.
    """
    for d in os.scandir(path):
        if d.is_dir(follow_symlinks=follow_symlinks):
            yield from scan_for_files(d.path)
        else:
            yield d.path


def blob_to_byte_array(bytes_obj: bytes):
    return _blob_to_dt(bytes_obj, 'b', 1, np.ubyte) + 128


def blob_to_float_array(bytes_obj: bytes):
    return _blob_to_dt(bytes_obj, 'f', 4, np.float32)


def blob_to_double_array(bytes_obj: bytes):
    return _blob_to_dt(bytes_obj, 'd', 8, np.float64)


def blob_to_short_array(bytes_obj: bytes):
    return _blob_to_dt(bytes_obj, 'H', 2, np.int16)


def blob_to_int_array(bytes_obj: bytes):
    return _blob_to_dt(bytes_obj, 'I', 4, np.int32)


def blob_to_long_array(bytes_obj: bytes):
    return _blob_to_dt(bytes_obj, 'Q', 8, np.int64)


def _blob_to_dt(bytes_obj: bytes, data_type_str: str, data_type_len: int, dtype):
    return np.array(
        next(iter(struct.iter_unpack('>' + data_type_str * int(len(bytes_obj) / data_type_len), bytes_obj))),
        dtype=dtype)


def write_hash_file(path: os.PathLike | str, alg: str = "sha256") -> str:
    """
    Calculates the hash of a file and writes the hex-encoded value to a ``.sha256`` (e.g.) file and returns it.
    """
    hash_file = path.parent / (path.name + "." + alg)
    alg_fn = getattr(hashlib, alg)()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(16 * 1024), b""):
            alg_fn.update(chunk)
    hex_digest = alg_fn.hexdigest()
    hash_file.write_text(hex_digest, encoding="utf-8")
    return hex_digest


def is_proper_file(path: str) -> bool:
    name = os.path.split(path)[1]
    return len(name) > 0 and name[0] not in {'.', '~', '_'}


def scantree(path: str, follow_symlinks: bool = False) -> Iterator[str]:
    """List the full path of every file not beginning with '.', '~', or '_' in a directory, recursively.
    .. deprecated Use scan_for_proper_files, which has a better name
    """
    for entry in os.scandir(path):
        if entry.is_dir(follow_symlinks=follow_symlinks):
            yield from scantree(entry.path)
        elif is_proper_file(entry.path):
            yield entry.path


scan_for_proper_files = scantree


def parse_local_iso_datetime(z: str) -> datetime:
    return datetime.datetime.strptime(z, '%Y-%m-%dT%H:%M:%S.%f')


def lines(file_name: str, known_encoding='utf-8') -> Iterator[str]:
    """Lazily read a text file or gzipped text file, decode, and strip any newline character (\n or \r).
    If the file name ends with '.gz' or '.gzip', assumes the file is Gzipped.
    Arguments:
        known_encoding: Applied only when decoding gzip
    """
    file_name = str(file_name)
    if file_name.endswith('.gz') or file_name.endswith('.gzip'):
        with io.TextIOWrapper(gzip.open(file_name, 'r'), encoding=known_encoding) as f:
            for line in f: yield line.rstrip('\n\r')
    else:
        with open(file_name, 'r') as f:
            for line in f: yield line.rstrip('\n\r')


def nice_time(n_ms: int) -> str:
    length = datetime.datetime(1, 1, 1) + datetime.timedelta(milliseconds=n_ms)
    if n_ms < 1000 * 60 * 60 * 24:
        return "{}h, {}m, {}s".format(length.hour, length.minute, length.second)
    else:
        return "{}d, {}h, {}m, {}s".format(length.day, length.hour, length.minute, length.second)


def flatten(*iterable):
    return list(chain.from_iterable(iterable))

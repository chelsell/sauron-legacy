import shutil
from enum import Enum
from typing import Any, Callable, Dict, Iterator, Optional

from pocketutils.core.exceptions import (
    LookupFailedError,
    MissingResourceError,
    RefusingRequestError,
)
from peewee import JOIN
from valarpy.Valar import Valar

from sauronx import is_process_running, show_table

from .alive import SauronxAlive
from .configuration import config
from .locks import SauronxLock
from .paths import *
from .paths import SubmissionPathCollection
from .results import Results


class Recommendation(Enum):

    DELETE = 1
    CONTINUE_RAW = 2
    CONTINUE = 3
    LEAVE = 4
    IGNORE_NO_OPTION = 5

    # TODO this class is terribly written

    def ask(self, coll: SubmissionPathCollection, db: Valar, skip_ignores: bool) -> None:
        path, raw_frames_path = coll.output_dir(), coll.outer_frames_dir()
        if self is Recommendation.DELETE:
            # don't actually delete in prompt_and_delete
            # instead, save to delete both path and output frames
            choice = prompt_and_delete(
                path, allow_dirs=True, trash_dir=config.trash_path(path), delete_fn=lambda p: None
            )
            # first delete raw frames
            if pexists(raw_frames_path) and choice == Deletion.HARD and pexists(raw_frames_path):
                slow_delete(raw_frames_path, 2)
                if pexists(raw_frames_path):
                    os.rmdir(raw_frames_path)
            elif pexists(raw_frames_path) and choice == Deletion.TRASH and pexists(raw_frames_path):
                slow_delete(raw_frames_path, 2)
                if pexists(raw_frames_path):
                    os.rmdir(raw_frames_path)
            # now delete output dir
            if choice == Deletion.HARD and pexists(path):
                slow_delete(path, 2)
                if pexists(path):
                    os.rmdir(path)
            elif choice == Deletion.TRASH and pexists(path):
                shutil.move(path, config.trash_path(path))
        elif self is Recommendation.CONTINUE_RAW:
            self._trash_move_leave_continue(
                coll,
                db,
                True,
                False,
                True,
                "Enter nothing to ignore, 'fix' (RECOMMENDED), or 'hard' to hard-delete.",
            )
        elif self is Recommendation.CONTINUE:
            self._trash_move_leave_continue(
                coll,
                db,
                True,
                True,
                True,
                "Enter nothing to ignore, 'fix' (RECOMMENDED), 'trash', or 'hard' to hard-delete.",
            )
        elif not skip_ignores and self is Recommendation.LEAVE:
            self._trash_move_leave_continue(
                coll,
                db,
                False,
                True,
                True,
                "Enter nothing to ignore (RECOMMENDED), 'trash', or 'hard' to hard-delete.",
            )

    def accept(self, coll: SubmissionPathCollection, db: Valar) -> None:
        output_dir = coll.output_dir()
        if self is Recommendation.DELETE:
            shutil.move(output_dir, config.trash_path(output_dir))
        elif self is Recommendation.CONTINUE or self is Recommendation.CONTINUE_RAW:
            self._proceed(coll, db)

    def _trash_move_leave_continue(
        self,
        coll: SubmissionPathCollection,
        db: Valar,
        continuable: bool,
        trashable: bool,
        deletable: bool,
        msg: str,
    ) -> None:
        output_dir = coll.output_dir()
        raw_frames_path = coll.outer_frames_dir()
        while True:
            command = input("[{}] ... ".format(msg))
            print("Deleteable" if deletable else "Not deleteable")
            if (
                command.lower() == "leave"
                or command.lower() == "keep"
                or command.lower() == "skip"
                or len(command.strip()) == 0
            ):
                break
            elif deletable and command.lower() == "hard":
                if os.path.exists(raw_frames_path):
                    slow_delete(raw_frames_path, 2)
                if pexists(output_dir):
                    slow_delete(output_dir, 2)
            elif trashable and command.lower() == "trash":
                if os.path.exists(raw_frames_path):
                    slow_delete(raw_frames_path, 2)
                    print(Fore.BLUE + "Deleted {}".format(raw_frames_path))
                if pexists(output_dir):
                    shutil.move(output_dir, config.trash_path(output_dir))
                else:
                    print(Fore.RED + "{} does not exist".format(output_dir))
                print(Fore.BLUE + "Trashed {}".format(output_dir))
                break
            elif continuable and command.lower() == "fix":
                self._proceed(coll, db)
                break
            else:
                print(Fore.RED + msg)

    def _proceed(self, coll: SubmissionPathCollection, db: Valar) -> None:
        output_dir = coll.output_dir()
        with open(pjoin(output_dir, "submission_hash.txt")) as f:
            submission_hash = f.read()
        with SauronxAlive(submission_hash, db) as sx_alive:
            results = Results(sx_alive, output_dir)
            try:
                results = Results(sx_alive, output_dir)
                if not coll.snapshot_timing_exists():
                    raise MissingResourceException("Can't proceed: capture didn't complete")
                if not coll.avi_exists():
                    results.make_video()
                results.upload()
            except MissingResourceException as e:
                warn_user(str(e))


class Verdict(Enum):

    TEST = 1
    AVAILABLE = 2
    IDLE_ON_VALINOR = 3
    FAILED_REMOTELY = 4
    FAILED_LOCALLY = 5
    UNRECOVERABLE = 6
    INVALID = 7
    CURRENTLY_RUNNING = 8
    BEING_INSERTED = 9
    HANDLED_BY_OTHER = 10
    FAILED_ENCODING = 11

    def recommendation(self) -> Recommendation:
        return self._recommendations()[self.name]

    def message(self, entry) -> str:
        return Verdict._messages(entry)[self.name]

    @staticmethod
    def _recommendations():
        return {
            "TEST": Recommendation.DELETE,
            "AVAILABLE": Recommendation.DELETE,
            "IDLE_ON_VALINOR": Recommendation.DELETE,
            "FAILED_REMOTELY": Recommendation.DELETE,
            "FAILED_LOCALLY": Recommendation.CONTINUE,
            "FAILED_ENCODING": Recommendation.CONTINUE_RAW,
            "UNRECOVERABLE": Recommendation.DELETE,
            "INVALID": Recommendation.DELETE,
            "CURRENTLY_RUNNING": Recommendation.IGNORE_NO_OPTION,
            "BEING_INSERTED": Recommendation.DELETE,
            "HANDLED_BY_OTHER": Recommendation.IGNORE_NO_OPTION,
        }

    @staticmethod
    def _messages(entry):
        return {
            "TEST": Fore.RED
            + """
                This is a run of the test battery.
                Delete it with 'rm -r {}'
            """.replace(
                "\t", ""
            ).format(
                entry.path
            ),
            "AVAILABLE": Fore.GREEN
            + """
                The verdict: The data is safely in Valar.
                Trash it with 'mv {} {}'
            """.replace(
                "\t", ""
            ).format(
                entry.path, config.trash_path(entry.path)
            ),
            "IDLE_ON_VALINOR": Fore.GREEN
            + """
                The verdict: The data was uploaded, but processing has not started.
                Leave this for now to be safe. You can delete this if you need the space.
            """.replace(
                "\t", ""
            ),
            "FAILED_REMOTELY": Fore.GREEN
            + """
                The verdict: The data was uploaded but failed on insertion.
                Leave this for now to be safe. You can delete this if you need the space.
            """.replace(
                "\t", ""
            ),
            "FAILED_ENCODING": Fore.CYAN
            + """
                The verdict: The capture completed, but encoding failed.
                Urgently, fix it by running 'sauronx continue {}'
            """.replace(
                "\t", ""
            ).format(
                entry.path
            ),
            "FAILED_LOCALLY": Fore.CYAN
            + """
                The verdict: SauronX failed, but the capture completed successfully.
                Fix it by running 'sauronx continue {}'
            """.replace(
                "\t", ""
            ).format(
                entry.path
            ),
            "UNRECOVERABLE": Fore.RED
            + """
                The verdict: The video capture or log writing did not complete, rendering this data either unrecoverable
                or very difficult to recover.
                Trash it by running 'mv {} {}'
            """.replace(
                "\t", ""
            ).format(
                entry.path, config.trash_path(entry.path)
            ),
            "INVALID": Fore.RED
            + """
                The verdict: The submission at path {} does not exist in Valar.
                Unless that metadata can be recovered, this should be deleted.
            """.replace(
                "\t", ""
            ).format(
                entry.path
            ),
            "CURRENTLY_RUNNING": """
                The verdict: This submission at path {} is currently being run.
                Don't delete it while it's running!
                If this is invalid, unlock SauronX first.
            """.replace(
                "\t", ""
            ).format(
                entry.path
            ),
            "HANDLED_BY_OTHER": """
                The verdict: Another process is handling path {}.
                If this is false, delete {} first.
            """.replace(
                "\t", ""
            ).format(
                entry.path, processing_file(entry.submission_hash)
            ),
            "BEING_INSERTED": Fore.GREEN
            + """
                The verdict: The data at path {} is currently being processed on Valinor.
                Leave this for now to be safe. You can delete this if you need the space.
            """.replace(
                "\t", ""
            ).format(
                entry.path
            ),
        }


class Entry:
    def __init__(self, path: str) -> None:
        self.coll = config.get_coll(path)
        self.path = path

        with open(pjoin(path, "submission_hash.txt")) as f:
            self.submission_hash = f.read()
        self.submission = self._submission()
        if self.submission is None:
            self.history = []
        else:
            self.history = list(self._history())
            self.best_status = self._best_status()
            self.plate_run = self._plate_run()

    def local_data_table(self) -> str:
        return show_table(
            headers=["stage", "file exists?"],
            rows=[
                ["snapshot timing info", "+" if self.capture_completed() else "<< failed! >>"],
                ["stimulus timing info", "+" if self.stimulus_completed() else "<< failed! >>"],
                ["video (hash)", self._checkmark(self.coll.avi_file() + ".sha256")],
            ],
            title="local storage",
        )

    def history_table(self) -> str:
        if self.is_invalid():
            return ""
        else:
            return show_table(
                headers=["status", "sauron", "run datetime"],
                rows=[[z.status, z.sauron.id, z.created] for z in self.history],
                title="full run history",
            )

    def pretty_basic_info(self) -> str:
        return "\n".join(
            (Fore.BLUE + key.ljust(16) + str(value) for key, value in self.basic_info().items())
        )

    def basic_info(self) -> Dict[str, str]:
        if self.is_invalid():
            dct = {"Path": self.path}
        else:
            dct = {
                "Path": self.path,
                "Experiment": self.submission.experiment.name,
                "Description": self.submission.description,
                "Length (s)": nice_time(self.submission.experiment.battery.length),
                "User": self.submission.user.username,
                "Best stage": self.best_status,
                "Run": str(self.plate_run.id if self.plate_run is not None else "-"),
            }
        return dct

    def verdict(self) -> Verdict:
        if self.is_running():
            return Verdict.CURRENTLY_RUNNING
        elif self.handled_by_other():
            return Verdict.HANDLED_BY_OTHER
        elif self.is_invalid():
            return Verdict.INVALID
        elif self.is_test():
            return Verdict.TEST
        elif self.is_ready():
            return Verdict.AVAILABLE
        elif self.failed_insert():
            return Verdict.FAILED_REMOTELY
        elif self.is_being_inserted():
            return Verdict.BEING_INSERTED
        elif self.is_on_valinor():
            return Verdict.IDLE_ON_VALINOR
        elif self.failed_encoding():
            return Verdict.FAILED_ENCODING
        elif self.recoverable_locally():
            return Verdict.FAILED_LOCALLY
        elif self.is_unrecoverable():
            return Verdict.UNRECOVERABLE
        else:
            warn_user("Unknown status!", "There's a bug in the code.", "Figure out what's wrong.")
            return Verdict.HANDLED_BY_OTHER

    ###########################################
    # These are all mutually exclusive statuses

    # junk statuses
    def is_invalid(self) -> bool:
        return self.submission is None

    def is_test(self) -> bool:
        return self.submission_hash == "_" * 12

    # post-upload statuses
    def is_ready(self) -> bool:
        return (
            self.best_status == "available" and self.plate_run is not None
        )  # the status wasn't set for some historical data

    def is_being_inserted(self) -> bool:
        return self.plate_run is not None and self.best_status in {
            "inserting",
            "inserting features",
            "inserting sensors",
        }

    def is_idle_on_valinor(self) -> bool:
        return self.plate_run is None and self.best_status == "uploaded"

    def failed_insert(self) -> bool:
        return self.best_status == "insert failed"

    # local
    def failed_encoding(self) -> bool:
        return (
            self.capture_completed()
            and self.stimulus_completed()
            and not self.is_on_valinor()
            and not self.encoding_completed()
        )

    def recoverable_locally(self) -> bool:
        return (
            self.capture_completed()
            and self.stimulus_completed()
            and not self.is_on_valinor()
            and self.encoding_completed()
        )

    def is_running(self) -> bool:
        return self.submission_hash in SauronxLock()

    def handled_by_other(self) -> bool:
        return pexists(processing_file(self.submission_hash))

    def is_unrecoverable(self) -> bool:
        return not self.capture_completed() or not self.stimulus_completed()

    ###########################################
    # These are are lower-level and not mutually exclusive

    def capture_completed(self) -> bool:
        return self.coll.snapshot_timing_exists()

    def encoding_completed(self) -> bool:
        return self.coll.avi_exists()

    def stimulus_completed(self) -> bool:
        return self.coll.stimulus_timing_exists()

    def is_on_valinor(self) -> bool:
        return self.best_status in {
            "uploaded",
            "inserting",
            "inserting features",
            "inserting sensors",
            "insert failed",
            "available",
        }

    ###########################################

    def _best_status(self) -> Optional[str]:
        in_order = [
            "starting",
            "capturing",
            "failed",
            "cancelled",
            "extracting",
            "compressing",
            "uploading",
            "uploaded",
            "inserting",
            "inserting features",
            "inserting sensors",
            "insert failed",
            "available",
        ]
        for check_status in reversed(in_order):
            if len([h.status for h in self.history if h.status == check_status]) > 0:
                return check_status

    def _submission(self):
        import valarpy.model as model

        return (
            model.Submissions.select(
                model.Submissions, model.Experiments, model.Users, model.Batteries
            )
            .join(model.Experiments)
            .join(model.Superprojects, JOIN.LEFT_OUTER)
            .switch(model.Experiments)
            .join(model.Batteries)
            .switch(model.Experiments)
            .join(model.TemplatePlates, JOIN.LEFT_OUTER)
            .join(model.PlateTypes, JOIN.LEFT_OUTER)
            .switch(model.Submissions)
            .join(model.Users, on=model.Submissions.user_id == model.Users.id)
            .where(model.Submissions.lookup_hash == self.submission_hash)
            .first()
        )

    def _plate_run(self):
        import valarpy.model as model

        return (
            model.Runs.select(model.Runs, model.Plates, model.Experiments)
            .join(model.Plates)
            .switch(model.Runs)
            .join(model.Experiments)
            .where(model.Runs.submission == self.submission.id)
            .first()
        )

    def _history(self):
        import valarpy.model as model

        return (
            model.SubmissionRecords.select(
                model.SubmissionRecords, model.Submissions, model.Users, model.Saurons
            )
            .join(model.Submissions)
            .join(model.Users, on=model.Submissions.user_id == model.Users.id)
            .switch(model.SubmissionRecords)
            .join(model.Saurons)
            .where(model.Submissions.lookup_hash == self.submission_hash)
            .order_by(model.SubmissionRecords.datetime_modified.desc())
        )

    def _checkmark(self, filename: str, success="+", fail: str = "") -> str:
        return success if pexists(pjoin(self.path, filename)) else fail


class DisplayOptions:
    def __init__(self, warnings: bool, local: bool, history: bool, verdict: bool) -> None:
        self.warnings = warnings
        self.local = local
        self.history = history
        self.verdict = verdict


class SearchRestrictions:
    def __init__(
        self,
        verdict: Optional[str] = None,
        status: Optional[str] = None,
        submission: Optional[str] = None,
        user: Optional[str] = None,
        experiment: Optional[str] = None,
        superproject: Optional[str] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
    ):
        self.verdict = verdict
        self.status = status
        self.submission = submission
        self.user = user
        self.experiment = experiment
        self.superproject = superproject
        self.before = None
        self.after = None  # TODO fix
        # self.before = dateparser.parse(before) if before is not None else None
        # self.after = dateparser.parse(after) if after is not None else None

    def matches(self, entry: Entry):
        return (
            (not entry.is_invalid())
            and (self.verdict is None or entry.verdict().name.lower() == self.verdict.lower())
            and (self.user is None or entry.submission.user.username.lower() == self.user.lower())
            and (
                self.experiment is None
                or entry.submission.experiment.name.lower() == self.experiment.lower()
            )
            and (
                self.superproject is None
                or entry.submission.superproject.name.lower() == self.superproject.lower()
            )
            and (self.submission is None or entry.submission_hash.startswith(self.submission))
            and (self.after is None or entry.submission.created >= self.after)
            and (self.before is None or entry.submission.created <= self.before)
            and (
                self.status is None
                or len([h for h in entry.history if h.status.lower() == self.status.lower()]) > 0
            )
        )


class DataManager:
    def __init__(self, db: Optional[Valar]) -> None:
        self.db = db

    def ls(self, base_dir: str) -> None:
        notify_user("Listing submissions under {}".format(base_dir))
        for d in self._ls(base_dir):
            print(Fore.BLUE + os.path.dirname(d))
        print("")

    def data(
        self, restrictions: SearchRestrictions, options: DisplayOptions, base_dir: str
    ) -> None:
        self._data(restrictions, options, base_dir)

    def auto_clean(
        self, restrictions: SearchRestrictions, options: DisplayOptions, base_dir: str
    ) -> None:
        if is_process_running():  # TODO this is broken on Windows
            warn_user("For safety, cannot auto-clean if another SauronX instance is running.")
            raise RefusingRequestException(
                "For safety, cannot auto-clean if another SauronX instance is running."
            )
        notify_user("Listing submissions under {}".format(base_dir))

        def accept(entry: Entry) -> None:
            recommendation = entry.verdict().recommendation()
            print(Fore.GREEN + "ACCEPTING RECOMMENDATION {}".format(recommendation.name))
            print(Fore.GREEN + "." * 100)
            recommendation.accept(entry.coll, self.db)

        self._data(restrictions, options, base_dir, accept)

    def clean(
        self,
        restrictions: SearchRestrictions,
        options: DisplayOptions,
        base_dir: str,
        skip_ignores: bool,
    ) -> None:
        print_to_user(
            [
                "You'll be prompted about all locally stored SauronX data under {}".format(
                    base_dir
                ),
                "You'll be asked first about any serious warnings, then what to do with the data.",
                "You can always choose to do nothing by pressing enter.",
            ],
            Fore.BLUE,
            top="_",
            bottom="",
        )
        if is_process_running():
            warn_user(
                "Another SauronX process appears to be running.",
                "As a precaution, make sure to leave any submission in-progress alone.",
            )
        for line in [
            Fore.GREEN + " Green signals that the data is available on Valinor.",
            Fore.BLACK + " Black means something is in progress.",
            Fore.CYAN + " Cyan indicates a warning or recoverable local failure.",
            Fore.RED + " Red signifies an error or serious warning.",
        ]:
            print(line)
        print(Fore.BLUE + "_" * 100)

        def ask(entry: Entry) -> None:
            entry.verdict().recommendation().ask(entry.coll, self.db, skip_ignores=skip_ignores)

        self._data(restrictions, options, base_dir, ask)
        notify_user(
            "Done listing SauronX output.",
            "If you need the storage immediately, remember to empty the trash.",
        )

    def obliterate(self, path) -> None:
        print(Fore.RED + "Obliterate ALL DATA under {}? [yes/no]".format(path), end="")
        if prompt_yes_no(""):
            n = 0
            for f in os.listdir(path):
                f = pjoin(path, f)
                slow_delete(f, 2)
                n += 1
                print("Deleted {}".format(f))
            print(Fore.RED + "Obliterated {} files or directories under {}".format(n, path))

    def _ls(self, base_dir: str) -> Iterator[str]:
        print("")
        lst = list(scan_for_files(base_dir))  # we modify the iterator by deleting files
        for f in lst:
            if f.endswith("submission_hash.txt"):
                yield os.path.dirname(f)

    def _data(
        self,
        restrictions: SearchRestrictions,
        options: DisplayOptions,
        base_dir: str,
        callback: Callable[[Entry], Any] = lambda s: None,
    ) -> None:
        for path in self._ls(base_dir):
            try:
                entry = Entry(path)
                if restrictions.matches(entry):
                    self._pretty_print(entry, options, callback)
            except LookupFailedException as e:
                self._pretty_error(path, e)

    def _pretty_print(
        self, entry: Entry, options: DisplayOptions, callback: Callable[[Entry], Any]
    ) -> None:
        print(Fore.BLUE + "~" * 100)
        print(entry.pretty_basic_info())
        if options.local:
            print(entry.local_data_table())
        if options.history and not entry.is_test():
            print(entry.history_table())
        if options.verdict:
            print(entry.verdict().message(entry))
        callback(entry)
        print(Fore.BLUE + "~" * 100)

    def _pretty_error(self, path: str, e: LookupFailedException) -> None:
        print(Fore.RED + "~" * 100)
        print(Fore.RED + e.message)
        print(Fore.RED + "~" * 100)


__all__ = ["DataManager", "SearchRestrictions", "DisplayOptions"]

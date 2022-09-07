from __future__ import annotations

import struct

from pocketutils.biochem.multiwell_plates import WB1
from pocketutils.core import *
from pocketutils.core.chars import *
from pocketutils.core.iterators import *
from pocketutils.full import Tools as _Tools
from typeddfs import TypedDfs

from sauronlab.core._imports import *
from sauronlab.core.valar_singleton import *


class IncompatibleNumpyArrayDataType(XTypeError):
    """ """


QueryFrame = TypedDfs.untyped("QueryFrame", doc="A DataFrame from a peewee query.")


I = TypeVar("I")
V = TypeVar("V")


class SauronlabValarTools:
    """"""

    @classmethod
    def query(cls, query: peewee.BaseQuery) -> QueryFrame:
        """
        Fetches on a peewee query, transforming the rows into a Pandas DataFrame.

        Note:

            Only the rows' own fields are included; does not include fields from joined tables.

        Examples:

            Getting all users::

                SauronlabValarTools.query(Users.select())

        """

        def get_data(row):
            return pd.Series(
                {
                    col: (value.hex() if isinstance(value, bytes) else value)
                    for col, value in row.get_data()
                }
            )

        return QueryFrame([get_data(row) for row in query])

    @classmethod
    def jvm_sbytes_to_ubytes(cls, data: bytes) -> np.array:
        """
        Used to convert "squashed" byte arrays from Valar into their true forms.
        Fundamentally these are unsigned bytes (0-255), but they were represented in Scala as signed bytes (-128 to 127) by subtracting 128.
        Then those bytes were inserted into MySQL blobs.
        To get them back, we read them into a signed byte Numpy array, cast to ints to avoid overflow, add 128, then convert to unsigned ints.

        Args:
            data: Bytes from Scala-inserted values in Valar blobs

        Returns:
            A Numpy ubyte (uint8) array

        """
        return (np.frombuffer(data, dtype=np.byte).astype(np.int32) + 128).astype(np.ubyte)

    @classmethod
    def signed_floats_to_blob(cls, data: np.array) -> bytes:
        """"""
        return SauronlabValarTools.array_to_blob(data, np.float32)

    @classmethod
    def blob_to_signed_floats(cls, data: bytes) -> np.array:
        """"""
        return np.copy(np.frombuffer(data, dtype=">f4"))

    @classmethod
    def blob_to_signed_ints(cls, data: bytes) -> np.array:
        """"""
        return np.copy(np.frombuffer(data, dtype=">i4"))

    @classmethod
    def array_to_blob(cls, data: np.array, dtype) -> bytes:
        """
        Gets the bytes of a Numpy array, first requiring that the array is of the specified type.

        Args:
            data: A numpy array
            dtype: A Numpy datatype, such as np.uint32

        Returns:
            The bytes representation

        Raises:
            IncompatibleNumpyArrayDataType: If the numpy array has the wrong data type
            TypeError: If ``data`` is not a Numpy array at all

        """
        if data.dtype != dtype:
            raise IncompatibleNumpyArrayDataType(f"Type {data.dtype} is not a {dtype}")
        return struct.pack(
            ">" + "f" * len(data), *data
        )  # For now, we are assuming data is 1D np.array. Change this once it's not.

    @classmethod
    def runs(cls, runs: RunsLike) -> Sequence[Runs]:
        """
        Fetches one or more runs from flexible formats.
        Currently performs one query on Valar per run. In the future will only perform one query for all of them.

        Args:
            runs: A run from a run ID, tag, name, instance, or submission hash or instance, or an iterable of any of these

        Returns:
            The Runs row instances in the same order

        """
        runs = runs if Tools.is_true_iterable(runs) else [runs]
        # make sure there aren't any weird types
        bad_types = [r for r in runs if not isinstance(r, (int, float, str, Runs, Submissions))]
        if len(bad_types) > 0:
            raise IncompatibleDataError(f"Invalid type for run or list or runs {bad_types}")
        # we'll build this up by setting individual indices
        blanks = [None for _ in runs]  # type: List[Optional[Runs]]
        # get by runs
        if any([b is None for b in blanks]):
            missing = [
                (i, r)
                for i, r in enumerate(runs)
                if blanks[i] is None
                and isinstance(
                    r,
                    (int, float, Runs)
                    or isinstance(r, str)
                    and not Tools.looks_like_submission_hash(r),
                )
            ]
            try:
                new = Runs.fetch_all_or_none([r for i, r in missing])
            except AssertionError:
                # TODO this shouldn't be raised
                raise LookupFailedError(f"At least one run is missing in {runs}") from None
            for i, n in Tools.zip_strict([i for i, r in missing], new):
                blanks[i] = n
        # get by submission objects
        if any([b is None for b in blanks]):
            missing = [
                (i, r)
                for i, r in enumerate(runs)
                if blanks[i] is None and isinstance(r, Submissions)
            ]
            new = {
                r.submission: r
                for r in Runs.select(Runs).where(Runs.submission_id << [s.id for i, s in missing])
            }
            for i, r in missing:
                blanks[i] = new.get(r)
        # get by submission hash
        if any([b is None for b in blanks]):
            missing = [
                (i, r) for i, r in enumerate(runs) if blanks[i] is None and isinstance(r, str)
            ]
            new = {
                r.submission.lookup_hash: r
                for r in Runs.select(Runs, Submissions)
                .join(Submissions)
                .where(Submissions.lookup_hash << [s for i, s in missing])
            }
            for i, r in missing:
                blanks[i] = new.get(r)
        # check that there are no missing items
        missing = {i: r for i, r in enumerate(runs) if blanks[i] is None}
        if len(missing) > 0:
            raise ValarLookupError(f"Didn't find {missing}")
        return blanks

    @classmethod
    def run_ids_unchecked(cls, runs: RunsLike) -> Sequence[int]:
        """
        Fetches runs and gets their IDs, but leaves any int as-is without querying.
        This function is therefore a tiny bit dangerous.
        """
        if not Tools.is_true_iterable(runs):
            runs = [runs]
        if all([isinstance(r, int) for r in runs]):
            return runs
        else:
            return [r.id for r in Tools.runs(runs)]

    @classmethod
    def run(cls, run: RunLike, join: bool = False) -> Runs:
        """
        Fetches a run from a flexible format.
        Fetches from Valar once. Use Tools.runs if you want to fetch multiple runs in a single query.

        Args:
            run: A run from a run ID, tag, name, instance, or submission hash or instance
            join: Join on experiments, submissions, sauron_configs, saurons, plates, and plate_types

        Returns:
            The Runs row instance

        """
        bq = lambda: (
            Runs.select(Runs, Submissions, Experiments, Plates, PlateTypes, Batteries)
            .join(Submissions, JOIN.LEFT_OUTER)
            .switch(Runs)
            .join(Experiments)
            .switch(Runs)
            .join(SauronConfigs)
            .join(Saurons)
            .switch(Runs)
            .join(Plates)
            .join(PlateTypes, JOIN.LEFT_OUTER)
            .switch(Experiments)
            .join(Batteries)
        )
        if isinstance(run, float):
            run = int(run)
        if (
            isinstance(run, Submissions)
            or isinstance(run, str)
            and SauronlabValarTools.looks_like_submission_hash(run)
        ):
            sub = Submissions.fetch_or_none(run)
            if sub is None:
                raise ValarLookupError(f"No run {run}")
            if join:
                return bq().where(Submissions.id == sub.id).first()
            else:
                return Runs.get(Runs.submission_id == sub.id)
        if isinstance(run, str) and run.isdigit():
            run = int(run)
        if join and isinstance(run, int):
            return bq().where(Runs.id == run).first()
        elif join and isinstance(run, Runs):
            return bq().where(Runs.id == run.id).first()
        elif join and isinstance(run, str):
            attempt = bq().where(Runs.name == run).first()
            if attempt is not None:
                return attempt
            attempt = bq().where(Runs.tag == run).first()
            if attempt is not None:
                return attempt
            raise ValarLookupError(f"No run {run}")
        return Runs.fetch(run)

    @classmethod
    def wb1_from_run(cls, run: RunLike) -> WB1:
        """
        Creates a 1-based multiwell plate corresponding to the given run.

        Args:
            run: A run ID, instance, name, tag, etc.

        Returns:
            A :class:``pocketutils.biochem.multiwell_plates.WB1``"""
        pt: PlateTypes = Tools.run(run, join=True).plate.plate_type
        return WB1(pt.n_rows, pt.n_columns)

    @classmethod
    def looks_like_submission_hash(cls, submission_hash: str) -> bool:
        """Returns whether the string could be a submission hash – is formatted correctly."""
        return (
            submission_hash == "_" * 12
            or regex.compile("[0-9a-f]{12}$", flags=regex.V1).match(submission_hash) is not None
        )


class Tools(_Tools, SauronlabValarTools):
    """ """

    @classmethod
    def prepped_file(cls, path: PathLike, exist_ok: bool = True) -> Path:
        """
        Returns a concrete :class:``pathlib.Path`` for a file that can be written to without issue.
        Uses :meth:``pocketutils.tools.path_tools.PathTools.prep_file`` to address permissions and
        directory creation. The directory will not be created on failure.

        Args:
            path: A string, :class:``pathlib.PurePath``, or :class:``os.PathLike``
            exist_ok: If ``False``, raises an error if the file already exists

        Raises:
            IOError: Specific subclasses under :class:``pocketutils.core.exceptions.PathError``, which in turn
                     subclasses :class:``IOError``; for example, from a permissions issue or because the path
                     exists but is not a file

        Returns:
            A concrete os-specific :class:``pathlib.Path``
        """
        cls.prep_file(path, exist_ok=exist_ok)
        return Path(path)

    @classmethod
    def prepped_dir(cls, path: PathLike, exist_ok: bool = True) -> Path:
        """
        Creates a directory and returns a concrete :class:``pathlib.Path``.
        Uses :meth:``pocketutils.tools.path_tools.PathTools.prep_file`` to avoid any issues.

        Args:
            path: A string, :class:``pathlib.PurePath``, or :class:``os.PathLike``
            exist_ok: If ``False``, raises an error if the file already exists;
                      passed directly into :meth:``pathlib.Path.mkdir``

        Returns:
            A concrete os-specific :class:``pathlib.Path``
        """
        cls.prep_dir(path, exist_ok=exist_ok)
        return Path(path)


__all__ = [
    "Tools",
    "Chars",
    "SizedIterator",
    "SeqIterator",
    "TieredIterator",
    "OptRow",
]

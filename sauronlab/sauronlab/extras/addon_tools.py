import ast
import shutil
import subprocess

from sauronlab.core._imports import *
from sauronlab.core._tools import *
from sauronlab.core.tools import *
from sauronlab.core.valar_singleton import *

I = TypeVar("I")
V = TypeVar("V")


class AddonTools:
    """
    Miscellaneous user-facing tools specific to the data we have in Valar.
    For example, uses our definition of a library plate ID.
    Some of these functions simply call their equivalent Tools or InternalTools functions.
    """

    @classmethod
    def download_file(cls, remote_path: PathLike, local_path: str, overwrite: bool = False) -> None:
        """
        Downloads a directory from a remote path.
        Tries, in order: shutil, rsync, scp.
        """
        remote_path = str(remote_path)
        try:
            return cls._download(remote_path, local_path, False, overwrite)
        except Exception:
            raise DownloadError(
                "Failed to download file {remote_path} to {local_path} with{'' if overwrite else 'out'} overwrite"
            )

    @classmethod
    def download_dir(cls, remote_path: PathLike, local_path: str, overwrite: bool = False) -> None:
        """
        Downloads a directory from a remote path.
        Tries, in order: shutil, rsync, scp.
        """
        try:
            remote_path = str(remote_path)
            return cls._download(remote_path, local_path, True, overwrite)
        except Exception:
            raise DownloadError(
                f"Failed to download dir {remote_path} to {local_path} with{'' if overwrite else 'out'} overwrite"
            )

    @classmethod
    def _download(cls, remote_path: str, path: PathLike, is_dir: bool, overwrite: bool) -> None:
        """
        Downloads via shutil or rsync, falling back to scp if rsync fails.
        """
        path = str(path)
        logger.debug(f"Downloading {remote_path} -> {path}")
        Tools.prep_file(path, exist_ok=overwrite)
        try:
            shutil.copyfile(remote_path, path)
            return
        except OSError:
            logger.error(f"Failed to copy {remote_path} to {path} using copyfile", exc_info=False)
            logger.debug(f"Copy failed.", exc_info=True)
        has_rsync = False
        try:
            subprocess.check_call(["rsync", "--version"])
            has_rsync = True
        except subprocess.SubprocessError:
            logger.debug("Did not find rsync", exc_info=True)
        if is_dir and has_rsync:
            subprocess.check_output(["rsync", "--ignore-existing", "-avz", remote_path, path])
        elif has_rsync:
            subprocess.check_output(
                [
                    "rsync",
                    "-t",
                    "--ignore-existing",
                    "--no-links",
                    '--exclude=".*"',
                    remote_path,
                    path,
                ]
            )
        else:
            subprocess.check_output(["scp", remote_path, path])

    @classmethod
    def generate_batch_hash(cls) -> str:
        """
        Generates a batch lookup_hash as an 8-digit lowercase alphanumeric string.
        """
        s = None
        # 41.36 bits with 1 million compounds has a 20% chance of a collision
        # that's ok because the chance for a single compound is very low, and we can always generate a new one
        while (
            s is None
            or Batches.select(Batches.lookup_hash).where(Batches.lookup_hash == s).first()
            is not None
        ):
            s = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))
        return s

    @classmethod
    def generate_submission_hash(cls) -> str:
        return "%012x" % (random.randrange(16**12))

    @classmethod
    def storage_path(cls, run: Union[int, str, Runs, Submissions], shire_path: str) -> PurePath:
        run = Tools.run(run)
        year = str(run.datetime_run.year).zfill(4)
        month = str(run.datetime_run.month).zfill(2)
        path = PurePath(shire_path, "store", year, month, str(run.tag))
        # TODO .replace('\\\\', '\\') ?
        # if path.startswith('\\'): path = '\\' + path
        return path

    @classmethod
    def parse_param_value(
        cls, submission: Union[Submissions, int, str], param_name: str
    ) -> Union[
        Sequence[np.int64],
        Sequence[np.float64],
        Sequence[Batches],
        Sequence[GeneticVariants],
        np.int64,
        np.float64,
        Batches,
        GeneticVariants,
        str,
        Sequence[str],
    ]:
        """
        Parses a submission value into strings, lists, ints, floats, batches, or genetic_variants.

        Args:
            submission: Submission Identifier
            param_name: Ex '$...drug'

        Returns:
            Submission Parameter value
        """
        submission = Submissions.fetch(submission)
        params = Tools.query(
            SubmissionParams.select().where(SubmissionParams.submission == submission)
        )
        if param_name not in params["name"].tolist():
            raise ValarLookupError(
                f"No submission param with name {param_name} for submission {submission.lookup_hash}"
            )
        # handle special case of library syntax
        row = params[params["name"] == param_name].iloc[0]
        if row.value.startswith("[/") and row.value.endswith("/]"):
            return row.value
        # otherwise convert by eval
        literal = ast.literal_eval(row.value)

        # util functions
        def oc_it(oc: str):
            return Batches.fetch(oc)

        def var_it(var: str):
            return GeneticVariants.fetch(var)

        # convert
        if row.param_type == "group" and isinstance(literal, str):
            return literal
        elif row.param_type == "replicate" and isinstance(literal, int):
            return np.int64(literal)
        elif row.param_type == "group" and isinstance(literal, list):
            return literal
        elif row.param_type == "compound" and isinstance(literal, str):
            return oc_it(literal)
        elif row.param_type == "compound" and isinstance(literal, list):
            return [oc_it(oc) for oc in literal]
        elif row.param_type == "variant" and isinstance(literal, str):
            return var_it(literal)
        elif row.param_type == "variant" and isinstance(literal, list):
            return [var_it(v) for v in literal]
        elif row.param_type == "dose" and isinstance(literal, list):
            return [np.float64(dose) for dose in literal]
        elif (row.param_type == "n_fish" or row.param_type == "dose") or (
            row.param_type == "dpf" and isinstance(literal, str)
        ):
            return np.float64(literal)
        elif (row.param_type == "n_fish" or row.param_type == "dpf") and isinstance(literal, list):
            return [np.int64(l) for l in literal]
        else:
            raise TypeError(
                f"This shouldn't happen: type {type(literal)} of param value {literal} not understood"
            )

    @classmethod
    def all_plates_ids_of_library(cls, ref: Union[Refs, int, str]) -> Set[str]:
        """
        Returns the batches.legacy_interal_id values, truncated to exclude the last two digits, of the batches under a library.
        For these batches, the legacy_internal_id values are the library name, followed by the plate number, followed by the well index (last 2 digits).
        This simply strips off the last two digits of legacy IDs that match the pattern described above. All legacy ids not following the pattern
        are excluded from the returned set.

        Args:
            ref: The library Refs table ID, name, or instance

        Returns:
            The unique library plate IDs, from the legacy_internal fields
        """
        ref = Refs.fetch(ref)
        s = set([])
        for o in Batches.select(Batches.legacy_internal, Batches.ref_id).where(
            Batches.ref_id == ref.id
        ):
            pat = regex.compile("""([A-Z]{2}[0-9]{5})[0-9]{2}""", flags=regex.V1)
            match = pat.fullmatch(o.legacy_internal)
            if match is not None:
                s.add(match.group(1))
        return s

    @classmethod
    def library_plate_id_of_submission(
        cls, submission: Union[Submissions, int, str], var_name: Optional[str] = None
    ) -> str:
        """
        Determines the library plate name from a submission.
        Uses a fair bit of logic to figure this out; peruse the code for more info.

        Args:
            submission: The submission ID, hash, or instance
            var_name: The submission_params variable name, often something like '$...drug'

        Returns:
            library plate id for new style submissions and truncated legacy_internal_id values for old style submissions.
        """
        submission = Submissions.fetch(submission)
        if var_name is None:
            var_name = Tools.only(
                {
                    p.name
                    for p in SubmissionParams.select().where(
                        SubmissionParams.submission == submission
                    )
                    if p.name.startswith("$...")
                },
                name="possible submission param names",
            )
        b = cls.parse_param_value(submission, var_name)
        if isinstance(b, str) and b.startswith("[/") and b.endswith("/]"):
            # new style where we keep the [/CB333/] format
            # and valar.params converts it
            return b[2:-2]
        if isinstance(b, list):
            # old style where the website converted the library into a list
            b = b[0]
            # ex: CB6158101
            pat = regex.compile("""([A-Z]{2}[0-9]{5})[0-9]{2}""", flags=regex.V1)
            match = pat.fullmatch(b.legacy_internal)
            if match is None:
                raise ValarLookupError(
                    f"Batch {b.lookup_hash} on submission {submission.lookup_hash} has an invalid legacy_internal_id {b.legacy_internal}"
                )
            return match.group(1)
        else:
            assert False, "Type {type(b)} of param {b} not understood"

    @classmethod
    def fetch_feature_slice(
        cls, well, feature: Features, start_frame: int, end_frame: int
    ) -> Optional[np.array]:
        """
        Quickly gets only a fraction of a time-dependent feature.

        Args:
            well: The well ID
            feature: The FeatureType to select
            start_frame: Starts at 0 as per our convention (note that MySQL itself starts at 1)
            end_frame: Starts at 0 as per our convention (note that MySQL itself starts at 1)
        """
        well = Wells.fetch(well)
        feature = Features.fetch(feature)
        sliced = fn.SUBSTR(
            WellFeatures.floats,
            start_frame + 1,
            feature.stride_in_bytes * (end_frame - start_frame),
        )
        blob = (
            WellFeatures.select(sliced.alias("sliced"))
            .where(WellFeatures.well_id == well.id)
            .first()
        )
        return None if blob is None else feature.from_blob(blob.sliced, well.id)


__all__ = ["AddonTools"]

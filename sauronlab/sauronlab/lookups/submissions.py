from sauronlab.core.core_imports import *
from sauronlab.lookups import *


@abcd.external
class SubmissionLookups(LookupTool):
    """
    Utilities for glancing at Valar's contents. Unlike "real" queries, these do not require a datetime filter.
    """

    @classmethod
    def tags(cls, wheres: Union[ExpressionsLike, RunTags] = None) -> Lookup:
        query = RunTags.select(RunTags, Runs).join(Runs)
        if isinstance(wheres, (int, str, Runs, Submissions)):
            wheres = Runs.id == Tools.run(wheres).id
        return SubmissionLookups._simple(
            RunTags,
            query,
            False,
            False,
            wheres,
            "id",
            ("run.id", "run.id"),
            ("run.name", "run.name"),
            "name",
            "value",
        )

    @classmethod
    def tag_summary(cls, wheres: Union[ExpressionsLike, RunTags] = None) -> Lookup:
        return (
            SubmissionLookups.tags(wheres)
            .drop("id", axis=1)
            .drop("run.id", axis=1)
            .drop("run.name", axis=1)
            .groupby("name")
            .count()
            .rename(columns={"value": "n_usages"})
        )

    @classmethod
    def params_on(cls, wheres: Union[ExpressionsLike, int, str, Submissions]) -> Lookup:
        wheres = InternalTools.flatten_smart(wheres)
        query = (
            SubmissionParams.select(SubmissionParams, Submissions, Experiments)
            .join(Submissions)
            .join(Experiments)
        )
        return SubmissionLookups._simple(
            Submissions,
            query,
            False,
            False,
            wheres,
            ("param_id", "id"),
            ("submission", "submission.lookup_hash"),
            "name",
            "value",
            "param_type",
            ("submission_created", "submission.created"),
        )


__all__ = ["SubmissionLookups"]

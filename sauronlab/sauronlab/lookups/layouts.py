from sauronlab.core.core_imports import *
from sauronlab.model.compound_names import *
from sauronlab.model.treatments import Treatment, Treatments
from sauronlab.model.well_names import *
from sauronlab.model.wf_builders import *


class Layout(UntypedDf):
    """ """

    pass


@abcd.auto_repr_str()
@abcd.external
class AbstractLayoutViewer:
    """ """

    def __call__(self, run: Union[int, str, Runs, Submissions]) -> pd.DataFrame:
        return self.of(run)

    @abcd.abstractmethod
    def of(self, run: Union[int, str, Runs]) -> pd.DataFrame:
        """


        Args:
            run:

        Returns:

        """
        raise NotImplementedError()

    def pivot(self, df: WellFrame, column: str) -> pd.DataFrame:
        """


        Args:
            df: WellFrame:
            column: str:

        Returns:

        """
        df = df.pivot("row", "column", column).reset_index()
        df["row"] = df["row"].map(lambda i: chr(64 + i))
        return df.set_index("row")


@abcd.auto_repr_str()
@abcd.external
class LayoutViewer(AbstractLayoutViewer):
    """ """

    def __init__(self, thing_name: str, function) -> None:
        self.thing_name = thing_name
        self._fn = function

    def __call__(self, run: Union[int, str, Runs, Submissions]) -> Layout:
        return self.of(run)

    def of(self, run: Union[int, str, Runs]) -> Layout:
        """


        Args:
            run:

        Returns:

        """
        df = WellFrameBuilder.runs(run).with_column(self.thing_name, self._fn).build()
        return Layout.convert(self.pivot(df, self.thing_name))


@abcd.auto_repr_str()
@abcd.external
class NamerLayoutViewer(AbstractLayoutViewer):
    """ """

    def __init__(self, namer: WellNamer, compound_namer: CompoundNamer) -> None:
        self.namer = namer
        self.compound_namer = compound_namer

    def of(self, run: Union[int, str, Runs]) -> pd.DataFrame:
        """


        Args:
            run:

        Returns:

        """
        df = (
            WellFrameBuilder.runs(run)
            .with_compound_names(self.compound_namer)
            .with_names(self.namer)
            .build()
        )
        return self.pivot(df, "name")


@abcd.auto_repr_str()
@abcd.external
class CompoundNamerLayoutViewer(AbstractLayoutViewer):
    """ """

    def __init__(self, namer: CompoundNamer) -> None:
        self.namer = namer

    def of(self, run: Union[int, str, Runs]) -> Layout:
        """


        Args:
            run:

        Returns:

        """
        df = WellFrameBuilder.runs(run).with_compound_names(self.namer).build()
        df = self.pivot(df, "compound_names")
        return Layout(df.applymap(lambda cnames: ", ".join(cnames)))


@abcd.external
class LayoutViewers:
    """ """

    treatments = LayoutViewer(
        "_treatments", lambda w, ts: str(Treatments([Treatment.from_well_treatment(t) for t in ts]))
    )
    batch_hashes = LayoutViewer(
        "_batch_hash",
        lambda w, ts: ", ".join(
            Tools.unique(
                [
                    str(Treatment.from_well_treatment(t).bhash[3:9])
                    for t in ts
                    if Treatment.from_well_treatment(t).bhash is not None
                ]
            )
        ),
    )
    batch_ids = LayoutViewer(
        "_batch_id",
        lambda w, ts: ", ".join(
            Tools.unique(
                [
                    str(Treatment.from_well_treatment(t).bid)
                    for t in ts
                    if Treatment.from_well_treatment(t).bid is not None
                ]
            )
        ),
    )
    batch_tags = LayoutViewer(
        "_batch_tag",
        lambda w, ts: ", ".join(
            Tools.unique(
                [
                    str(Treatment.from_well_treatment(t).btag)
                    for t in ts
                    if Treatment.from_well_treatment(t).btag is not None
                ]
            )
        ),
    )
    compound_ids = LayoutViewer(
        "_compound_id",
        lambda w, ts: ", ".join(
            Tools.unique(
                [
                    str(Treatment.from_well_treatment(t).cid)
                    for t in ts
                    if Treatment.from_well_treatment(t).bid is not None
                ]
            )
        ),
    )
    doses = LayoutViewer(
        "_dose",
        lambda w, ts: ", ".join(
            Tools.unique(
                [
                    str(Treatment.from_well_treatment(t).dose)
                    for t in ts
                    if Treatment.from_well_treatment(t).dose is not None
                ]
            )
        ),
    )
    doses_pretty = LayoutViewer(
        "_dose",
        lambda w, ts: ", ".join(
            Tools.unique(
                [
                    Tools.nice_dose(Treatment.from_well_treatment(t).dose)
                    for t in ts
                    if Treatment.from_well_treatment(t).dose is not None
                ]
            )
        ),
    )
    controls = LayoutViewer(
        "_control", lambda w, ts: w.control_type.name if w.control_type is not None else "-"
    )
    variants = LayoutViewer(
        "_variant", lambda w, ts: w.variant.name if w.variant is not None else "-"
    )
    variant_ids = LayoutViewer(
        "_variant", lambda w, ts: w.variant.id if w.variant is not None else "-"
    )
    n_fishes = LayoutViewer("_n_fish", lambda w, ts: w.n if w.n is not None else "-")
    ages = LayoutViewer("_age", lambda w, ts: w.age if w.age is not None else "-")
    groups = LayoutViewer("_group", lambda w, ts: w.well_group if w.well_group is not None else "-")

    @classmethod
    def name(
        cls,
        namer: WellNamer = WellNamers.elegant(),
        compound_namer: CompoundNamer = CompoundNamers.tiered_fallback(),
    ):
        """


        Args:
            namer:
            compound_namer:

        Returns:

        """
        return NamerLayoutViewer(namer, compound_namer)

    @classmethod
    def compound_names(cls, namer: CompoundNamer = CompoundNamers.tiered_fallback()):
        """


        Args:
            namer:

        Returns:

        """
        return CompoundNamerLayoutViewer(namer)


__all__ = ["LayoutViewers", "LayoutViewer"]

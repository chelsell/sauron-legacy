from __future__ import annotations

from matplotlib.axes import Axes
from matplotlib.figure import Figure

from sauronlab.core.core_imports import *
from sauronlab.model.compound_names import *
from sauronlab.viz.breakdown_plots import BreakdownBarPlotter, BreakdownPiePlotter


class MandosFrame(UntypedDf):
    """"""

    @classmethod
    def required_columns(cls) -> Sequence[str]:
        """"""
        return [
            "rule_id",
            "compound",
            "inchikey",
            "chembl_id",
            "object_id",
            "external_id",
            "target_name",
            "object_name",
            "predicate",
            "ref_id",
            "ref",
        ]

    @classmethod
    def reserved_columns(cls) -> Sequence[str]:
        """"""
        return [
            "rule_id",
            "compound",
            "inchikey",
            "chembl_id",
            "compound_name",
            "object_id",
            "external_id",
            "object_name",
            "predicate_id",
            "predicate",
            "ref_id",
            "ref",
        ]

    def bar(
        self, colors: Union[None, bool, Sequence[str]] = None, ax: Optional[Axes] = None
    ) -> Figure:
        """


        Args:
            colors: Union[None:
            ax:

        Returns:

        """
        counts = self.counts_by_object()
        labels = counts["object_name"].values
        values = counts["count"].values
        return BreakdownBarPlotter().plot(labels, values, colors, ax=ax)

    def pie(
        self, colors: Union[None, bool, Sequence[str]] = None, ax: Optional[Axes] = None
    ) -> Figure:
        """


        Args:
            colors:
            ax:

        Returns:

        """
        counts = self.counts_by_object()
        counts = UntypedDf(counts.iloc[::-1]).reset_index()  # reverse so we sort clockwise
        labels = counts["object_name"].values
        values = counts["count"].values
        return BreakdownPiePlotter().plot(labels, values, colors, ax=ax)

    def counts_by_object(self, multi_count: bool = False):
        """


        Args:
          multi_count: bool:  (Default value = False)

        Returns:

        """
        return self.counts_by_col("object_name", multi_count=multi_count)

    def counts_by_col(self, col: str, multi_count: bool = False) -> UntypedDf:
        """


        Args:
            col: str:
            multi_count: bool:  (Default value = False)

        Returns:

        """
        if multi_count:
            counts = (
                self.groupby(col)
                .count()[["rule_id"]]
                .reset_index()
                .rename(columns={"rule_id": "count"})
            )
        else:
            counts = (
                pd.DataFrame(self.groupby(col)["compound_id"].nunique())
                .reset_index()
                .rename(columns=dict(compound_id="count"))
            )
        counts["__sort"] = counts[col].str.lower()
        counts = UntypedDf(counts).sort_natural("__sort")
        return counts


class ChemInfoFrame(TypedDf):
    """ """

    @classmethod
    def required_columns(cls) -> Sequence[str]:
        """ """
        return ["compound", "name", "value", "ref"]


class GoTermFrame(TypedDf):
    """ """

    @classmethod
    def required_columns(cls) -> Sequence[str]:
        """ """
        return ["compound", "term"]


@abcd.auto_repr()
@abcd.auto_eq()
@abcd.auto_html()
class MandosSearch:
    """ """

    def __init__(self, kind: str, as_of: datetime):
        self.kind = kind
        self.wheres = []
        self.object_tags = []
        self.rule_tags = []
        self.namers = []
        self.as_of = as_of
        self._quiet = False
        self.batch_refs = None

    @classmethod
    def targets(cls, as_of: datetime) -> MandosSearch:
        """


        Args:
            as_of: datetime:

        Returns:

        """
        return MandosSearch("target", as_of)

    @classmethod
    def classes(cls, as_of: datetime) -> MandosSearch:
        """


        Args:
            as_of: datetime:

        Returns:

        """
        return MandosSearch("class", as_of)

    @classmethod
    def indications(cls, as_of: datetime) -> MandosSearch:
        """


        Args:
            as_of: datetime:

        Returns:

        """
        return MandosSearch("indication", as_of)

    def where(self, where) -> MandosSearch:
        """


        Args:
            where:

        Returns:

        """
        self.wheres.append(where)
        return self

    def with_object_tags(self, name: Optional[str]) -> MandosSearch:
        """


        Args:
            name: Optional[str]:

        Returns:

        """
        if name is None:
            self.object_tags = None
        else:
            if self.object_tags is None:
                raise ValueError("Object tags already set to None (all)")
            if isinstance(name, str):
                name = [name]
            for n in name:
                self.object_tags.append(n)
        return self

    def with_rule_tags(self, name: Optional[str]) -> MandosSearch:
        """


        Args:
            name: Optional[str]:

        Returns:

        """
        if name is None:
            self.rule_tags = None
        else:
            if self.object_tags is None:
                raise ValueError("Rule already set to None (all)")
            if isinstance(name, str):
                name = [name]
            for n in name:
                self.rule_tags.append(n)
        return self

    def with_compound_names(self, col_name=None, namer=None) -> MandosSearch:
        """


        Args:
            col_name:
            namer:

        Returns:

        """
        if col_name is None:
            col_name = "compound_name"
        if namer is None:
            namer = TieredCompoundNamer(TieredCompoundNamer.elegant_sources)
        self.namers.append((col_name, namer))
        return self

    def with_batches(self, refs: Set[Union[str, int, Refs]] = None) -> MandosSearch:
        """


        Args:
            refs:

        Returns:

        """
        if refs is None:
            self.batch_refs = {1, 3, 10}
        else:
            self.batch_refs = list(Refs.select())
        return self

    def search(self) -> MandosFrame:
        """ """
        query = (
            MandosRules.select(MandosRules, Compounds, MandosPredicates, MandosObjects)
            .join(Compounds, JOIN.LEFT_OUTER)
            .switch(MandosRules)
            .join(MandosObjects, JOIN.LEFT_OUTER)
            .switch(MandosRules)
            .join(Refs, JOIN.LEFT_OUTER)
            .switch(MandosRules)
            .join(MandosPredicates, JOIN.LEFT_OUTER)
        )
        if self.kind is not None:
            query = query.where(MandosPredicates.kind == self.kind)
        if self.as_of is not None:
            query = query.where(MandosRules.created < self.as_of)
        for where in self.wheres:
            query = query.where(where)
        query = list(query)
        logger.trace(f"Found {len(query)} annotations")
        df = pd.DataFrame(
            [
                pd.Series(
                    {
                        "rule_id": a.id,
                        "compound_id": a.compound.id,
                        "inchikey": a.compound.inchikey,
                        "chembl_id": a.compound.chembl,
                        "ref_id": a.ref.id,
                        "ref_name": a.ref.name,
                        "predicate_id": a.predicate.id,
                        "predicate_name": a.predicate.name.lower(),
                        "object_id": a.object.id,
                        "object_external_id": a.object.external,
                        "object_name": a.object.name,
                    }
                )
                for a in query
            ],
            columns=[
                "rule_id",
                "compound_id",
                "inchikey",
                "chembl_id",
                "object_id",
                "object_external_id",
                "object_name",
                "predicate_id",
                "predicate_name",
                "ref_id",
                "ref_name",
            ],
        )
        self._add_object_tags(df)
        self._add_rule_tags(df)
        self._add_batches(df)
        df = MandosFrame.convert(df)
        if "index" in df.columns:
            df = df.drop("index", axis=1)
        for col_name, namer in self.namers:
            df[col_name] = namer.map_to(df["compound_id"])
        return MandosFrame(df).cfirst(["rule_id", "compound_id"])

    def _add_batches(self, df: pd.DataFrame) -> None:
        """


        Args:
            df: pd.DataFrame:

        """
        if self.batch_refs is None:
            return
        cids = set(df["compound_id"])
        refs = Refs.fetch_all(self.batch_refs)
        lookup = defaultdict(lambda: [])
        for batch in (
            Batches.select(Batches.id, Batches.compound_id, Batches.ref)
            .where(Batches.compound_id << cids)
            .where(Batches.ref << refs)
        ):
            lookup[batch.compound_id].append(batch.id)
        for compound in cids:
            df["batch_ids"] = tuple(df["compound_id"].map(lambda target: lookup[compound]))

    def _add_object_tags(self, df: pd.DataFrame) -> None:
        """


        Args:
            df: pd.DataFrame:

        """
        objs = set(df["object_id"])
        tags = MandosObjectTags.select().where(MandosObjectTags.object_id << objs)
        tags = (
            list(tags)
            if self.object_tags is None
            else list(tags.where(MandosObjectTags.name << self.object_tags))
        )
        self._add_tags(df, tags, "object_id")

    def _add_rule_tags(self, df: pd.DataFrame) -> None:
        """


        Args:
            df: pd.DataFrame:

        """
        rules = set(df["rule_id"].unique())
        tags = MandosRuleTags.select().where(MandosRuleTags.rule_id << rules)
        tags = (
            list(tags)
            if self.rule_tags is None
            else list(tags.where(MandosRuleTags.name << self.rule_tags))
        )
        self._add_tags(df, tags, "rule_id")

    def _add_tags(self, df: pd.DataFrame, tags, name) -> None:
        """


        Args:
            df: pd.DataFrame:
            tags:
            name:

        """
        lookup = defaultdict(lambda: [])
        for tag in tags:
            lookup[(getattr(tag, name), tag.name)].append(tag.value)

        def fix(target):
            """


            Args:
              target:

            Returns:

            """
            ell = lookup.get((target, tag_name))
            return tuple([]) if ell is None else tuple(ell)

        for tag_name in [x[1] for x in lookup.keys()]:
            df[tag_name] = (
                df[name].map(fix).map(lambda s: None if s is None or len(s) == 0 else Tools.only(s))
            )


class MandosSearches:
    """ """

    @classmethod
    def info(cls, compounds: Union[Compounds, int, str]) -> ChemInfoFrame:
        """


        Args:
            compounds:

        Returns:

        """
        if isinstance(compounds, (Compounds, int, str)):
            compounds = [compounds]
        compounds = [Compounds.fetch(c) for c in compounds]
        # noinspection PyTypeChecker
        return ChemInfoFrame.convert(
            pd.DataFrame(
                [
                    pd.Series(
                        {
                            "compound": i.compound,
                            "name": i.name,
                            "value": i.value,
                            "ref": i.ref.name,
                        }
                    )
                    for i in MandosInfo.select(MandosInfo, Refs)
                    .join(Refs, JOIN.LEFT_OUTER)
                    .where(MandosInfo.compound_id << {c.id for c in compounds})
                ]
            )
        )

    @classmethod
    def targets(cls, compound: Union[Compounds, int, str], as_of: datetime) -> MandosFrame:
        """


        Args:
            compound:
            as_of: datetime:

        Returns:

        """
        compound = Compounds.fetch(compound)
        return MandosSearch.targets(as_of).where(MandosRules.compound == compound.id).search()

    @classmethod
    def classes(cls, compound: Union[Compounds, int, str], as_of: datetime) -> MandosFrame:
        """


        Args:
            compound:
            as_of: datetime:

        Returns:

        """
        compound = Compounds.fetch(compound)
        return MandosSearch.classes(as_of).where(MandosRules.compound == compound.id).search()

    @classmethod
    def indications(cls, compound: Union[Compounds, int, str], as_of: datetime) -> MandosFrame:
        """


        Args:
            compound:
            as_of: datetime:

        Returns:

        """
        compound = Compounds.fetch(compound)
        return MandosSearch.indications(as_of).where(MandosRules.compound == compound.id).search()

    @classmethod
    def go_terms(cls, compounds: Set[int]) -> GoTermFrame:
        """


        Args:
            compounds:

        Returns:

        """
        if isinstance(compounds, (Compounds, int, str)):
            compounds = [compounds]
        compounds = {Compounds.fetch(c).id for c in compounds}
        all_rules = MandosRules.select().where(MandosRules.compound_id << compounds)
        all_objects = {r.object_id for r in all_rules}
        all_tags = list(
            MandosObjectTags.select()
            .where(MandosObjectTags.object_id << all_objects)
            .where(MandosObjectTags.name == "GO function")
        )
        compounds_to_objects = {c: [] for c in compounds}
        for r in all_rules:
            compounds_to_objects[r.compound_id].append(r.object_id)
        objects_to_tags = {r.object_id: [] for r in all_rules}
        for t in all_tags:
            objects_to_tags[t.object_id].append(t.value)
        compounds_to_tags = {c: [] for c in compounds}
        for c, objects in compounds_to_objects.items():
            for o in objects:
                for tag in objects_to_tags[o]:
                    compounds_to_tags[c].append(tag)
        lst = []
        for c, tags in compounds_to_tags.items():
            for t in tags:
                lst.append(pd.Series({"compound": c, "term": t}))
        # noinspection PyTypeChecker
        return GoTermFrame.convert(pd.DataFrame(lst))


__all__ = ["MandosSearches", "MandosSearch", "MandosFrame", "ChemInfoFrame", "GoTermFrame"]

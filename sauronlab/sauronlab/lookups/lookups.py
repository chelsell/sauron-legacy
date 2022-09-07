from __future__ import annotations

from sauronlab.core.core_imports import *
from sauronlab.lookups import *
from sauronlab.model.compound_names import TieredCompoundNamer

look = Tools.look
_users = {u.id: u.username for u in Users.select()}
_compound_namer = TieredCompoundNamer(max_length=50)


@abcd.external
class Lookups(LookupTool):
    """Utilities for glancing at Valar's contents. Unlike "real" queries, these do not require a datetime filter."""

    @classmethod
    def annotations(
        cls,
        *wheres: Union[ExpressionsLike, int, str, Annotations],
        like: bool = False,
        regex: bool = False,
    ) -> Lookup:
        """


        Args:
            *wheres:
            like:
            regex:

        Returns:

        """
        query = (
            Annotations.select(
                Annotations,
                Runs,
                Wells,
                Users,
                Assays,
                Batteries,
                Experiments,
                Projects,
                SauronConfigs,
                Saurons,
                Submissions,
            )
            .join(Runs, JOIN.LEFT_OUTER)
            .join(Experiments, JOIN.LEFT_OUTER)
            .join(Projects, JOIN.LEFT_OUTER)
            .switch(Annotations)
            .join(Submissions, JOIN.LEFT_OUTER)
            .switch(Experiments)
            .join(Batteries, JOIN.LEFT_OUTER)
            .switch(Runs)
            .join(SauronConfigs, JOIN.LEFT_OUTER)
            .join(Saurons, JOIN.LEFT_OUTER)
            .switch(Annotations)
            .join(Wells, JOIN.LEFT_OUTER)
            .switch(Annotations)
            .join(Assays, JOIN.LEFT_OUTER)
            .switch(Annotations)
            .join(Users, JOIN.LEFT_OUTER)
        )
        return Lookups._simple(
            Annotations,
            query,
            like,
            regex,
            wheres,
            "id",
            ("submission", "submission.lookup_hash"),
            ("run", "run.name"),
            ("well", "well.id"),
            ("assay", "assay.id"),
            "level",
            "name",
            "description",
            "value",
            ("annotator", "annotator.username"),
            ("when_run", "run.datetime_run"),
            ("experiment", "run.experiment.id"),
            ("when_added", "created"),
        )

    @classmethod
    def batch_annotations(
        cls,
        *wheres: Union[ExpressionsLike, BatchAnnotations],
        like: bool = False,
        regex: bool = False,
    ) -> Lookup:
        """


        Args:
            *wheres:
            like:
            regex:

        Returns:

        """
        query = (
            BatchAnnotations.select(BatchAnnotations, Batches, Users)
            .join(Batches)
            .switch(BatchAnnotations)
            .join(Users)
        )
        return Lookups._simple(
            Annotations,
            query,
            like,
            regex,
            wheres,
            "id",
            ("batch", "batch.lookup_hash"),
            ("compound", "batch.compound_id"),
            "level",
            "name",
            "description",
            ("annotator", "annotator.username"),
            ("when_added", "created"),
        )

    @classmethod
    def submissions(
        cls,
        *wheres: Union[ExpressionsLike, SubmissionLike],
        like: bool = False,
        regex: bool = False,
    ) -> Lookup:
        """


        Args:
            *wheres:
            like:
            regex:

        Returns:

        """
        query = (
            Submissions.select(Submissions, Experiments, Users, Batteries, TemplatePlates)
            .join(Experiments, JOIN.LEFT_OUTER)
            .join(Projects, JOIN.LEFT_OUTER)
            .switch(Experiments)
            .join(Batteries, JOIN.LEFT_OUTER)
            .switch(Experiments)
            .join(TemplatePlates, JOIN.LEFT_OUTER)
            .switch(Submissions)
            .join(Users, on=Submissions.user_id)
            .switch(Submissions)
            .join(Runs, JOIN.LEFT_OUTER)
        )
        return (
            LookupBuilder(Submissions)
            .set_query(query)
            .like_regex(like, regex)
            .add_all(
                "id",
                ("lookup_hash", "lookup_hash"),
                ("exp", "experiment.name"),
                "description",
                ("battery", "experiment.battery.name"),
                ("length", "experiment.battery.length"),
                ("template_plate", "experiment.template_plate.name"),
                ("user_dosed", "user.username"),
                ("user_plated", "person_plated.username"),
                ("when_dosed", "datetime_dosed"),
                ("when_plated", "datetime_plated"),
                ("continuing_sub", "continuing.lookup_hash"),
                ("run", "runs_set", lambda rs: rs[0].id if len(rs) > 0 else None),
                ("when_run", "runs_set", lambda rs: rs[0].datetime_run if len(rs) > 0 else None),
                ("when_inserted", "created"),
                (
                    "when_run_inserted",
                    "runs_set",
                    lambda rs: rs[0].created if len(rs) > 0 else None,
                ),
            )
            .query(wheres)
        )

    @classmethod
    def plates(cls, *wheres: Union[Plates, int, ExpressionsLike]):
        """


        Args:
            *wheres:

        Returns:

        """
        query = Plates.select(Plates, PlateTypes, Users).join(PlateTypes).switch(Plates).join(Users)
        return Lookups._simple(
            Plates,
            query,
            False,
            False,
            wheres,
            "id",
            "name",
            "datetime_plated",
            ("person_plated", "person_plated.username"),
            ("plate_type", "plate_type.name"),
        )

    @classmethod
    def runs(
        cls, *wheres: Union[RunsLike, ExpressionsLike], like: bool = False, regex: bool = False
    ) -> Lookup:
        """


        Args:
            *wheres:
            like:
            regex:

        Returns:

        """
        wheres = InternalTools.flatten_smart(wheres)
        if all(isinstance(w, (int, Runs, str, Submissions)) for w in wheres):
            wheres = [Runs.id << [r.id for r in Tools.runs(wheres)]]

        def uses(*any_of):
            """


            Args:
                *any_of:

            Returns:

            """
            return Lookups._expressions_use(wheres, any_of)

        uses_assays = uses(AssayPositions, Assays)
        uses_treatments = uses(WellTreatments, Batches, Compounds)
        uses_wells = uses(WellTreatments, Batches, Compounds, Wells, ControlTypes, GeneticVariants)
        uses_batches = uses(Batches, Compounds)
        uses_compounds = uses(Compounds)
        uses_settings = uses(SauronSettings)
        if uses_settings:
            sq = SauronSettings.select(SauronSettings, SauronConfigs).join(SauronConfigs)
            for q in Lookups._expressions_using(wheres, SauronSettings):
                sq = sq.where(q)
            valid_configs = {s.sauron_config.id for s in sq}
            wheres = Lookups._expressions_not_using(wheres, SauronSettings)
            wheres.append(SauronConfigs.id << valid_configs)
        if uses_treatments:
            query = Lookups._runs_hard(
                with_assays=uses_assays, with_batches=uses_batches, with_compounds=uses_compounds
            )
            base_attr = "well.run"
        elif uses_wells:
            query = Lookups._runs_simple(with_assays=uses_assays)
            base_attr = "run"
        else:
            query = Lookups._runs_simplest(with_assays=uses_assays)
            base_attr = None
        return (
            LookupBuilder(Runs)
            .set_query(query)
            .like_regex(like, regex)
            .set_base_attribute(base_attr)
            .add_all(
                "id",
                "name",
                "tag",
                ("submission", "submission.lookup_hash"),
                "description",
                ("plate", "plate.id"),
                ("user_run", "experimentalist.username"),
                ("when_run", "datetime_run"),
                ("when_dosed", "datetime_dosed"),
                ("when_plated", "plate.datetime_plated"),
                (
                    "acc_sec",
                    "",
                    lambda r: None
                    if r.acclimation_sec is None
                    else timedelta(seconds=r.acclimation_sec),
                ),
                ("dose_sec", "", lambda r: ValarTools.treatment_sec(r)),
                ("inc_sec", "", lambda r: ValarTools.wait_sec(r)),
                ("config", "sauron_config.id"),
                ("sauron", "sauron_config.sauron.name"),
                ("exp", "experiment.name"),
                ("project", "experiment.project.id"),
                ("battery", "experiment.battery.name"),
                ("length", "experiment.battery.length"),
                ("fps", "", ValarTools.frames_per_second),
                ("generation", "", lambda r: ValarTools.generation_of(r).name.lower()),
                ("when_inserted", "created"),
            )
            .query(wheres)
        )
        # ('when_cmd_run', '', lambda r: ValarTools.run_tag_optional(r, 'datetime_command_entered')),
        # ('sauronx_vr', '', lambda r: ValarTools.run_tag_optional(r, 'sauronx_version')),
        # ('user_plated', 'plate.person_plated.username'),

    @classmethod
    def _runs_simplest(cls, with_assays: bool) -> ExpressionLike:
        """


        Args:
            with_assays: bool:

        Returns:

        """
        query = (
            Runs.select(
                Runs,
                Plates,
                Experiments,
                Projects,
                SauronConfigs,
                Saurons,
                PlateTypes,
                TemplatePlates,
                Users,
            )
            .join(Plates)
            .switch(Runs)
            .join(Experiments)
            .join(Projects, JOIN.LEFT_OUTER)
            .switch(Runs)
            .join(SauronConfigs, JOIN.LEFT_OUTER)
            .join(Saurons)
            .switch(Plates)
            .join(PlateTypes, JOIN.LEFT_OUTER)
            .switch(Runs)
            .join(Users, JOIN.LEFT_OUTER)
            .switch(Experiments)
            .join(Batteries, JOIN.LEFT_OUTER)
            .switch(Experiments)
            .join(TemplatePlates, JOIN.LEFT_OUTER)
        )
        if with_assays:
            query = query.switch(Batteries).join(AssayPositions, JOIN.RIGHT_OUTER).join(Assays)
        return query

    @classmethod
    def _runs_simple(cls, with_assays: bool) -> peewee.Query:
        """


        Args:
            with_assays: bool:

        Returns:

        """
        query = (
            Wells.select(
                Wells,
                ControlTypes,
                GeneticVariants,
                Runs,
                Plates,
                Experiments,
                Projects,
                SauronConfigs,
                Saurons,
                PlateTypes,
                TemplatePlates,
                Users,
            )
            .join(ControlTypes, JOIN.LEFT_OUTER)
            .switch(Wells)
            .join(GeneticVariants, JOIN.LEFT_OUTER)
            .switch(Wells)
            .join(Runs)
            .join(Plates)
            .switch(Runs)
            .join(Experiments)
            .join(Projects, JOIN.LEFT_OUTER)
            .switch(Runs)
            .join(SauronConfigs, JOIN.LEFT_OUTER)
            .join(Saurons)
            .switch(Plates)
            .join(PlateTypes, JOIN.LEFT_OUTER)
            .switch(Runs)
            .join(Users, JOIN.LEFT_OUTER)
            .switch(Experiments)
            .join(Batteries, JOIN.LEFT_OUTER)
            .switch(Experiments)
            .join(TemplatePlates, JOIN.LEFT_OUTER)
        )
        if with_assays:
            # TODO does this right outer join lose some runs?
            query = query.switch(Batteries).join(AssayPositions, JOIN.RIGHT_OUTER).join(Assays)
        return query

    @classmethod
    def _runs_hard(
        cls, with_assays: bool, with_batches: bool, with_compounds: bool
    ) -> peewee.Query:
        """


        Args:
            with_assays: bool:
            with_batches: bool:
            with_compounds: bool:

        Returns:

        """
        tables = [
            WellTreatments,
            Wells,
            ControlTypes,
            GeneticVariants,
            Runs,
            Plates,
            Experiments,
            Projects,
            SauronConfigs,
            Saurons,
            PlateTypes,
            TemplatePlates,
            Users,
        ]
        joiners = []
        if with_compounds:
            tables.extend([Batches, Compounds])
            joiners.append(
                lambda q: q.switch(WellTreatments).join(Batches).join(Compounds, JOIN.LEFT_OUTER)
            )
        elif with_batches:
            tables.append(Batches)
            joiners.append(lambda q: q.switch(WellTreatments).join(Batches))
        if with_assays:
            tables.extend([AssayPositions, Assays])
            joiners.append(
                lambda q: q.switch(Batteries).join(AssayPositions, JOIN.RIGHT_OUTER).join(Assays)
            )

        query = WellTreatments.select(*tables)
        query = (
            query.join(Wells, JOIN.RIGHT_OUTER)
            .join(Runs)
            .join(Plates)
            .switch(Wells)
            .join(ControlTypes, JOIN.LEFT_OUTER)
            .switch(Wells)
            .join(GeneticVariants, JOIN.LEFT_OUTER)
            .switch(Runs)
            .join(Experiments)
            .join(Projects, JOIN.LEFT_OUTER)
            .switch(Runs)
            .join(SauronConfigs, JOIN.LEFT_OUTER)
            .join(Saurons)
            .switch(Plates)
            .join(PlateTypes, JOIN.LEFT_OUTER)
            .switch(Runs)
            .join(Users, JOIN.LEFT_OUTER)
            .switch(Experiments)
            .join(Batteries, JOIN.LEFT_OUTER)
            .switch(Experiments)
            .join(TemplatePlates, JOIN.LEFT_OUTER)
        )
        for joiner in joiners:
            query = joiner(query)
        return query

    @classmethod
    def wells(
        cls, *wheres: Union[ExpressionsLike, int, Wells], like: bool = False, regex: bool = False
    ) -> Lookup:
        """


        Args:
            *wheres:
            like:
            regex:

        Returns:

        """
        query = (
            Wells.select(Wells, Runs, Plates, PlateTypes).join(Runs).join(Plates).join(PlateTypes)
        )
        df = Lookups._simple(
            Annotations,
            query,
            like,
            regex,
            wheres,
            "id",
            ("position", "well_index"),
            "run",
            ("name", "run.name"),
            ("plate", "run.plate"),
            ("plate_type", "run.plate.plate_type"),
            ("when_run", "run.datetime_run"),
        )

        def label(row):
            pt = PlateTypes.fetch(row.plate_type)
            return WB1(pt.n_rows, pt.n_columns).index_to_label(row.position)

        df["label"] = df.apply(label, axis=1)
        return Lookup(df)

    @classmethod
    def projects(
        cls,
        *wheres: Union[None, Projects, str, int, ExpressionsLike],
        like: bool = False,
        regex: bool = False,
    ) -> Lookup:
        """


        Args:
            *wheres:
            like:
            regex:

        Returns:

        """
        query = (
            Projects.select(Projects, ProjectTypes, Users, Experiments, Batteries, TemplatePlates)
            .join(ProjectTypes, JOIN.LEFT_OUTER)
            .switch(Projects)
            .join(Experiments, JOIN.LEFT_OUTER)
            .switch(Projects)
            .join(Users, JOIN.LEFT_OUTER)
            .switch(Experiments)
            .join(Batteries, JOIN.LEFT_OUTER)
            .switch(Experiments)
            .join(TemplatePlates, JOIN.LEFT_OUTER)
        )
        return (
            LookupBuilder(Projects)
            .set_query(query)
            .like_regex(like, regex)
            .add_all(
                "id",
                "name",
                "description",
                ("creator", "creator.username"),
                ("active", "active", bool),
                ("when_inserted", "created"),
            )
            .query(wheres)
        )

    @classmethod
    def experiments(
        cls,
        *wheres: Union[None, Experiments, str, int, ExpressionsLike],
        like: bool = False,
        regex: bool = False,
    ) -> Lookup:
        query = (
            Experiments.select(
                Runs,
                Experiments,
                Projects,
                ProjectTypes,
                SauronConfigs,
                Saurons,
                Batteries,
                TemplatePlates,
                TransferPlates,
                Users,
            )
            .join(Runs, JOIN.LEFT_OUTER)
            .switch(Experiments)
            .join(Projects, JOIN.LEFT_OUTER)
            .join(ProjectTypes, JOIN.LEFT_OUTER)
            .switch(Runs)
            .join(SauronConfigs, JOIN.LEFT_OUTER)
            .join(Saurons, JOIN.LEFT_OUTER)
            .switch(Runs)
            .join(Submissions, JOIN.LEFT_OUTER)
            .switch(Experiments)
            .join(Batteries, JOIN.LEFT_OUTER)
            .switch(Experiments)
            .join(Users, JOIN.LEFT_OUTER)
            .switch(Experiments)
            .join(TemplatePlates, JOIN.LEFT_OUTER)
            .switch(Experiments)
            .join(TransferPlates, JOIN.LEFT_OUTER)
        )
        df = (
            LookupBuilder(Experiments)
            .set_query(query)
            .like_regex(like, regex)
            .add_all(
                "id",
                "name",
                "description",
                ("creator", "creator.username"),
                ("active", "active", bool),
                ("project", "project.name"),
                ("project_id", "project.id"),
                ("battery", "battery.name"),
                ("template_plate", "template_plate.name"),
                ("transfer_plate", "transfer_plate.name"),
                ("when_inserted", "created"),
            )
            .query(wheres)
        )
        runs = (
            Runs.select(Runs, SauronConfigs, Saurons)
            .join(SauronConfigs)
            .join(Saurons)
            .where(Runs.experiment << df["id"].unique().tolist())
            .order_by(Runs.datetime_run)
        )
        runs = Tools.multidict(runs, "experiment_id")

        def n_runs(e):
            return len(runs[e])

        def first_run(e):
            return Tools.first(
                sorted(
                    (
                        r.datetime_run if r.datetime_run is not None else datetime(5000, 1, 1)
                        for r in runs[e]
                    )
                )
            )

        def last_run(e):
            return Tools.first(
                reversed(
                    sorted(
                        (
                            r.datetime_run if r.datetime_run is not None else datetime(5000, 1, 1)
                            for r in runs[e]
                        )
                    )
                )
            )

        def generations(e):
            return frozenset((ValarTools.generation_of(r) for r in runs[e]))

        def saurons(e):
            return frozenset((ValarTools.sauron_name(r.sauron_config.sauron) for r in runs[e]))

        def sauron_configs(e):
            return frozenset((ValarTools.sauron_config_name(r.sauron_config) for r in runs[e]))

        if len(df) > 0:  # TODO shouldn't be needed
            df["n_runs"] = df["id"].map(n_runs)
            df["first_run"] = df["id"].map(first_run)
            df["last_run"] = df["id"].map(last_run)
            df["generations"] = df["id"].map(generations)
            df["saurons"] = df["id"].map(saurons)
            df["configs"] = df["id"].map(sauron_configs)
        return Lookup(df)

    @classmethod
    def compound_search(cls, *names: Union[Sequence[str], str], **where) -> Lookup:
        """
        Search for compounds matching names.

        Args:
            *names: Names to search for in CompoundLabels
            **where: kwargs with a key of EITHER 'where' or 'wheres', which are lists of additional expressions

        Returns:

        """
        where = where.get("where", where.get("wheres"))
        names = InternalTools.flatten_smart(names)
        wheres = CompoundLabels.name << names
        if where is not None and Tools.is_true_iterable(where):
            wheres.extend(where)
        elif where is not None:
            wheres.append(where)
        return Lookups.compounds(wheres)

    @classmethod
    def compounds(
        cls, *wheres: Union[CompoundLike, ExpressionsLike], like: bool = False, regex: bool = False
    ) -> Lookup:
        """


        Args:
            *wheres:
            like:
            regex:

        Returns:

        """
        uses_compound_labels = LookupTool._expressions_use(wheres, [CompoundLabels])
        uses_batches = LookupTool._expressions_use(wheres, [Batches])
        if uses_compound_labels:
            query = Compounds.select(
                Compounds.id,
                Compounds.inchikey,
                Compounds.chembl,
                CompoundLabels,
            ).join(CompoundLabels, JOIN.LEFT_OUTER)
        else:
            query = Compounds.select(Compounds.id, Compounds.inchikey, Compounds.chembl)
        df = (
            LookupBuilder(Compounds)
            .set_query(query)
            .like_regex(like, regex)
            .add_all(
                "id",
                "inchikey",
                "description",
                ("chembl_id", "chembl"),
                ("when_inserted", "created"),
            )
            .query(wheres)
        )
        return Lookups._add_names(df, "id")

    @classmethod
    def batch_search(cls, *names: Union[Sequence[str], str], **where) -> Lookup:
        """
        Search for batches matching names.

        Args:
            *names: Names to search for in CompoundLabels and BatchLabels
            **where: kwargs with a key of EITHER 'where' or 'wheres', which are lists of additional expressions

        Returns:

        """
        where = where.get("where", where.get("wheres"))
        names = InternalTools.flatten_smart(names)
        wheres = [(CompoundLabels.name << names) | (BatchLabels.name << names)]
        if where is not None and Tools.is_true_iterable(where):
            wheres.extend(where)
        elif where is not None:
            wheres.append(where)
        return Lookups.batches(wheres)

    @classmethod
    def batches(
        cls, *wheres: Union[BatchLike, ExpressionsLike], like: bool = False, regex: bool = False
    ) -> Lookup:
        """


        Args:
            *wheres:
            like:
            regex:

        Returns:

        """
        uses_batch_labels = Lookups._expressions_use(wheres, [BatchLabels])
        uses_compound_labels = Lookups._expressions_use(wheres, [CompoundLabels])
        DryStocks = Batches.alias()
        tables = [
            Batches,
            Compounds.id,
            Compounds.inchikey,
            Compounds.chembl,
            Refs,
            Suppliers,
            Users.id,
            Users.username,
            Users.write_access,
            Users.first_name,
            Users.last_name,
            DryStocks,
        ]
        if uses_batch_labels:
            tables.append(BatchLabels)
        if uses_compound_labels:
            tables.append(CompoundLabels)
        query = (
            Batches.select(*tables)
            .join(Compounds, JOIN.LEFT_OUTER, on=Batches.compound_id == Compounds.id)
            .join(CompoundLabels, JOIN.LEFT_OUTER)
            .switch(Batches)
            .join(Suppliers, JOIN.LEFT_OUTER)
            .switch(Batches)
            .join(Refs, JOIN.LEFT_OUTER)
            .switch(Batches)
            .join(DryStocks, JOIN.LEFT_OUTER, on=Batches.made_from_id == DryStocks.id)
            .switch(Batches)
            .join(Locations, JOIN.LEFT_OUTER)
            .switch(Batches)
            .join(BatchLabels, JOIN.LEFT_OUTER)
            .switch(Batches)
            .join(Users, JOIN.LEFT_OUTER)
        )
        if uses_batch_labels:
            query = query.switch(Batches).join(BatchLabels, JOIN.LEFT_OUTER)
        if uses_compound_labels:
            query = query.switch(Compounds).join(CompoundLabels, JOIN.LEFT_OUTER)
        solvents = ValarTools.known_solvent_names()
        locations = {ell.id: ell.name for ell in Locations.select()}
        df = (
            LookupBuilder(Batches)
            .set_query(query)
            .like_regex(like, regex)
            .add_all(
                "id",
                "lookup_hash",
                "tag",
                ("cid", "compound.id"),
                ("inchikey", "compound.inchikey"),
                ("chembl_id", "compound.chembl"),
                (
                    "dry_stock",
                    "made_from",
                    lambda b: None
                    if b is None
                    else "b{} ({})".format(
                        b.id, locations[b.location_id] if b.location_id is not None else "-"
                    ),
                ),
                ("supplier", "supplier.name"),
                ("ref", "ref.name"),
                ("location", "location.name"),
                "amount",
                ("legacy_id", "legacy_internal"),
                ("conc", "concentration_millimolar"),
                (
                    "solvent",
                    "solvent",
                    lambda s: None
                    if s is None
                    else (solvents[s] if s in solvents else "c" + str(s)),
                ),
                ("weight", "molecular_weight"),
                ("catalog_no", "supplier_catalog_number"),
                ("user", "user_ordered.username"),
                ("date", "date_ordered"),
            )
            .query(wheres)
        )
        concerns = Tools.multidict(
            BatchAnnotations.select().where(BatchAnnotations.batch << set(df["id"])), "batch_id"
        )
        df["concerns"] = df["id"].map(
            lambda b: ", ".join({"{} ({})".format(x.level, x.id) for x in concerns[b]})
            if b in concerns
            else None
        )
        return Lookups._add_names(df, "cid")

    @classmethod
    def compound_labels_of(
        cls,
        compounds: Union[CompoundLike, Iterable[CompoundLike]],
        like: bool = False,
        regex: bool = False,
    ) -> Lookup:
        """


        Args:
            compounds:
            like:
            regex:

        Returns:

        """
        if isinstance(compounds, (Compounds, str, int)):
            compounds = [compounds]
        compounds = [Compounds.fetch(c) for c in compounds]
        wheres = Compounds.id << compounds
        query = (
            CompoundLabels.select(CompoundLabels, Compounds, Refs)
            .join(Refs)
            .switch(CompoundLabels)
            .join(Compounds)
        )
        return (
            LookupBuilder(Compounds)
            .set_query(query)
            .like_regex(like, regex)
            .add_all(
                "id",
                "name",
                ("ref_id", "ref.id"),
                ("ref_name", "ref.name"),
                ("compound", "compound.id"),
                ("inchikey", "compound.inchikey"),
                "created",
            )
            .query(wheres)
        )

    @classmethod
    def transfer_plates(
        cls,
        *wheres: Union[ExpressionsLike, int, str, TransferPlates],
        like: bool = False,
        regex: bool = False,
    ) -> Lookup:
        """


        Args:
            *wheres:
            like:
            regex:

        Returns:

        """
        # noinspection PyPep8Naming
        Parents = TransferPlates.alias()
        query = (
            TransferPlates.select(TransferPlates, Users, PlateTypes, Suppliers)
            .join(Suppliers, JOIN.LEFT_OUTER)
            .switch(TransferPlates)
            .join(Users, JOIN.LEFT_OUTER)
            .switch(TransferPlates)
            .join(Parents, JOIN.LEFT_OUTER, on=(TransferPlates.parent_id == Parents.id))
            .switch(TransferPlates)
            .join(PlateTypes, JOIN.LEFT_OUTER)
        )
        return Lookups._simple(
            TransferPlates,
            query,
            like,
            regex,
            wheres,
            "id",
            "name",
            ("description", "description", Tools.truncate),
            ("plate_type", "plate_type.name"),
            ("parent", "parent.name"),
            ("supplier", "supplier.name"),
            ("creator", "creator.username"),
            ("diluted_by", "dilution_factor_from_parent"),
            ("initial_ul_per_well", "initial_ul_per_well"),
            ("when_created", "datetime_created"),
            ("when_inserted", "created"),
        )

    @classmethod
    def users(
        cls,
        *wheres: Union[ExpressionsLike, int, str, Users],
        like: bool = False,
        regex: bool = False,
    ) -> Lookup:
        """


        Args:
            *wheres:
            like:
            regex:

        Returns:

        """
        query = Users.select()
        return Lookups._simple(
            Users,
            query,
            like,
            regex,
            wheres,
            "id",
            "username",
            "first_name",
            "last_name",
            "write_access",
            ("has_password", "bcrypt_hash", lambda b: b is not None),
            "created",
        )

    @classmethod
    def project_types(
        cls,
        *wheres: Union[ExpressionsLike, int, str, ProjectTypes],
        like: bool = False,
        regex: bool = False,
    ) -> Lookup:
        """


        Args:
            *wheres:
            like:
            regex:

        Returns:

        """
        query = ProjectTypes.select()
        df = Lookups._simple(
            ProjectTypes,
            query,
            like,
            regex,
            wheres,
            "id",
            "name",
            "description",
        )
        projects = Tools.multidict(
            Projects.select().where(Projects.id << df["id"].unique().tolist()), "project_type"
        )

        def n_projects(pt):
            """


            Args:
              pt:

            Returns:

            """
            return len(projects[pt])

        if len(df) > 0:  # TODO shouldn't be needed
            df["n_projects"] = df["id"].map(n_projects)
        return Lookup(df)

    @classmethod
    def audio_files(
        cls,
        *wheres: Union[ExpressionsLike, int, str, AudioFiles],
        like: bool = False,
        regex: bool = False,
    ) -> Lookup:
        """


        Args:
            *wheres:
            like:
            regex:

        Returns:

        """
        query = AudioFiles.select(AudioFiles, Stimuli).join(Stimuli, JOIN.LEFT_OUTER)
        return Lookups._simple(
            AudioFiles,
            query,
            like,
            regex,
            wheres,
            "id",
            "filename",
            "n_seconds",
            ("creator", "creator.username"),
            "notes",
            "created",
        )

    @classmethod
    def suppliers(
        cls,
        *wheres: Union[ExpressionsLike, int, str, Suppliers],
        like: bool = False,
        regex: bool = False,
    ) -> Lookup:
        """


        Args:
            *wheres:
            like:
            regex:

        Returns:

        """
        query = Suppliers.select()
        return Lookups._simple(Suppliers, query, like, regex, wheres, "id", "name", "description")

    @classmethod
    def refs(
        cls,
        *wheres: Union[ExpressionsLike, int, str, Refs],
        like: bool = False,
        regex: bool = False,
    ) -> Lookup:
        """


        Args:
            *wheres:
            like:
            regex:

        Returns:

        """
        query = Refs.select()
        return Lookups._simple(
            Refs,
            query,
            like,
            regex,
            wheres,
            "id",
            "name",
            "description",
            "datetime_downloaded",
            "external_version",
            "url",
            "created",
        )

    @classmethod
    def features(
        cls,
        *wheres: Union[ExpressionsLike, int, str, Features],
        like: bool = False,
        regex: bool = False,
    ) -> Lookup:
        """


        Args:
            *wheres:
            like:
            regex:

        Returns:

        """
        query = Features.select()
        return Lookups._simple(
            Features,
            query,
            like,
            regex,
            wheres,
            "id",
            "name",
            "description",
            "dimensions",
            "data_type",
            "created",
        )

    @classmethod
    def sensors(
        cls,
        *wheres: Union[ExpressionsLike, int, str, Sensors],
        like: bool = False,
        regex: bool = False,
    ) -> Lookup:
        """


        Args:
            *wheres:
            like:
            regex:

        Returns:

        """
        query = Sensors.select()
        return Lookups._simple(
            Sensors,
            query,
            like,
            regex,
            wheres,
            "id",
            "name",
            "description",
            "data_type",
            "blob_type",
            "n_between",
            "created",
        )

    @classmethod
    def stimuli(
        cls,
        *wheres: Union[ExpressionsLike, int, str, Stimuli],
        like: bool = False,
        regex: bool = False,
    ) -> Lookup:
        """


        Args:
            *wheres:
            like:
            regex:

        Returns:

        """
        query = Stimuli.select(Stimuli, AudioFiles).join(AudioFiles, JOIN.LEFT_OUTER)
        return Lookups._simple(
            Stimuli,
            query,
            like,
            regex,
            wheres,
            "id",
            "name",
            ("display_name", "name", ValarTools.stimulus_display_name),
            "description",
            ("display_color", "name", ValarTools.stimulus_display_color),
            ("n_seconds", "audio_file.n_seconds"),
            "wavelength_nm",
            "audio_file_id",
            ("audio_filename", "audio_file.filename"),
            ("audio_size", "audio_file.data", lambda d: Tools.friendly_size(len(d)) if d else None),
        )

    @classmethod
    def plate_types(
        cls,
        *wheres: Union[ExpressionsLike, str, PlateTypes],
        like: bool = False,
        regex: bool = False,
    ) -> Lookup:
        """


        Args:
            *wheres:
            like:
            regex:

        Returns:

        """
        query = PlateTypes.select(PlateTypes, Suppliers).join(Suppliers, JOIN.LEFT_OUTER)
        return Lookups._simple(
            PlateTypes,
            query,
            like,
            regex,
            wheres,
            "id",
            "name",
            ("supplier", "supplier.name"),
            "part_number",
            "n_rows",
            "n_columns",
            "well_shape",
            "opacity",
        )

    @classmethod
    def saurons(
        cls,
        *wheres: Union[ExpressionsLike, int, str, Saurons],
        like: bool = False,
        regex: bool = False,
    ) -> Lookup:
        """


        Args:
            *wheres:
            like:
            regex:

        Returns:

        """
        query = Saurons.select(Saurons)
        return Lookups._simple(Saurons, query, like, regex, wheres, "id", "name", "active")

    @classmethod
    def sauron_configs(
        cls, *wheres: Union[ExpressionsLike, int, SauronConfigs], **kwargs
    ) -> Lookup:
        """


        Args:
            *wheres:
            **kwargs:

        Returns:

        """
        like = kwargs.get("like") is True
        regex = kwargs.get("regex") is True
        query = SauronConfigs.select(SauronConfigs, Saurons).join(Saurons)
        return Lookups._simple(
            SauronConfigs,
            query,
            like,
            regex,
            wheres,
            "id",
            ("sauron_id", "sauron_id"),
            ("sauron_name", "sauron.name"),
            "description",
            "datetime_changed",
            "created",
        ).sort_values(["sauron_name", "datetime_changed"])

    @classmethod
    def control_types(
        cls,
        *wheres: Union[ExpressionsLike, int, str, ControlTypes],
        like: bool = False,
        regex: bool = False,
    ) -> Lookup:
        """


        Args:
            *wheres:
            like:
            regex:

        Returns:

        """
        query = ControlTypes.select()
        return Lookups._simple(
            ControlTypes,
            query,
            like,
            regex,
            wheres,
            "id",
            "name",
            "description",
            ("positive", "positive", bool),
            ("drug_related", "drug_related", bool),
            ("genetics_related", "genetics_related", bool),
        )

    @classmethod
    def locations(
        cls,
        *wheres: Union[ExpressionsLike, int, str, Locations],
        like: bool = False,
        regex: bool = False,
    ) -> Lookup:
        """


        Args:
            *wheres:
            like:
            regex:

        Returns:

        """
        # noinspection PyPep8Naming
        Parents = Locations.alias()
        query = Locations.select().join(
            Parents, JOIN.LEFT_OUTER, on=(Locations.part_of == Parents.id)
        )
        return Lookups._simple(
            Locations,
            query,
            like,
            regex,
            wheres,
            "id",
            "name",
            "description",
            "purpose",
            ("part_of", "part_of.name"),
            ("active", "active", bool),
            ("temporary", "temporary", bool),
        )

    @classmethod
    def batteries(
        cls, *wheres: Union[ExpressionsLike, BatteryLike], like: bool = False, regex: bool = False
    ) -> Lookup:
        """


        Args:
            *wheres:
            like:
            regex:

        Returns:

        """
        # TODO does this work for empty batteries?
        query = (
            Batteries.select(Batteries, Users)
            .join(Users, JOIN.LEFT_OUTER)
            .switch(Batteries)
            .join(AssayPositions, JOIN.RIGHT_OUTER)
            .join(Assays)
        )
        return Lookups._simple(
            Batteries,
            query,
            like,
            regex,
            wheres,
            "id",
            "name",
            ("description", "description", Tools.truncate),
            ("author", "author.username"),
            "length",
            ("hidden", "hidden", bool),
            ("when_inserted", "created"),
        ).drop_duplicates()

    @classmethod
    def assays(
        cls, *wheres: Union[ExpressionsLike, AssayLike], like: bool = False, regex: bool = False
    ) -> Lookup:
        """


        Args:
            *wheres:
            like:
            regex:

        Returns:

        """
        query = (
            Assays.select(Assays, Users, TemplateAssays)
            .join(TemplateAssays, JOIN.LEFT_OUTER)
            .join(Users, JOIN.LEFT_OUTER)
        )
        return Lookups._simple(
            Assays,
            query,
            like,
            regex,
            wheres,
            "id",
            "name",
            ("description", "description", Tools.truncate),
            ("author", "template_assay.author.username"),
            "length",
            ("hidden", "hidden", bool),
            ("template", "template_assay.name"),
            ("when_inserted", "created"),
        )

    @classmethod
    def variants(
        cls,
        *wheres: Union[ExpressionsLike, int, str, GeneticVariants],
        like: bool = False,
        regex: bool = False,
    ) -> Lookup:
        """


        Args:
            *wheres:
            like:
            regex:

        Returns:

        """
        query = GeneticVariants.select(GeneticVariants, Users).join(Users, JOIN.LEFT_OUTER)
        variants = {v.id: v for v in GeneticVariants.select()}
        df = Lookups._simple(
            GeneticVariants,
            query,
            like,
            regex,
            wheres,
            "id",
            "name",
            ("creator", "creator.username"),
            ("mother", "mother_id", lambda m: variants[m].name if m is not None else None),
            ("father", "father_id", lambda m: variants[m].name if m is not None else None),
            "lineage_type",
            "notes",
            "date_created",
            ("fully_annotated", "fully_annotated", bool),
            ("when_inserted", "created"),
        )
        return df

    @classmethod
    def _add_names(cls, df, id_col: str):
        """


        Args:
          df:
          id_col: str:

        Returns:

        """
        if len(df) > 0:
            all_ids = {
                int(c) for c in df[id_col].unique().tolist() if not Tools.is_null(c) and c != ""
            }
            names = _compound_namer.fetch(all_ids)
            df["best_name"] = df[id_col].map(lambda x: names[x] if x in names else None)
        else:
            df["best_name"] = []
        return Lookup.convert(df)


__all__ = ["Lookups"]

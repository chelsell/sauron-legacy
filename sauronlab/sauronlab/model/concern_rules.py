"""
Concerns are specifically concerns about runs.
They include run and batch annotations, number of features, and more.
"""

from __future__ import annotations

import inspect

from sauronlab.core.core_imports import *
from sauronlab.model.concerns import *
from sauronlab.model.features import *
from sauronlab.model.sensors import *
from sauronlab.model.well_frames import *

control_types = {c.name: c for c in ControlTypes.select()}
TRASH_CONTROLS = {
    c: control_types[c]
    for c in {"ignore", "near-WT (-)", "no drug transfer", "low drug transfer"}
    if c in control_types
}
DEFINITELY_BAD_CONTROLS = {
    c: control_types[c] for c in {"no drug transfer", "low drug transfer"} if c in control_types
}


class ConcernRule:
    """"""

    @property
    def clazz(self) -> Type[Concern]:
        """ """
        raise NotImplementedError()

    def of(self, df: WellFrame):
        """


        Args:
          df: WellFrame:

        Returns:

        """
        raise NotImplementedError()

    def severity(self, concern) -> Severity:
        """


        Args:
          concern:

        Returns:

        """
        raise NotImplementedError()

    def _new(self, run: Runs, *args):
        """


        Args:
            run: Runs:
            *args:

        Returns:

        """
        # noinspection PyArgumentList
        concern = self.clazz(run, Severity.CRITICAL, *args)
        # noinspection PyArgumentList
        return self.clazz(run, self.severity(concern), *args)


class MissingSensorConcernRule(ConcernRule):
    """ """

    def __init__(self, as_of: datetime):
        self.as_of = as_of

    @property
    def clazz(self) -> Type[Concern]:
        """ """
        return MissingSensorConcern

    def severity(self, concern: MissingSensorConcern) -> Severity:
        """


        Args:
            concern: MissingSensorConcern:

        Returns:

        """
        # 16, 17 are snapshots, so missing them isn't serious
        missing = {s for s in concern.missing}
        bad = {s for s in concern.missing if s.id not in [16, 17]}
        verybad = {s for s in concern.missing if s.id not in [16, 17]}
        generation = concern.generation
        version = (
            ValarTools.run_tag(concern.run, "sauronx_version") if generation.is_sauronx() else None
        )
        if concern.generation.is_pointgrey():
            pass
            # if it was SauronX with pymata-aio, then missing light sensors is critical
        if len(verybad) > 0 and concern.generation.is_pointgrey():
            return Severity.CRITICAL
        elif len(verybad) > 0:
            return Severity.DANGER
        elif len(bad) > 0 and concern.generation.is_pointgrey():
            return Severity.WARNING
        elif len(bad) > 0:
            return Severity.CAUTION  # just missing snapshots
        else:
            return Severity.GOOD

    def of(self, df: WellFrame) -> Generator[MissingSensorConcern, None, None]:
        """


        Args:
            df: WellFrame:

        Returns:

        """
        for run in df.unique_runs():
            run = Runs.fetch(run)
            # TODO check registry
            generation = ValarTools.generation_of(run)
            expected = set(ValarTools.required_sensors(generation).values())
            actual = set(ValarTools.sensors_on(run))
            yield self._new(run, generation, expected, actual)


class SensorLengthConcernRule(ConcernRule):
    """"""

    def __init__(self, as_of: datetime, sensor_cache):
        self.as_of = as_of
        self.sensor_cache = sensor_cache

    @property
    def clazz(self) -> Type[Concern]:
        """ """
        return SensorLengthConcern

    def severity(self, concern: SensorLengthConcern) -> Severity:
        """


        Args:
            concern: SensorLengthConcern:

        Returns:

        """
        for thresh, level in zip(
            [2, 2 / 4, 2 / 16, 2 / 16, 2 / 256],
            [Severity.CRITICAL, Severity.DANGER, Severity.WARNING, Severity.CAUTION, Severity.NOTE],
        ):
            if concern.actual < concern.expected and abs(concern.log2_diff) < thresh:
                return level
        return Severity.GOOD

    def of(self, df: WellFrame) -> Generator[SensorLengthConcern, None, None]:
        """


        Args:
            df: WellFrame:

        Returns:

        """
        for run in df.unique_runs():
            generation = ValarTools.generation_of(run)
            if generation is not DataGeneration.POINTGREY:
                continue  # not supported -- yet
            extant_sensor: str = next(
                iter(k for k, v in ValarTools.required_sensors(generation).items())
            )
            sensor = ValarTools.standard_sensor(extant_sensor, generation)
            run = Runs.fetch(run)
            sampling = float(
                ValarTools.toml_item(run, "sauron.hardware.sensors.sampling_interval_milliseconds")
            )
            expected = np.float(run.experiment.battery.length / sampling)
            photo_data = None
            try:
                photo_data = self.sensor_cache.load((SensorNames.PHOTOSENSOR, run))
            except ValarLookupError:
                pass  # hit debug below
            if photo_data is None:
                logger.debug(f"Missing photosensor data on r{run.id}")
            else:
                actual = np.float(len(photo_data.data))
                yield self._new(run, expected, actual, generation, sensor)
                # we won't bother for thermo


class TargetTimeConcernRule(ConcernRule):
    """
    Processes deviations from expected treatment, wait, and acclimation durations.
        Looks for rows in the ``Annotations`` tables with names:
            - expected :: seconds :: acclimation
            - expected :: seconds :: wait
            - expected :: seconds :: treatment
        When it can't find an annotation, falls back to the value in ``Concerns.expected_times``.
        Otherwise, yields a concern for each run, each of the 3 kinds, and each corresponding annotations.

    """

    def __init__(self, as_of: datetime):
        self.as_of = as_of

    @property
    def clazz(self) -> Type[Concern]:
        """ """
        return TargetTimeConcern

    def severity(self, concern: TargetTimeConcern) -> Severity:
        """
        Gets a severity based on various lab experience.
        Subject to change. Current rules:
            Tries the levels from highest to lowest, each with a progressively more liberal bound on relative error.
            Each level's bound is its higher level's bound divided by a power of 2.
            These powers are: 1, 2, 4, 16
            For treatment time:
                - rel error > 2.0    ⇒ DANGER
                - rel error > 1.25   ⇒ WARNING
                - rel error > 1.0625 ⇒ CAUTION
                - rel error > 1.125  ⇒ NOTE
                - rel error ≤ 1.125  ⇒ GOOD
                So for a 1-hour treatment time, DANGER is <30min or >2hr,
                WARNING is <45min or >90min,
                CAUTION or higher is applied for being 7.5 minutes late,
                and GOOD is applied for being ≤3.75 minutes late.
            For (pre-treatment) wait time:
                The logic is similar, following halving thresholds.
                But the bounds are asymmetric: For DANGER, < 4-fold or > 8-fold (usually <15min or >8hr)
            For (dark) acclimation time:
                Same idea, with values < 4-fold or > 8-fold (usually <2.5min or >80min)

        Args:
          concern: TargetTimeConcern:

        Returns:

        """
        # TODO: What is this??
        if hasattr(self, "__severity") and self.__severity is not None:
            return self.__severity

        def fail(low, high) -> bool:
            """


            Args:
              low:
              high:

            Returns:

            """
            return concern.log2_diff < low or concern.log2_diff >= high

        def halving(low, high):
            """


            Args:
              low:
              high:

            Returns:

            """
            for i, then in zip(
                [1, 2, 4, 16], [Severity.DANGER, Severity.WARNING, Severity.CAUTION, Severity.NOTE]
            ):
                if fail(low / i, high / i):
                    return then
            return Severity.GOOD

        if concern.kind is TargetTimeKind.TREATMENT:
            return halving(-2, 2)
        elif concern.kind is TargetTimeKind.WAIT:
            return halving(-4, 8)
        elif concern.kind is TargetTimeKind.ACCLIMATION:
            return halving(-4, 8)
        else:
            assert False, concern.kind

    def of(self, df: WellFrame) -> Generator[TargetTimeConcern, None, None]:
        """


        Args:
            df: WellFrame:

        Returns:

        """
        for run in df.unique_runs():
            run = Runs.fetch(run)  # type: Runs
            yield from self._time_concerns(run, TargetTimeKind.ACCLIMATION)
            yield from self._time_concerns(run, TargetTimeKind.WAIT)
            if run.datetime_dosed is not None:
                yield from self._time_concerns(run, TargetTimeKind.TREATMENT)

    def _time_concerns(
        self, run: Runs, kind: TargetTimeKind
    ) -> Generator[TargetTimeConcern, None, None]:
        """


        Args:
            run: Runs:
            kind: TargetTimeKind:

        Returns:

        """
        actual = self._fetch_actual_time(run, kind)
        if actual is None:
            actual = np.inf
        for expected, tag in self._fetch_expected_times(run, kind):
            yield self._new(run, expected, actual, kind, tag)

    def _fetch_actual_time(self, run: Runs, kind: TargetTimeKind) -> float:
        if kind is TargetTimeKind.WAIT:
            return ValarTools.wait_sec(run)
        elif kind is TargetTimeKind.TREATMENT:
            return ValarTools.treatment_sec(run)
        else:
            return ValarTools.acclimation_sec(run)

    def _fetch_expected_times(
        self, run: Runs, kind: TargetTimeKind
    ) -> Generator[Tup[float, Optional[Annotations]], None, None]:
        # get from experiment notes; otherwise fall back
        # but always override if there are Annotations for that run
        annotation_name = "expected :: seconds :: " + kind.name.lower()
        pattern = regex.compile(annotation_name + " *= *" + "(\\d+)", flags=regex.V1)
        if run.experiment.notes:
            match = list(pattern.finditer(run.experiment.notes))
            if len(match) > 2:
                logger.error(
                    f"Multiple tags for {annotation_name} in experiment {run.experiment.name}"
                )
                expected = self.default_expected_time(kind)
            elif len(match) == 1:
                expected = float(match[0].group(1))
            else:
                expected = self.default_expected_time(kind)
            annots = self._find_annotations(run, kind)
            if len(annots) > 0:
                for tag in annots:
                    try:
                        yield float(tag.value)
                        yield float(tag.value), tag
                    except (AttributeError, ArithmeticError):
                        raise XValueError(
                            f"Annotation {tag.id} does not have a valid float value (is {tag.value})"
                        )
            else:
                yield (expected, None)

    def default_expected_time(self, kind: TargetTimeKind) -> float:
        """


        Args:
            kind: TargetTimeKind:

        Returns:

        """
        return {
            TargetTimeKind.ACCLIMATION: 10 * 60,
            TargetTimeKind.WAIT: 60 * 60,
            TargetTimeKind.TREATMENT: 60 * 60,
        }[kind]

    def _find_annotations(self, run: Runs, kind: TargetTimeKind) -> Sequence[Annotations]:
        annotation_name = "expected :: seconds :: " + kind.name.lower()
        return list(
            Annotations.select()
            .where(Annotations.run == run)
            .where(Annotations.name == annotation_name)
        )


class BatchConcernRule(ConcernRule):
    """"""

    def __init__(self, as_of: datetime):
        self.as_of = as_of

    @property
    def clazz(self) -> Type[Concern]:
        """ """
        return BatchConcern

    def severity(self, concern: BatchConcern) -> Severity:
        return Severity.parse(concern.annotation.level)

    def of(self, df: WellFrame) -> Generator[BatchConcern, None, None]:
        runs = {run.id: run for run in Runs.fetch_all(df.unique_runs())}
        batches = {batch.id: batch for batch in Batches.fetch_all(df.unique_batch_ids())}
        query = BatchAnnotations.select().where(BatchAnnotations.batch << set(batches.keys()))
        if self.as_of:
            query = query.where(BatchAnnotations.created < self.as_of)
        anns = Tools.multidict(query, "batch_id")
        for run in df.unique_runs():
            for batch_id in df.with_run(run).unique_batch_ids():
                for concern in anns[batch_id]:
                    yield self._new(runs[run], batches[batch_id], concern)


class AnnotationConcernRule(ConcernRule):
    """"""

    def __init__(self, as_of: datetime):
        self.as_of = as_of

    @property
    def clazz(self) -> Type[Concern]:
        """ """
        return AnnotationConcern

    def severity(self, concern: AnnotationConcern) -> Severity:
        return Severity.parse(concern.annotation.level)

    def of(self, df: WellFrame) -> Generator[AnnotationConcern, None, None]:
        runs = {run.id: run for run in Runs.fetch_all(df.unique_runs())}
        query = (
            Annotations.select(Annotations, Users, Runs, Submissions)
            .join(Users, JOIN.LEFT_OUTER)
            .switch(Annotations)
            .join(Runs)
            .switch(Annotations)
            .join(Submissions, JOIN.LEFT_OUTER)
            .where(Annotations.run_id << set(runs))
        )
        if self.as_of:
            query = query.where(Annotations.created < self.as_of)
        anns = Tools.multidict(query, "run_id")
        for run in df.unique_runs():
            for concern in anns[run]:
                yield self._new(runs[run], concern)


class ToFixConcernRule(ConcernRule):
    """"""

    def __init__(self, as_of: datetime):
        self.as_of = as_of

    @property
    def clazz(self) -> Type[Concern]:
        return ToFixConcern

    def severity(self, concern: ToFixConcern) -> Severity:
        if concern.fixed_with is None:
            return Severity.NOTE
        else:
            return Severity.parse(concern.annotation.level)

    def of(self, df: WellFrame) -> Generator[ToFixConcern, None, None]:
        runs = {run.id: run for run in Runs.fetch_all(df.unique_runs())}
        to_fixes = Tools.multidict(self._query("to_fix", runs), "run_id")
        fixed = Tools.multidict(self._query("fixed", runs), "run_id")
        for run in df.unique_runs():
            to_fixes_r = sorted(to_fixes[run], key=lambda a: a.created)
            fixed_values = Tools.multidict(fixed[run], "value")
            for to_fix in to_fixes_r:
                yield self._new(runs[run], to_fix, fixed_values.get(str(to_fix.id)))

    def _query(self, level: str, runs):
        q = (
            Annotations.select(Annotations, Users, Runs, Submissions)
            .join(Users, JOIN.LEFT_OUTER)
            .switch(Annotations)
            .join(Runs)
            .switch(Annotations)
            .join(Submissions, JOIN.LEFT_OUTER)
            .where(Annotations.run_id << set(runs))
            .where(Annotations.level == level)
        )
        return q.where(Annotations.created < self.as_of)


class GenerationConcernRule(ConcernRule):
    """"""

    def __init__(self, as_of: datetime, feature: Union[FeatureType, str]):
        self.as_of = as_of
        self.feature = FeatureTypes.of(feature)

    @property
    def clazz(self) -> Type[Concern]:
        return GenerationConcern

    def severity(self, concern: GenerationConcern) -> Severity:
        return Severity.DANGER

    def of(self, df: WellFrame) -> Generator[GenerationConcern, None, None]:
        if self.feature is None:
            return
        runs = {run.id: run for run in Runs.fetch_all(df.unique_runs())}
        for run in df.unique_runs():
            generation = ValarTools.generation_of(run)
            if generation not in self.feature.generations:
                yield self._new(runs[run], self.feature.generations, generation)


class ImpossibleTimeConcernRule(ConcernRule):
    """"""

    def __init__(self, as_of: datetime):
        self.as_of = as_of

    @property
    def clazz(self) -> Type[Concern]:
        return ImpossibleTimeConcern

    def severity(self, concern: ImpossibleTimeConcern) -> Severity:
        generation = ValarTools.generation_of(concern.run)
        # some legacy data was missing these values (especially datetime plated)
        if generation.is_sauronx() or str(concern.value) != "None":
            return Severity.DANGER
        else:
            return Severity.CAUTION

    def of(self, df: WellFrame) -> Generator[ImpossibleTimeConcern, None, None]:
        runs = {run.id: run for run in Runs.fetch_all(df.unique_runs())}
        for run in df.unique_runs():
            run = runs[run]
            dfx = df.with_run(run)
            batches = dfx["b_ids"].unique()
            plate = Plates.fetch(run.plate)  # type: Plates
            if run.plate.datetime_plated is None:
                yield self._new(run, "datetime_plated", "None")
            if len(batches) > 0 and run.datetime_dosed is None:
                yield self._new(
                    run,
                    "datetime_dosed",
                    f"None [batches {','.join([str(b) for b in batches])}]",
                )
            if len(batches) == 0 and run.datetime_dosed is not None:
                yield self._new(
                    run, "datetime_dosed", run.datetime_dosed.isoformat() + " [no batches]"
                )
            if run.datetime_dosed is not None and run.datetime_run < run.datetime_dosed:
                yield self._new(
                    run,
                    "datetime_dosed" + Chars.right + "datetime_run",
                    run.datetime_dosed.isoformat() + Chars.right + run.datetime_run.isoformat(),
                )
            if plate.datetime_plated is not None and run.datetime_run < plate.datetime_plated:
                yield self._new(
                    run,
                    "datetime_plated" + Chars.right + "datetime_run",
                    plate.datetime_plated.isoformat() + Chars.right + run.datetime_run.isoformat(),
                )


class NFeaturesConcernRule(ConcernRule):
    """"""

    def __init__(self, as_of: datetime, feature: Union[None, FeatureType, str]):
        self.as_of = as_of
        self.feature = None if feature is None else FeatureTypes.of(feature)

    @property
    def clazz(self) -> Type[Concern]:
        return NFeaturesConcern

    def severity(self, concern: NFeaturesConcern) -> Severity:
        # multiples of 4
        if concern.raw_error > 192:
            return Severity.CRITICAL
        elif concern.raw_error > 48:
            return Severity.DANGER
        elif concern.raw_error > 12:
            return Severity.WARNING
        elif concern.raw_error > 3:
            # losing up to 2 is expected due to trimming
            # in practice, 3 are often lost
            # gaining frames is much weirder, but we'll keep the same thresholds
            return Severity.CAUTION
        elif concern.raw_error > 0:
            return Severity.NOTE
        else:
            return Severity.GOOD

    def of(self, df: WellFrame) -> Generator[GenerationConcern, None, None]:
        if self.feature is None or not self.feature.time_dependent:
            return
        runs = {run.id: run for run in Runs.fetch_all(df.unique_runs())}
        for run in df.unique_runs():
            dfx = WellFrame.of(df.with_run(run))
            n_expected = int(ValarTools.expected_n_frames(run))
            n_actual = int(dfx.feature_length())
            n_nan = dfx.count_nans_at_end() + dfx.count_nans_at_start()
            yield self._new(runs[run], n_expected, n_actual - n_nan)


class WellConcernRule(ConcernRule):
    """"""

    def __init__(self, as_of: datetime):
        self.as_of = as_of

    @property
    def clazz(self) -> Type[Concern]:
        return WellConcern

    def severity(self, concern: WellConcern) -> Severity:
        very_bad = {
            t.name: n for t, n in concern.trash.items() if t.name in DEFINITELY_BAD_CONTROLS
        }
        if len(very_bad) == 24:
            return Severity.CRITICAL
        if len(very_bad) > 12:
            return Severity.DANGER
        elif len(very_bad) > 6:
            return Severity.WARNING
        elif len(concern.trash) > 0:
            return Severity.CAUTION
        else:
            return Severity.GOOD

    def of(self, df: WellFrame) -> Generator[WellConcern, None, None]:
        def counts(dfx):
            x = {v: len(dfx.with_controls(c)) for c, v in TRASH_CONTROLS.items()}
            return {a: b for a, b in x.items() if b > 0}

        for run in df.unique_runs():
            cs = counts(df.with_run(run))
            yield self._new(Runs.fetch(run), cs)


STANDARD_CONCERN_RULES = frozenlist(
    [
        GenerationConcernRule,
        ImpossibleTimeConcernRule,
        MissingSensorConcernRule,
        SensorLengthConcernRule,
        NFeaturesConcernRule,
        TargetTimeConcernRule,
        AnnotationConcernRule,
        ToFixConcernRule,
        WellConcernRule,
        BatchConcernRule,
    ]
)


class ConcernRuleCollection:
    """"""

    def __init__(
        self,
        feature: Union[FeatureType, str],
        sensor_cache,
        as_of: Optional[datetime],
        min_severity: Union[int, str, Severity] = Severity.GOOD,
    ):
        self.feature = FeatureTypes.of(feature)
        self.sensor_cache = sensor_cache
        self.as_of = as_of
        self.min_severity = Severity.of(min_severity)

    @classmethod
    def create(
        cls,
        classes: Sequence[Type[ConcernRule]] = STANDARD_CONCERN_RULES,
        name: str = "MyConcernRuleCollection",
        exclude: Optional[Iterable[Union[Type[ConcernRule], str]]] = None,
    ) -> Type[ConcernRuleCollection]:
        """
        Generates a new type from a list of rule classes.
        In ``rules``, maps every argument to a ConcernRule's ``__init__`` using
        attributes of the *created MyRuleCollection instance's* of the same name.
        For example, in the following:

            MyConcernRuleCollection = ConcernRuleCollection.create([SensorLengthConcernRule])
            collection = MyConcernRuleCollection("MI", my_sensor_cache, datetime(2021, 1, 1))
            concerns = collection.of(df)

        Here, ``collection.of`` will map ``collection.sensor_cache`` (value: ``my_sensor_cache``)
        to the ``sensor_cache`` parameter of ``SensorLengthConcernRule.__init__``.

        Args:
            classes: Sequence of ConcernRule types to include
            name: Sets the name of the created class
            exclude: For convenience, exclude these sensor types (even if in ``classes``)

        Returns:
            A ConcernRuleCollection *type*
        """
        if exclude is None:
            exclude = []
        exclude = {e if isinstance(e, str) else e.__name__ for e in exclude}

        class C(ConcernRuleCollection):
            @property
            def rules(self) -> Sequence[ConcernRule]:
                instances = []
                for clazz in classes:
                    if clazz.__name__ in exclude:
                        continue
                    params = inspect.signature(clazz.__init__).parameters
                    args = {p: getattr(self, p) for p in params.keys() if p != "self"}
                    # noinspection PyArgumentList
                    created = clazz(**args)
                    instances.append(created)
                return instances

        C.__name__ = name
        return C

    @property
    def rules(self) -> Sequence[ConcernRule]:
        """ """
        raise NotImplementedError()

    def of(self, df: WellFrame) -> Generator[Concern, None, None]:
        runs = list(df.unique_runs())
        key = Severity.key_str()
        if len(runs) > 1:
            logger.info(f"Checking {self.__class__.__name__} on {len(runs)} runs.")
        elif len(runs) == 1:
            logger.info(f"Checking {self.__class__.__name__} on run r{runs[0]}.")
        for rule in self.rules:
            logger.debug(f"Checking rule {rule.__class__.__name__}")
            concerns = list(rule.of(df))
            if len(concerns) > 0 and len(runs) == 1:
                logger.debug(f"Found {len(concerns)} concerns on r{runs[0]}.")
            elif len(concerns) > 0:
                logger.debug(f"Found {len(concerns)} concerns on {len(runs)} runs.")
            for concern in concerns:
                if concern.severity >= self.min_severity:
                    logger.debug(
                        f"Found concern {concern.__class__.name} on r{concern.run.id}: {concern.description()}"
                    )
                    yield concern


class SimpleConcernRuleCollection(ConcernRuleCollection):
    """"""

    @property
    def rules(self) -> Sequence[ConcernRule]:
        """ """
        return [
            GenerationConcernRule(self.as_of, self.feature),
            ImpossibleTimeConcernRule(self.as_of),
            MissingSensorConcernRule(self.as_of),
            SensorLengthConcernRule(self.as_of, self.sensor_cache),
            NFeaturesConcernRule(self.as_of, self.feature),
            TargetTimeConcernRule(self.as_of),
            AnnotationConcernRule(self.as_of),
            ToFixConcernRule(self.as_of),
            WellConcernRule(self.as_of),
            BatchConcernRule(self.as_of),
        ]


# TODO
# SimpleConcernRuleCollection = ConcernRuleCollection.create(
#    STANDARD_CONCERN_RULES,
#    name="SimpleConcernRuleCollection"
# )


class Concerns:
    """"""

    @classmethod
    def create(
        cls,
        classes: Sequence[Type[ConcernRule]] = STANDARD_CONCERN_RULES,
        name: str = "MyConcernRuleCollection",
        exclude: Optional[Iterable[Union[Type[ConcernRule], str]]] = None,
    ) -> Type[ConcernRuleCollection]:
        return ConcernRuleCollection.create(classes, name, exclude)

    create.__doc__ = ConcernRuleCollection.create.__doc__

    @classmethod
    def default_collection(
        cls,
        feature: Union[FeatureType, str],
        sensor_cache,
        as_of: Optional[datetime],
        min_severity: Union[int, str, Severity] = Severity.GOOD,
    ) -> ConcernRuleCollection:
        """


        Args:
            feature:
            sensor_cache:
            as_of:
            min_severity:

        Returns:

        """
        return SimpleConcernRuleCollection(feature, sensor_cache, as_of, min_severity)

    @classmethod
    def of(
        cls,
        df: WellFrame,
        feature: Union[FeatureType, str],
        sensor_cache,
        as_of: Optional[datetime],
        min_severity: Union[int, str, Severity] = Severity.GOOD,
    ) -> Sequence[Concern]:
        """


        Args:
            df: WellFrame:
            feature:
            sensor_cache:
            as_of:
            min_severity:

        Returns:

        """
        return list(cls.default_collection(feature, sensor_cache, as_of, min_severity).of(df))

    @classmethod
    def log_warnings(cls, concerns: Sequence[Concern]):
        """


        Args:
            concerns:

        Returns:

        """
        concerns = list(concerns)  # might be a generator, even though that's the wron gtype
        if len(concerns) == 0:
            return  # will break the max fn otherwise
        widest_severity = max([len(c.severity.name.lower()) for c in concerns])
        widest_name = max([len(c.name) for c in concerns])
        widest_run = max([1 + len(str(c.run.id)) for c in concerns])
        for concern in concerns:
            concern.severity.log_fn(
                concern.severity.emoji
                + " "
                + ("r" + str(concern.run.id)).ljust(widest_run + 1)
                + " "
                + concern.name.ljust(widest_name + 1)
                + " "
                + Chars.shelled(concern.severity.name.lower()).rjust(widest_severity + 1)
                + " "
                + concern.description()
            )

    @classmethod
    def to_df(cls, concerns: Sequence[Concern]) -> ConcernFrame:
        """


        Args:
            concerns:

        Returns:

        """
        return ConcernFrame([pd.Series(concern.as_dict()) for concern in concerns])


__all__ = [
    "LoadConcern",
    "SimpleConcernRuleCollection",
    "ConcernRuleCollection",
    "Concerns",
]

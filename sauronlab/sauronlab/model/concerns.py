"""
Concerns are specifically concerns about runs.
They include run and batch annotations, number of features, and more.
"""

from __future__ import annotations

# importing dataclass directly is necessary to fix pycharm warnings
from dataclasses import dataclass
from traceback import FrameSummary, StackSummary

from sauronlab.core.core_imports import *
from sauronlab.model.cache_interfaces import ASensorCache
from sauronlab.model.features import *
from sauronlab.model.sensors import *
from sauronlab.model.well_frames import *


class ConcernFrame(UntypedDf):
    """"""

    pass


class TargetTimeKind(Enum):
    """"""

    ACCLIMATION = 1
    WAIT = 2
    TREATMENT = 3


@enum.unique
class Severity(enum.Enum):
    """
    An enum and estimate of how bad a concern is.

    These values are analagous to the choices in Annotations.level and BatchAnnotations.level.
    And in cases where the Concern is derived from an Annotation or BatchAnnotation,
    the Concern's Severity will generally be equivalent to the annotation's level.
    The exceptions are 'fix' and 'to_fix' (described below).
    In order of best to worst:
        * GOOD       ~ '0:good'      Indicates that the data is more trustworthy than normally expected (not a concern)
        * NOTE       ~ '1:note'      Indicates something neither good nor bad (also not a concern)
        * CAUTION    ~ '2:caution'   Something concerning but will (generally) interfere in _no_ analyses (ex: wait time is 2 hours instead of 1)
        * WARNING    ~ '3:warning'   Something that will interfere in _some_ analyses (ex: treatment time is 2 hours instead of 1)
        * DANGER     ~ '4:danger'    Something that will interfere in _most_ analyses (ex: blue LED was out)
        * CRITICAL   ~ '9:deleted'   Something that will interfere with _all_ analyses; the data should be discarded (ex: video was empty)
    Because we don't delete data, even if it's garbage, adding a 9:delete annotation effectively marks the data as deleted.

    Annotations with 'to_fix' or 'fixed' annotations are generally translated as:
        * to_fix     ~ DANGER (you REALLY should fix it before analyzing)
        * fixed      ~ NOTE   (fixing an issue doesn't make the data better than expected)

    Many Concern types are not derived from Annotations or BatchAnnotations.
    For example, wells with low drug transfer, late treatment times, missing features or sensors, etc.
    ConcernRule define a Severity, but you can of course make your own rules for defining these.

    For example:
    The Severity of treatment times built into ``TargetTimeConcernRule.severity`` has specific rules
    for how bad (or good) a late (or early) treatment, wait (pre-treatment), or acclimation duration is.
    For example, >2-fold late treatment is marked with DANGER.
    You could also define your own function::

        def lateness(concern: TargetTimeConcern) -> Severity:
            if concern.kind is not TargetTimeKind.TREATMENT:


    A good rule of thumb:
        - DANGER or CRITICAL  -- discard or fix
        - WARNING            -- examine and decide
        - CAUTION            -- examine and confirm
        - GOOD or NOTE       -- ignore these

    """

    GOOD, NOTE, CAUTION, WARNING, DANGER, CRITICAL = 0, 1, 2, 3, 4, 9

    def __lt__(self, other):
        return self.value < other.value

    def __gt__(self, other):
        return self.value > other.value

    def __le__(self, other):
        return self.value <= other.value

    def __ge__(self, other):
        return self.value >= other.value

    @property
    def to_enum_value(self) -> str:
        """ """
        return self.value + ":" + self.name.lower()

    @property
    def log_fn(self):
        """"""
        return getattr(logger, self.log_level.lower())

    @property
    def log_level(self) -> str:
        """"""
        return {
            9: "ERROR",
            4: "WARNING",
            3: "WARNING",
            2: "CAUTION",
            1: "INFO",
            0: "INFO",
        }[  # shouldn't be used, so don't
            self.value
        ]

    @property
    def emoji(self) -> str:
        """
        Returns a single-character symbol indicating the severity, followed by padding spaces.
        They are:
            - ⛔  for CRITICAL
            - ☢  for DANGER
            - ⚠  for WARNING
            - ·   for CAUTION
            -     for NOTE and GOOD (spaces)
        Unfortunately, not all monospace fonts handle these widths correctly.
        Therefore using ljust and rjust probably won't work as expected:
            The radiation and warning signs have Neutral East Asian width.
            The no entry symbol has Ambiguous East Asian width.
            The rest have smaller widths.
        To work around this, hair spaces are appended. But that's not enough.

        Returns:

        """
        return {
            9: Chars.donotenter,
            4: Chars.radiation + Chars.hairspace,
            3: Chars.warning + Chars.hairspace,
            2: Chars.middot + Chars.hairspace * 2,
            1: "\u2007" + Chars.hairspace * 2,
            0: "\u2007" + Chars.hairspace * 2,
        }[self.value]

    @classmethod
    def of(cls, level: Union[Severity, int, str]) -> Severity:
        """
        Returns a Severity from:
            - a Severity instance
            - the name of a Severity (case-insensitive)
            - the name of an Annotation or BatchAnnotation level (case-insensitive)
            - the numerical value of a Severity

        Args:
            level:

        Returns:

        """
        if hasattr(level, "value"):
            # TODO not good, but can't check for isinstance with enum
            level = level.value
        if isinstance(level, str):
            for x in cls:
                if level.upper() == x.name:
                    return x
            return cls.parse(level)
        elif isinstance(level, int):
            for x in cls:
                if level == x.value:
                    return x
            raise XValueError(f"Bad level value {level}")
        raise XTypeError(f"Bad type {type(level)} for {level}")

    @classmethod
    def parse(cls, level: str) -> Severity:
        """
        Parses a 'level' value from Annotations or BatchAnnotations.

        Args:
            level: str:

        Returns:

        Raises:
            LookupFailedError:

        """
        level = level.lower()
        if level == "to_fix":
            return Severity.DANGER
        if level == "9:deleted":
            return Severity.CRITICAL
        for val in Severity:
            if val.name == level or level[0] == str(val.value):
                return val
        raise LookupFailedError(f"Level {level} not recognized")

    @classmethod
    def bad_values(cls) -> Sequence[Severity]:
        """"""
        return [Severity.CAUTION, Severity.WARNING, Severity.DANGER, Severity.CRITICAL]

    @classmethod
    def key_str(cls) -> str:
        """"""
        return Chars.dangled(
            "  ".join([s.name + ":" + s.emoji.strip() for s in Severity.bad_values()])
        )


@dataclass(frozen=True, order=True)
class Concern(metaclass=abc.ABCMeta):
    """
    A result from a quality test on behavioral data on a run (or well).
    Might indicate an issue or potential issue. Refer to its ``severity``.

    """

    run: Runs
    severity: Severity

    @property
    def name(self):
        """ """
        return self.__class__.__name__.replace("Concern", "")

    def as_dict(self) -> Mapping[str, Any]:
        """ """
        raise NotImplementedError()

    def description(self) -> str:
        """ """
        raise NotImplementedError()

    def _main_dict(self) -> Mapping[str, Any]:
        """ """
        return {
            "kind": self.name,
            "severity": self.severity.name,
            "run": self.run,
            "description": self.description(),
        }


@dataclass(frozen=True, order=True)
class LoadConcern(Concern):
    """
    The data could not be loaded at all.
    """

    error: BaseException
    tb: FrameSummary

    def as_dict(self) -> Mapping[str, Any]:
        """ """
        return {**self._main_dict(), "message": str(self.error)}

    def description(self) -> str:
        """ """
        return "Load failed with {self.run.id} / {type(self.error)}"


@dataclass(frozen=True, order=True)
class ImpossibleTimeConcern(Concern):
    """"""

    kind: str
    value: str

    def as_dict(self) -> Mapping[str, Any]:
        """ """
        return {**self._main_dict(), "kind": self.kind, "value": self.value}

    def description(self) -> str:
        """ """
        return f"{self.kind} time is {self.value}"


@dataclass(frozen=True, order=True)
class MissingSensorConcern(Concern):
    """"""

    generation: DataGeneration
    expected: Set[Sensors]
    actual: Set[Sensors]

    @property
    def missing(self) -> Set[Sensors]:
        """"""
        return self.expected - self.actual

    def as_dict(self) -> Mapping[str, Any]:
        return {
            **self._main_dict(),
            "defined": frozenset([s.name for s in self.actual]),
            "missing": frozenset([s.name for s in self.missing]),
        }

    def description(self) -> str:
        if len(self.missing) > 1:
            return f"Missing sensors: {', '.join([s.name for s in self.missing])}"
        elif len(self.missing) == 1:
            return f"Missing sensor: {', '.join([s.name for s in self.missing])}"
        else:
            return "Has all sensors"


@dataclass(frozen=True, order=True)
class WellConcern(Concern):
    """"""

    trash: Mapping[ControlTypes, int]

    @property
    def name(self):
        return "WellConcern"

    def as_dict(self) -> Mapping[str, Any]:
        x = Tools.join_kv(self.trash, ",")
        return {**self._main_dict(), "counts": "-" if len(x) == 0 else x}

    def description(self) -> str:
        if len(self.trash) > 0:
            return "Hazard well(s) present: " + ", ".join(
                k.name + Chars.bracketed("n=" + str(v)) for k, v in self.trash.items()
            )
        else:
            return "No hazard wells"


@dataclass(frozen=True, order=True)
class BatchConcern(Concern):
    """"""

    batch: Batches
    annotation: BatchAnnotations

    def as_dict(self) -> Mapping[str, Any]:
        return {
            **self._main_dict(),
            "id": self.annotation.id,
            "batch": self.batch.id,
            "description": self.annotation.description,
        }

    def description(self) -> str:
        return f"Suspicious batch b{self.batch.id}: '{self.annotation.description}'"


@dataclass(frozen=True, order=True)
class _AnnotationConcern(Concern, metaclass=abc.ABCMeta):
    """"""

    annotation: Annotations

    def as_dict(self) -> Mapping[str, Any]:
        """ """
        return {
            **self._main_dict(),
            "id": self.annotation.id,
            "description": self.annotation.description,
            "datetime_annotated": self.annotation.created,
            "user_annotated": self.annotation.annotator.username,
        }


@dataclass(frozen=True, order=True)
class _ErrorConcern(Concern, metaclass=abc.ABCMeta):
    """"""

    expected: float
    actual: float

    @property
    def raw_diff(self) -> float:
        """"""
        return self.actual - self.expected

    @property
    def raw_error(self) -> float:
        """"""
        return abs(self.raw_diff)

    @property
    def relative_error(self) -> float:
        """"""
        return abs(self.relative_diff)

    @property
    def relative_diff(self) -> float:
        """"""
        if self.expected == 0 or np.isinf(self.expected):
            logger.debug(f"Expected value is {self.expected}. Setting relative_diff=+inf")
            return np.inf
        else:
            return (self.actual - self.expected) / self.expected

    @property
    def log2_diff(self) -> float:
        """"""
        if self.expected == 0 or np.isinf(self.expected):
            logger.debug(f"Expected value is {self.expected}. Setting log2_diff=+inf")
            return np.inf
        elif self.actual == 0 or np.isinf(self.actual):
            logger.debug(f"Actual value is {self.actual}. Setting log2_diff=+inf")
            return np.inf
        else:
            # noinspection PyAttributeOutsideInit
            return np.log2(self.actual) - np.log2(self.expected)

    def as_dict(self) -> Mapping[str, Any]:
        return {
            **self._main_dict(),
            "raw_diff": self.raw_diff,
            "expected": self.expected,
            "actual": self.actual,
            "relative_error": self.relative_error,
            "log2_diff": self.log2_diff,
        }


@dataclass(frozen=True, order=True)
class SensorLengthConcern(_ErrorConcern):
    """"""

    generation: DataGeneration
    sensor: Sensors

    def as_dict(self) -> Mapping[str, Any]:
        return {**super().as_dict(), "sensor": self.sensor.id}

    def description(self) -> str:
        return f"Sensor {self.sensor.name} severity: {self.severity.name.lower()}: {self.expected} → {self.actual}"


@dataclass(frozen=True, order=True)
class TargetTimeConcern(_ErrorConcern):
    """"""

    kind: TargetTimeKind
    annotation: Optional[Annotations]

    @property
    def name(self):
        return self.kind.name.capitalize() + "Sec"

    def as_dict(self) -> Mapping[str, Any]:
        return {**super().as_dict(), "annotation_id": Tools.look(self.annotation, "id")}

    def description(self) -> str:
        diff = Tools.pretty_float(self.log2_diff, 2)
        actual = Tools.pretty_float(self.actual, 3).lstrip("+")  #actual = Tools.pretty_float(self.actual, None).lstrip("+") argument None throws error Sigfigs of None is nonpositive. Same deal next line. -CH
        expected = Tools.pretty_float(self.expected, 3).lstrip("+")
        return "{} is {}× (log₂) off: {} → {}".format(
            self.kind.name.capitalize().ljust(11), diff.ljust(7), expected.ljust(5), actual.ljust(5)
        )


@dataclass(frozen=True, order=True)
class AnnotationConcern(_AnnotationConcern):
    """"""

    def description(self) -> str:
        return (
            "Annotation: "
            + Chars.squoted(self.annotation.name)
            + " "
            + Chars.parened("id=" + str(self.annotation.id))
        )


@dataclass(frozen=True, order=True)
class ToFixConcern(_AnnotationConcern):
    """"""

    fixed_with: Optional[Annotations]

    def description(self) -> str:
        return "{} to_fix {} ({}; id={}): {}".format(
            "Unfixed" if self.fixed_with is None else "Fixed",
            Chars.squoted(self.annotation.name),
            self.annotation.created,
            self.annotation.id,
            self.annotation.description,
        )


@dataclass(frozen=True, order=True)
class NFeaturesConcern(_ErrorConcern):
    """"""

    def as_dict(self) -> Mapping[str, Any]:
        """ """
        return super().as_dict()

    def description(self) -> str:
        """ """
        return f"Feature length: {self.expected} → {self.actual}"


@dataclass(frozen=True, order=True)
class GenerationConcern(Concern):
    """"""

    expected_generations: Set[DataGeneration]
    actual_generation: DataGeneration

    def as_dict(self) -> Mapping[str, Any]:
        return {
            **self._main_dict(),
            "expected_generations": tuple(self.expected_generations),
            "actual_generation": self.actual_generation.name,
        }

    def description(self) -> str:
        return "Generation(s) {} (expected) → {}".format(
            Tools.join(self.expected_generations, ",", attr="name"), self.actual_generation.name
        )


__all__ = [
    "Concern",
    "Severity",
    "LoadConcern",
    "MissingSensorConcern",
    "GenerationConcern",
    "NFeaturesConcern",
    "ToFixConcern",
    "AnnotationConcern",
    "BatchConcern",
    "SensorLengthConcern",
    "TargetTimeConcern",
    "TargetTimeKind",
    "ImpossibleTimeConcern",
    "WellConcern",
    "ConcernFrame",
]

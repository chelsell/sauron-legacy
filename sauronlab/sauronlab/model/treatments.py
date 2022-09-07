from __future__ import annotations

import orjson

from sauronlab.core.core_imports import *


def _o(x: Optional[int]) -> int:
    return 0 if x is None else x


# we can't use dataclass order=True because None is allowed
@abcd.total_ordering
@dataclass(frozen=True, order=False)
class Treatment:
    """
    A drug (batch) and micromolar dose from a ``WellTreatments`` row with pretty printing.
    Two Treatments are equal iff their ordered_compound IDs and doses are equal.
    Less than, greater than, etc. are implemented by comparing, in order:
        1. Compound ID
        2. Batch ID
        3. Dose
    """

    cid: Optional[int]
    bid: int
    bhash: str
    btag: Optional[str]
    dose: float
    # put these last so the ordering is faster: they're the same iff cid is the same
    inchikey: Optional[str]
    chembl: Optional[str]

    def __lt__(self, other):
        if not isinstance(other, Treatment):
            raise TypeError(f"Type {other}; universal equality not supported")
        # we can't use dataclass order=True because None is allowed
        return (_o(self.bid), self.dose) < (_o(other.bid), other.dose)

    @classmethod
    def deserialize(cls, source: str) -> Treatment:
        if isinstance(source, Treatment):
            return source
        if isinstance(source, str):
            data = orjson.loads(source.encode(encoding="utf8"))
        else:
            data = source  # dict
        try:
            return cls(**data)
        except json.JSONDecodeError:
            logger.error(f"Failed to decode '{source}'")
            raise

    def serialize(self) -> str:
        return orjson.dumps(
            dict(
                cid=self.cid,
                bid=self.bid,
                bhash=self.bhash,
                btag=self.btag,
                dose=self.dose,
                inchikey=self.inchikey,
                chembl=self.chembl,
            )
        ).decode(encoding="utf8")

    @classmethod
    def from_well_treatment(cls, condition: WellTreatments) -> Treatment:
        batch = condition.batch
        compound = batch.compound
        return Treatment(
            cid=None if compound is None else compound.id,
            bid=batch.id,
            bhash=batch.lookup_hash,
            inchikey=None if compound is None else compound.inchikey,
            dose=condition.micromolar_dose,
            btag=batch.tag,
            chembl=None if compound is None else compound.chembl,
        )

    @classmethod
    def from_info(cls, batch: Union[Batches, int, str], dose: float) -> Treatment:
        batch = Batches.fetch(batch)
        compound = batch.compound
        return Treatment(
            cid=None if compound is None else compound.id,
            bid=batch.id,
            bhash=batch.lookup_hash,
            inchikey=None if compound is None else compound.inchikey,
            dose=dose,
            btag=batch.tag,
            chembl=None if compound is None else compound.chembl,
        )

    def __str__(self):
        return f"b{self.bid}({self.dose}µM)" if self.bid is not None else "-"

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash((self.bid, self.dose))

    def copy(self) -> Treatment:
        """ """
        return Treatment(
            cid=self.cid,
            bid=self.bid,
            bhash=self.bhash,
            btag=self.btag,
            inchikey=self.inchikey,
            chembl=self.chembl,
            dose=self.dose,
        )


@abcd.total_ordering
class Treatments:
    """
    A wrapper for a list of Treatment objects.
    Any duplicate Treatment instances (determined by Treatment.__eq__ will be removed,
    and the instances will be sorted by Treatment.__lt__.
    This has a __str__ and __repr__ that simplify the Treatment contents.
    """

    def __init__(self, treatments: Collection[Treatment]):
        self.treatments = sorted(set(treatments))

    @classmethod
    def deserialize(cls, source: str) -> Treatments:
        if isinstance(source, Treatments):
            return source
        try:
            data = orjson.loads(source.encode(encoding="utf8"))
            data = [Treatment.deserialize(t) for t in data["treatments"]]
        except json.JSONDecodeError:
            logger.error(f"Failed to decode {source}")
            raise
        return cls(treatments=data)

    def serialize(self) -> str:
        return '{"treatments":[' + ",".join([t.serialize() for t in self.treatments]) + "]}"

    def single(self) -> Treatment:

        return Tools.only(self.treatments, name="treatments")

    def __eq__(self, other):
        return self.treatments == other.treatments

    def __lt__(self, other):
        return tuple(self.treatments) < tuple(other.treatments)

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return self._format(lambda t: "b" + str(t.bid))

    def str_with_hash(self):

        return self._format(lambda t: t.bhash)

    def _format(self, function: Callable[[Treatment], Any]) -> str:
        if self.len() > 0:
            ocs = {function(t): [] for t in self}
            for t in self:
                ocs[function(t)].append(t.dose)
            return " ".join(
                (
                    [
                        "{} ({})".format(
                            oc, ", ".join([Tools.format_micromolar(d) for d in sorted(doses)])
                        )
                        for oc, doses in ocs.items()
                    ]
                )
            )
        else:
            return "-"

    def __repr__(self):
        return str(self)

    def _repr_html_(self):
        return str(self)

    def __hash__(self):
        return hash("".join(str(self.treatments)))

    def __getitem__(self, treatment_index: int) -> Treatment:
        return self.treatments[treatment_index]

    # unfortunate workaround for https://github.com/pandas-dev/pandas/issues/17695
    def len(self) -> int:
        return len(self.treatments)

    def copy(self) -> Treatments:
        return Treatments(self.treatments)

    @classmethod
    def of(cls, treatments: Union[Treatments, Treatment, Collection[Treatment]]) -> Treatments:
        if isinstance(treatments, Treatments):
            return treatments
        elif isinstance(treatments, Treatment):
            return Treatments([treatments])
        elif Tools.is_true_iterable(treatments):
            return Treatments(treatments)
        else:
            raise XTypeError(f"Invalid type {type(treatments)} for treatments {treatments}")


__all__ = ["Treatment", "Treatments"]

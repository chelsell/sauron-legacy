"""
Code for working with the Mandos sub-database.
Can depend on core, calc, and model.
"""
from __future__ import annotations

from sauronlab.core.core_imports import *
from sauronlab.lookups import *


class MandosLookups(LookupTool):
    """"""

    @classmethod
    def predicates(
        cls,
        *wheres: Union[ExpressionsLike, int, str, MandosPredicates],
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
        query = MandosPredicates.select(MandosPredicates, Refs).join(Refs)
        # there is no unique key on name or external (because it depends on ref), so search on either
        # TODO this fails for iterables of mixed types
        wheres = InternalTools.flatten_smart(wheres)
        if len(wheres) > 0 and all((isinstance(w, str) for w in wheres)):
            wheres = (MandosPredicates.name << wheres) | (MandosPredicates.external << wheres)
        return LookupTool._simple(
            MandosPredicates,
            query,
            like,
            regex,
            wheres,
            "id",
            ("external_id", "external"),
            "name",
            ("ref_id", "ref.id"),
            ("ref_name", "ref.name"),
            "kind",
            "created",
        )

    @classmethod
    def objects(
        cls,
        *wheres: Union[ExpressionsLike, int, str, MandosObjects],
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
        # there is no unique key on name or external (because it depends on ref), so search on either
        wheres = InternalTools.flatten_smart(wheres)
        # TODO this fails for iterables of mixed types
        if (
            len(wheres) > 0
            and Tools.is_true_iterable(wheres)
            and all((isinstance(w, str) for w in wheres))
        ):
            wheres = (MandosObjects.name << wheres) | (MandosObjects.external << wheres)
        query = MandosObjects.select(MandosObjects, Refs).join(Refs)
        return LookupTool._simple(
            MandosObjects,
            query,
            like,
            regex,
            wheres,
            "id",
            ("external_id", "external"),
            "name",
            ("ref_id", "ref.id"),
            ("ref_name", "ref.name"),
            "created",
        )


__all__ = ["MandosLookups"]

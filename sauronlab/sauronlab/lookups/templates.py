from sauronlab.core.core_imports import *
from sauronlab.lookups import *


@abcd.external
class TemplateLookups(LookupTool):
    @classmethod
    def treatments(
        cls,
        *wheres: Union[ExpressionsLike, TemplatePlates],
        like: bool = False,
        regex: bool = False,
    ) -> Lookup:
        query = TemplateTreatments.select(TemplateTreatments, TemplatePlates).join(TemplatePlates)
        return TemplateLookups._simple(
            TemplatePlates,
            query,
            like,
            regex,
            wheres,
            "id",
            ("wells", "well_range_expression"),
            ("batch", "batch_expression"),
            ("dose", "dose_expression"),
        )

    @classmethod
    def wells(
        cls,
        *wheres: Union[ExpressionsLike, TemplatePlates],
        like: bool = False,
        regex: bool = False,
    ) -> Lookup:
        query = (
            TemplateWells.select(TemplateWells, TemplatePlates)
            .join(TemplatePlates)
            .switch(TemplateWells)
            .join(ControlTypes, JOIN.LEFT_OUTER)
        )
        df = TemplateLookups._simple(
            TemplatePlates,
            query,
            like,
            regex,
            wheres,
            "id",
            ("wells", "well_range_expression"),
            ("control_type", "control_type.name"),
            ("n", "n_expression"),
            ("variant", "variant_expression"),
            ("age", "age_expression"),
            ("group", "group_expression"),
        )
        # df['n'] = df['n'].map(lambda a: 0 if Tools.is_empty(a) else Tools.iround(a)).astype(int)
        # df['age'] = df['age'].map(lambda a: 0 if Tools.is_empty(a) else Tools.iround(a)).astype(int)
        return df


__all__ = ["TemplateLookups"]

from __future__ import annotations

from sauronlab.core.core_imports import *
from sauronlab.model.features import *


class PlateFrame(UntypedDf):
    """
    A row-by-column DataFrame representing some value in a multiwell plate.
    """

    @classmethod
    def mean(cls, run: RunLike, feature: FeatureType) -> PlateFrame:
        """


        Args:
            run:
            feature:
        """
        return cls.of(run, feature, np.mean)

    @classmethod
    def sum(cls, run: RunLike, feature: FeatureType) -> PlateFrame:
        """


        Args:
            run: RunLike:
            feature: FeatureType:
        """
        return cls.of(run, feature, np.sum)

    @classmethod
    def of(
        cls, run: RunLike, feature: FeatureType, stat: Callable[[np.array], Union[float, str]]
    ) -> PlateFrame:
        """


        Args:
            run:
            feature:
            stat:
        """
        run = Tools.run(run)
        feature = FeatureTypes.of(feature)
        wb1 = Tools.wb1_from_run(run)
        data = {
            wb1.index_to_label(wf.well.well_index): feature.calc(wf, None, None, wf.well)
            for wf in WellFeatures.select(WellFeatures, Wells)
            .join(Wells)
            .where(Wells.run == run)
            .where(WellFeatures.type == feature.valar_feature)
        }
        data = {k: stat(v) for k, v in data.items()}
        data = pd.DataFrame([pd.Series(dict(label=k, value=v)) for k, v in data.items()])
        pat = regex.compile("([A-Za-z]+)([0-9]+)", flags=regex.V1)
        data["row"] = data["label"].map(lambda s: pat.fullmatch(s).group(1))
        data["column"] = data["label"].map(
            lambda s: Tools.strip_off_start(pat.fullmatch(s).group(2), "0")
        )
        data = data.drop("label", axis=1)
        data = data.pivot(index="row", columns="column", values="value")
        return PlateFrame(data)


__all__ = ["PlateFrame"]

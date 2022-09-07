from __future__ import annotations

from typeddfs.df_typing import DfTyping

from sauronlab.core.core_imports import *


class BaseScoreFrame(TypedDf):
    """
    Something that has a label and some kind of score(s).
    Requires at least a column called 'label'.
    """

    @classmethod
    def get_typing(cls) -> DfTyping:
        """ """
        return DfTyping(
            _required_columns=["label", "score"],
            _reserved_columns=[
                "control",
                "well",
                "run",
                "class",
                "lower",
                "upper",
                "spread",
                "pval",
                "is_control",
            ],
        )

    @property
    def value_cols(self) -> Sequence[str]:
        """ """
        z = ["score"]
        for c in ["lower", "upper", "spread", "pval"]:
            if c in self.columns:
                z.append(c)
        return z

    @property
    def ref_cols(self) -> Sequence[str]:
        """ """
        z = []
        for c in ["well", "run"]:
            if c in self.columns:
                z.append(c)
        return z

    @property
    def core_info_cols(self) -> Sequence[str]:
        """ """
        return [c for c in ["label", "control", "class"] if c in self.columns]

    def by_label(self, label: Union[str, Iterable[str]]) -> __qualname__:
        if isinstance(label, str):
            return self.__class__(self[self["label"] == label])
        else:
            return self.__class__(self[self["label"].isin(label)])

    @classmethod
    def simple(cls, classes: pd.Series, scores: pd.Series) -> BaseScoreFrame:
        df = BaseScoreFrame([classes, scores])
        df.columns = ["label", "score"]
        return BaseScoreFrame(df)

    def sort_pretty(self, more_controls: Optional[Set[str]] = None) -> __qualname__:
        """
        Sorts by the names with a natural sort, but putting control names at the top.
        To do this, relies on the name to determine whether a row is a control.
        """
        return self.__class__.retype(
            ValarTools.sort_controls_first(self, "label", more_controls=more_controls)
        )

    def sort_first(self, names: Sequence[str]) -> __qualname__:
        """
        Sorts these names first, keeping the rest in the same order.
        """
        return self.__class__.retype(ValarTools.sort_first(self, self["label"], names))

    @property
    def _constructor_expanddim(self):
        raise ValueError()

    def summarize(
        self,
        ci: Optional[float] = None,
        center_fn=np.mean,
        spread_fn=np.std,
        boot: Optional[int] = None,
    ) -> BaseScoreFrame:
        if ci is not None and (ci < 0 or ci > 1):
            raise ValueError(f"CI is {ci}")
        gb = self.core_info_cols
        selected = self[[*gb, "score"]]
        scores = selected.groupby("label").aggregate(center_fn)
        stds = selected.groupby("label").aggregate(spread_fn)
        if ci is None:
            tops = scores + stds
            bottoms = scores - stds
        elif boot is None:
            tops = selected.groupby(gb).quantile(ci)
            # noinspection PyTypeChecker
            bottoms = selected.groupby(gb).quantile(1 - ci)
        else:

            def get_b(g, c):
                return np.quantile(
                    [
                        float(g.sample(len(g), replace=True).score.aggregate(center_fn))
                        for _ in range(boot)
                    ],
                    c,
                )

            tops = selected.groupby(gb).aggregate(get_b, c=ci)
            bottoms = selected.groupby(gb).aggregate(get_b, c=1 - ci)
        summary = pd.DataFrame(scores)
        summary.columns = ["score"]
        summary["spread"] = stds
        summary["upper"] = tops
        summary["lower"] = bottoms
        # noinspection PyTypeChecker
        return self.__class__(summary.reset_index())

    def set_controls_from_names(self) -> BaseScoreFrame:

        z = self.copy()
        controls = {s.name: s.name for s in ControlTypes.select()}
        z["control"] = z["name"].map(lambda s: controls.get(s))
        # noinspection PyTypeChecker
        return self.__class__(z)

    @classmethod
    def make_into(cls, df: pd.DataFrame, class_name: str):
        class X(cls):
            pass

        X.__name__ = class_name
        return X(df)


class ScoreFrameWithPrediction(BaseScoreFrame):
    """
    A score frame with additional columns 'prediction' and 'score_for_prediction'.
    Supports generating ROC and PR curves.
    """

    @classmethod
    @abcd.overrides
    def required_columns(cls) -> Sequence[str]:
        return ["label", "prediction", "score", "score_for_prediction"]


__all__ = ["BaseScoreFrame", "ScoreFrameWithPrediction"]

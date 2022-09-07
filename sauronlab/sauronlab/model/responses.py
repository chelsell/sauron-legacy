from __future__ import annotations

from typeddfs.df_typing import DfTyping

from sauronlab.core.core_imports import *
from sauronlab.model.metrics import *


class DoseResponseFrame(TypedDf):
    def without_controls(self):

        return self.__class__(self[self["control"].isna()])

    def _scores(self, i: int) -> BaseScoreFrame:
        upper, lower, score = "upper_" + str(i), "lower_" + str(i), "score_" + str(i)
        df = self[["label", "x_value", upper, lower, score]].rename(
            columns={upper: "upper", lower: "lower", score: "score"}
        )
        return BaseScoreFrame.make_into(df, f"ScoreFrame{i}")

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


class DoseResponseFrame1D(DoseResponseFrame):
    """
    A dataframe with some required columns.

    Columns are:
        - 'label': Used to determine Axes; each label is in a different cell in the grid. The labels are used in titles.
        - 'x_value': The x coordinates. You may want to make this logscale.
        - 'x_text': The x position labels.
        - 'upper_1', 'lower_1', 'score_1' (axis on left side, different bands)
    """

    @classmethod
    def get_typing(cls) -> DfTyping:
        return DfTyping(
            _required_columns=["label", "x_value", "x_text", "upper_1", "lower_1", "score_1"]
        )

    def scores(self) -> BaseScoreFrame:
        """
        Returns a BaseScoreFrame of the scores.
        """
        return self._scores(1)


class DoseResponseFrame2D(DoseResponseFrame):
    """
    A dataframe with some required columns.

    The columns are:
        - 'label': Used to determine Axes; each label is in a different cell in the grid. The labels are used in titles.
        - 'x_value': The x coordinates. You may want to make this logscale.
        - 'x_text': The x position labels.
        - 'upper_1', 'lower_1', 'score_1' (axis on left side, different bands)
        - 'upper_2', 'lower_2', 'score_2' (axis on right side, different bands).
    """

    @classmethod
    def get_typing(cls) -> DfTyping:
        return DfTyping(
            _required_columns=[
                "label",
                "x_value",
                "x_text",
                "upper_1",
                "lower_1",
                "score_1",
                "upper_2",
                "lower_2",
                "score_2",
            ]
        )

    def scores(self, i: int) -> BaseScoreFrame:
        """
        Returns a BaseScoreFrame of the scores for just one 'axis'.

        This is usually 1 or 2 to denote negative and positive controls, respectively.
        """
        return self._scores(i)


__all__ = ["DoseResponseFrame", "DoseResponseFrame1D", "DoseResponseFrame2D"]

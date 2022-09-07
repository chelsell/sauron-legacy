from __future__ import annotations

from matplotlib.figure import Figure
from typeddfs.df_typing import DfTyping

from sauronlab.core.core_imports import *
from sauronlab.model.metrics import *
from sauronlab.viz.accuracy_plots import *


class AccuracyCountFrame(BaseScoreFrame):
    """ """

    pass


class AccuracyFrame(ScoreFrameWithPrediction):
    """
    Has columns 'label', 'score', 'prediction', and 'score_for_prediction', with one row per prediction.
    """

    @classmethod
    def get_typing(cls) -> DfTyping:
        return DfTyping(_required_columns=["label", "prediction", "score", "score_for_prediction"])

    def counts(self) -> AccuracyCountFrame:
        """"""
        df = self.copy()
        df["score"] = df["label"] == df["prediction"]
        df = self.groupby("label").sum()[["score"]]
        return AccuracyCountFrame(AccuracyCountFrame(df.reset_index()))

    def means(self) -> AccuracyCountFrame:
        """"""
        df = self.copy()
        df["score"] = df["label"] == df["prediction"]
        df = self.groupby("label").mean()[["score"]] * 100.0
        return AccuracyCountFrame(AccuracyCountFrame(df.reset_index()))

    def with_label(self, label: Union[str, Iterable[str]]) -> AccuracyFrame:
        """


        Args:
            label:

        Returns:

        """
        if isinstance(label, str):
            return self.__class__.retype(self[self["label"] == label])
        else:
            return self.__class__.retype(self[self["label"].isin(label)])

    def rocc(self, control_label: str) -> Figure:
        """


        Args:
            control_label: str:

        Returns:

        """
        data = self.rocs(control_label)
        return MetricPlotter(MetricInfo.roc()).plot(data)

    def prc(self, control_label: str) -> Figure:
        """


        Args:
            control_label: str:

        Returns:

        """
        data = self.prs(control_label)
        return MetricPlotter(MetricInfo.pr()).plot(data)

    def swarm(self, renamer: Optional[Callable[[str], str]] = None) -> Figure:
        """
        Plots a swarm plot with the class labels on the x-axis and the probability on the y-axis.

        Args:
            renamer: A function mapping class labels to more human-friendly class labels

        Returns:
            A Matplotlib Figure

        """
        return AccuracyPlotter("swarm").plot(self, renamer=renamer)

    def violin(self, renamer: Optional[Callable[[str], str]] = None) -> Figure:
        """
        Plots a violin plot with the class labels on the x-axis and the probability on the y-axis.

        Args:
            renamer: A function mapping class labels to more human-friendly class labels

        Returns:
            A Matplotlib Figure

        """
        return AccuracyPlotter("violin").plot(self, renamer=renamer)

    def bar(
        self, renamer: Optional[Callable[[str], str]] = None, ci: float = 0.95, boot: int = 1000
    ) -> Figure:
        """
        Plots a bar plot with the class labels on the x-axis and the average probability on the y-axis.

        Args:
            renamer: A function mapping class labels to more human-friendly class labels
            ci: Confidence interval 0.0-1.0
            boot: Number of bootstarp samples

        Returns:
          A Matplotlib Figure

        """
        return AccuracyPlotter("bar").plot(
            self.summarize(ci=ci, center_fn=np.median, boot=boot), renamer=renamer
        )

    def boot_mean(self, b: int, q: float = 0.95) -> BaseScoreFrame:
        """
        Calculates a confidence interval of the mean from bootstrap over the wells (single rows).

        Args:
            b: The number of bootstrap samples
            q: The high quantile, between 0 and 1.

        Returns:
            A DataFrame with columns 'label', 'lower', and 'upper'.

        """
        data = []
        for repeat in range(b):
            samples = self.sample(len(self), replace=True)
            data.append(samples.groupby("label")[["score"]].mean().reset_index())
        upper = (
            AccuracyFrame(pd.concat(data))
            .groupby("label")
            .quantile(q)
            .rename(columns={"label": "upper"})["upper"],
        )
        lower = (
            AccuracyFrame(pd.concat(data))
            .groupby("label")
            .quantile(1 - q)
            .rename(columns={"label": "lower"})["lower"]
        )
        return BaseScoreFrame(pd.merge(upper, lower, left_index=True, right_index=True))


__all__ = ["AccuracyFrame"]

from __future__ import annotations

from dataclasses import dataclass

import sklearn.metrics as skmetrics
from statsmodels.nonparametric.kde import KDEUnivariate
from typeddfs.df_typing import DfTyping

from sauronlab.core.core_imports import *


class StatTools:
    """"""

    @classmethod
    def kde(
        cls, a: np.array, kernel: str = "gau", bw: str = "normal_reference"
    ) -> Tup[np.array, np.array]:
        """
        Calculates univariate KDE with statsmodel.
        (This function turned into a thin wrapper around statsmodel.)
        Note that scipy uses statsmodel for KDE if it's available. Otherwise, it silently falls back to scipy. That's clearly hazardous.

        Args:
            a: np.array:
            kernel:
            bw:

        Returns:

        """
        if isinstance(a, pd.Series):
            a = a.values
        dens = KDEUnivariate(a)
        dens.fit(kernel=kernel, bw=bw)
        return dens.support, dens.density


@dataclass(frozen=True, repr=True)
class MetricInfo:
    """A type of 2D metric such as ROC or Precision-Recall."""

    name: str
    score: str
    false: str
    true: str

    @classmethod
    def roc(cls):
        """ """
        return MetricInfo("ROC", "AUC (%)", "FPR (%)", "TPR (%)")

    @classmethod
    def pr(cls):
        """"""
        return MetricInfo(
            "Precision" + Chars.en + "Recall",
            "average precision (%)",
            "precision (%)",
            "recall (%)",
        )


@dataclass(frozen=True, repr=True)
class MetricData:
    """
    Typically either ROC or Precision-Recall curves.
    """

    label: str
    control: Optional[str]
    score: float
    false: Sequence[float]
    true: Sequence[float]

    def __post_init__(self):
        if len(self.false) != len(self.true):
            raise LengthMismatchError(
                f"FPR has length {len(self.false)} but TPR has length {len(self.true)}"
            )

    @classmethod
    def roc(
        cls, label: str, control: Optional[str], true: Sequence[bool], scores: Sequence[float]
    ) -> MetricData:
        """


        Args:
            label: str:
            control: Optional[str]:
            true: Sequence[bool]:
            scores: Sequence[float]:

        Returns:

        """
        auc = skmetrics.roc_auc_score(true, scores)
        fpr, tpr, thresholds = skmetrics.roc_curve(true, scores)
        return MetricData(label, control, auc * 100.0, fpr * 100.0, tpr * 100.0)

    @classmethod
    def pr(
        cls, label: str, control: Optional[str], true: Sequence[bool], scores: Sequence[float]
    ) -> MetricData:
        """


        Args:
            label: str:
            control: Optional[str]:
            true: Sequence[bool]:
            scores: Sequence[float]:

        Returns:

        """
        score = skmetrics.average_precision_score(true, scores)
        precision, recall, thresholds = skmetrics.precision_recall_curve(true, scores)
        return MetricData(label, control, score * 100.0, precision * 100.0, recall * 100.0)


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
        """


        Args:
            label:

        """
        if isinstance(label, str):
            return self.__class__(self[self["label"] == label])
        else:
            return self.__class__(self[self["label"].isin(label)])

    @classmethod
    def simple(cls, classes: pd.Series, scores: pd.Series) -> BaseScoreFrame:
        """


        Args:
            classes: pd.Series:
            scores: pd.Series:

        """
        df = BaseScoreFrame([classes, scores])
        df.columns = ["label", "score"]
        return BaseScoreFrame(df)

    def sort_pretty(self, more_controls: Optional[Set[str]] = None) -> __qualname__:
        """
        Sorts by the names with a natural sort, but putting control names at the top.
        To do this, relies on the name to determine whether a row is a control.

        Args:
            more_controls: Optional[Set[str]]:  (Default value = None)

        """
        return self.__class__.retype(
            ValarTools.sort_controls_first(self, "label", more_controls=more_controls)
        )

    def sort_first(self, names: Sequence[str]) -> __qualname__:
        """
        Sorts these names first, keeping the rest in the same order.

        Args:
            names: Sequence[str]:

        """
        return self.__class__.retype(ValarTools.sort_first(self, self["label"], names))

    @property
    def _constructor_expanddim(self):
        """ """
        raise ValueError()

    def summarize(
        self,
        ci: Optional[float] = None,
        center_fn=np.mean,
        spread_fn=np.std,
        boot: Optional[int] = None,
    ) -> BaseScoreFrame:
        """


        Args:
            ci:
            center_fn:  (Default value = np.mean)
            spread_fn:  (Default value = np.std)
            boot:

        Returns:

        """
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
        """"""
        z = self.copy()
        controls = {s.name: s.name for s in ControlTypes.select()}
        z["control"] = z["name"].map(lambda s: controls.get(s))
        # noinspection PyTypeChecker
        return self.__class__(z)

    @classmethod
    def make_into(cls, df: pd.DataFrame, class_name: str):
        """


        Args:
            df: pd.DataFrame:
            class_name: str:

        Returns:

        """

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

    def rocs(self, control_label: str) -> Sequence[MetricData]:
        """


        Args:
            control_label: str:

        Returns:

        """
        return self._curves(control_label, MetricInfo.roc(), MetricData.roc)

    def prs(self, control_label: str) -> Sequence[MetricData]:
        """


        Args:
            control_label: str:

        Returns:

        """
        return self._curves(control_label, MetricInfo.pr(), MetricData.pr)

    def _curves(self, control_label: str, info, clazz):
        __a, __b = self.__ab(control_label)
        curves = []
        for label in self["label"].unique():
            bylabel = self.by_label([label, control_label])
            labels = set(bylabel["label"].unique())
            if len(labels) == 2 and label != __a and label != __b:
                curves.append(bylabel._curve(control_label, info, clazz))
            elif label != control_label and label != __a and label != __b:
                logger.caution(f"Skipping {control_label} vs {label} with {len(labels)} labels")
        if __a is not None and __b is not None:
            curves.append(self._curveab(control_label, info, clazz))
        elif __a is not None:
            logger.warning(f"{control_label}__a exists but {control_label}__b does not. Ignoring.")
        elif __b is not None:
            logger.warning(f"{control_label}__b exists but {control_label}__a does not. Ignoring.")
        return curves

    def _curveab(self, control_label: str, info, clazz):
        logger.caution(f"Transparently handling __a and __b for {control_label} in curves")
        __a, __b = self.__ab(control_label)
        bylabel = self.by_label([__a, __b])
        # TODO _false_and_score
        truea, scorea = bylabel._true_and_score(control_label + "__a")
        trueb, scoreb = bylabel._true_and_score(control_label + "__b")
        true, score = list(truea) + list(trueb), list(scorea) + list(scoreb)
        data = clazz(control_label, control_label, true, score)
        logger.trace(
            f"{info.score} for {control_label} against itself is {Tools.round_to_sigfigs(data.score, 3)}%"
        )
        return data

    def __ab(self, control_label: str):
        __a = control_label + "__a" if control_label + "__a" in self["label"].unique() else None
        __b = control_label + "__b" if control_label + "__b" in self["label"].unique() else None
        return __a, __b

    def _curve(self, control_label: str, info, clazz):
        # the reason for taking the control label rather than the treatment is simple:
        # You can generally call AccuracyFramey.roc('solvent (-)') for any treatment.
        # You don't have to know which treatment it is.
        labels = set(self["label"].unique())
        other_label = [ell for ell in labels if ell != control_label][0]
        true, score = self._true_and_score(control_label)
        data = clazz(other_label, None, true, score)
        logger.trace(
            f"{info.score} for {other_label} against {control_label} is {Tools.round_to_sigfigs(data.score, 3)}%"
        )
        return data

    def _true_and_score(self, control_label: str):
        true: Sequence[bool] = (self["label"] != control_label).astype(int).values
        score = [
            (s if guess != control_label else 100 - s) / 100.0
            for s, actually, guess in zip(self["score_for_prediction"], true, self["prediction"])
        ]
        return true, score


@dataclass(frozen=True)
class KdeData:
    """
    Kernel density estimation data.
    """

    samples: np.array
    support: Sequence[float]
    density: Sequence[float]
    params: Optional[Mapping[str, Any]]

    def density_df(
        self, support_start: Optional[float] = None, support_end: Optional[float] = None
    ) -> UntypedDf:
        """


        Args:
            support_start:
            support_end:

        Returns:

        """
        df = UntypedDf({"support": self.support, "density": self.density})
        if support_start is not None:
            df = df[df["support"] >= support_start]
        if support_end is not None:
            df = df[df["support"] <= support_end]
        return df

    @classmethod
    def from_scores(cls, df: BaseScoreFrame, **kwargs) -> KdeData:
        """


        Args:
            df:
            **kwargs:

        Returns:

        """
        return cls.from_samples(df["score"], **kwargs)

    @classmethod
    def from_samples(cls, samples: Sequence[float], **kwargs) -> KdeData:
        """


        Args:
            samples:
            **kwargs:

        Returns:

        """
        support, density = StatTools.kde(samples, **kwargs)
        return KdeData(samples, support, density, params=kwargs)


__all__ = ["MetricData", "MetricInfo", "BaseScoreFrame", "ScoreFrameWithPrediction", "KdeData"]

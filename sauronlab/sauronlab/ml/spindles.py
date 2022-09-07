from __future__ import annotations

from matplotlib.figure import Figure

from sauronlab.core.core_imports import *
from sauronlab.model.metrics import *
from sauronlab.model.responses import *
from sauronlab.viz.accuracy_plots import *


class SummarizedSpindleFrame(BaseScoreFrame):
    """"""

    def to_dose_response(
        self, axis: int, splitter: Callable[[str], Tup[str, str]] = Tools.split_species_micromolar
    ) -> DoseResponseFrame1D:
        """


        Args:
            axis:
            splitter:

        Returns:

        """
        summary = self.copy()
        all_controls = {s.name: s.name for s in ControlTypes.select()}
        all_controls.update({s: s.name for s in ControlTypes.select()})
        split = [splitter(name) for name in summary["label"]]
        summary["label"] = [i[0] for i in split]
        summary["x_raw"] = [
            np.nan if Tools.is_probable_null(s) else s for s in [k[1] for k in split]
        ]
        if all(summary["x_raw"].isnull()):
            logger.caution("All response x values are null")
        del split  # we're going to sort, so don't use this!!
        summary = summary.sort_values(["label", "x_raw"])
        summary["control"] = summary["label"].map(all_controls.get)
        summary["x_text"] = summary["x_raw"].map(
            lambda s: np.nan if Tools.is_probable_null(s) else Tools.round_to_sigfigs(s, 3)
        )
        summary["x_value"] = summary.groupby("label").cumcount()
        summary["upper_" + str(axis)] = summary["upper"]
        summary["lower_" + str(axis)] = summary["lower"]
        summary["score_" + str(axis)] = summary["score"]
        return DoseResponseFrame1D(
            summary[
                [
                    "label",
                    "control",
                    "x_raw",
                    "x_text",
                    "x_value",
                    "upper_" + str(axis),
                    "lower_" + str(axis),
                    "score_" + str(axis),
                ]
            ]
        )


class SpindleFrame(ScoreFrameWithPrediction):
    """
    Summarized results of many case-control comparisons for 1 or more controls.
    Each row is the result a binary (case-control) classifier on a single well.

    The control label is in the column 'target',
    and the case label is in the column 'source' (as in arrows).
    The name source is intentionally weird to **avoid misinterpretation**:
    Target and source were the two labels compared between.
    _Label_, on the other hand, is different.

    The rows derived from a single case-control comparison between labels 'optovin' and 'solvent (-)'
    will **all** have target 'solvent (-)' and source 'optovin'.
    But the 'label' will be **either** 'solvent (-)' **or** 'optovin, according to what the well actually was.

    The label will also be different from the source when using MultiTrainers' ``split_same=True``.
    The labels were remapped when doing the comparison between a control and itself,
    randomly partitioning the wells into __a and __b (suffixes). Then the label will contain __a or __b,
    while both the target and source will be the control name.

    **For example:**
        - source == 'solvent (-)'
        - target == 'solvent (-)'
        - label  == 'solvent (-)__a' (or 'solvent (-)__b')

    Using this distinction, if you simply average scores by label, you'll mix the desired scores.
    For ROC curves, you'll need the true labels in the 'label' column.
    See ``source_to_label``, which returns a copy with the labels replaced with the source.
    (Don't use this by habit -- only use it when needed, because it might cause confusion later.)

    Supports generating dose-response curves by splitting label names into (treatment, dose) pairs.
    The dose can actually anything, such as number of fish, datetime run, or binding affinity to some target.
    See ``to_1d_dose_response`` and ``to_2d_dose_response``.

    Also supports generating ROC and precision-recall curves.

    Here are all of the columns:
        - target               (target control in comparison)
        - source               (target non-control label in comparison)
        - repeat               (the ith repeat of the comparison; used when wells were subsampled repeatedly)
        - well                 (well ID)
        - run                  (run ID)
        - label                (the true label of the well)
        - prediction           (the predicted label)
        - score                (probability for the true label)

    """

    @classmethod
    @abcd.overrides
    def required_columns(cls) -> Sequence[str]:
        """"""
        return ["label", "target", "repeat", "score", "prediction", "score_for_prediction"]

    def by_target(self, target: Union[str, int, ControlTypes]) -> SpindleFrame:
        """


        Args:
            target:

        Returns:

        """
        target = ControlTypes.fetch(target) if not isinstance(target, str) else target
        # noinspection PyTypeChecker
        return self.__class__(self[self["target"] == target])

    def by_source(self, source: str) -> SpindleFrame:
        """


        Args:
            source: str:

        Returns:

        """
        # noinspection PyTypeChecker
        return self.__class__(self[self["source"] == source])

    def source_to_label(self, source: str) -> SpindleFrame:
        """


        Args:
            source: str:

        Returns:

        """
        # noinspection PyTypeChecker
        return self.__class__(self.drop("label", axis=1).rename(columns={"source": "label"}))

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

    def to_2d_dose_response(
        self,
        negative_control: Union[int, str, ControlTypes] = "solvent (-)",
        positive_control: Union[int, str, ControlTypes] = "killed (+)",
        splitter: Callable[
            [str], Tup[str, Union[str, float, int, None]]
        ] = Tools.split_species_micromolar,
        ci: Optional[float] = 0.8,
        center_fn=np.median,
        spread_fn=np.std,
        boot: Optional[int] = None,
    ) -> DoseResponseFrame2D:
        """
        Summarize this SpindleFrame, averaging over replicate (source, target) pairs with and:
            - calculate 4 summary statistics for each pair: 'lower', 'middle', 'upper', and 'spread',
                where middle is generally the median, lower and upper are the bounds of a confidence interval,
                and spread is the standard deviation.
            - split the labels into (treatment, dose) pairs,
                where dose can really be anything, such as number of animals or datetime run
            - make 'lower', 'middle', 'upper', and 'spread' columns for a positive control and a negative control:
                negative => lower_1, etc; positive => lower_2, etc

        Args:
            negative_control: The name of the negative control (not checked), or a ControlTypes-lookupable object
            positive_control: The name of the positive control (not checked), or a ControlTypes-lookupable object
            splitter: A function that splits any label into a (label, dose-or-None) pair.
            ci: 0.0-1.0, the confidence interval
            center_fn: A function generating the middle_1 and middle_2 columns (Default value = np.median)
            spread_fn: A function generating the spread_1 and spread_2 columns (Default value = np.std)
            boot: If non-null, calculates a CI by bootstrap with this number of samples

        Returns:
            A DoseResponseFrame2D frame.

        """
        x = self.to_1d_dose_response(
            negative_control,
            splitter=splitter,
            center_fn=center_fn,
            spread_fn=spread_fn,
            ci=ci,
            boot=boot,
            axis=1,
        )
        y = self.to_1d_dose_response(
            positive_control,
            splitter=splitter,
            center_fn=center_fn,
            spread_fn=spread_fn,
            ci=ci,
            boot=boot,
            axis=2,
        )
        drs = DoseResponseFrame2D(
            pd.merge(x, y, on=["label", "control", "x_raw", "x_text", "x_value"])
        )
        return DoseResponseFrame2D(drs)

    def to_1d_dose_response(
        self,
        control: Union[int, str, ControlTypes] = "solvent (-)",
        splitter: Callable[[str], Tup[str, str]] = Tools.split_species_micromolar,
        ci: Optional[float] = 0.8,
        center_fn=np.median,
        spread_fn=np.std,
        boot: Optional[int] = None,
        axis: int = 1,
    ) -> DoseResponseFrame1D:
        """
        Similar to ``to_2d_dose_response``; see that function.
        This just considers only 1 control type.

        Args:
            control:
            splitter:
            ci:
            center_fn:  (Default value = np.median)
            spread_fn:  (Default value = np.std)
            boot:
            axis:

        Returns:

        """
        if ci is None and boot is not None:
            raise XTypeError(f"CI is None but boot is {boot}")
        control = control if isinstance(control, str) else ControlTypes.fetch(control).name
        if control not in self["target"].unique():
            raise XValueError(f"This spindle does not have a control named '{control}'")
        x = SpindleFrame(self[self["target"] == control])
        summary = x.summarize(ci, center_fn=center_fn, spread_fn=spread_fn, boot=boot)
        summary = SummarizedSpindleFrame(summary)
        drs = DoseResponseFrame1D(
            summary.to_dose_response(axis, splitter=splitter).dropna(how="all", axis="columns")
        )
        for c in drs.columns:
            if c.endswith("1") or c.endswith("2"):
                drs[c] = drs[c].astype(np.float32)
        return DoseResponseFrame1D(drs)


__all__ = [
    "DoseResponseFrame",
    "DoseResponseFrame1D",
    "DoseResponseFrame2D",
    "SummarizedSpindleFrame",
    "SpindleFrame",
]

from __future__ import annotations

from dataclasses import dataclass

from sauronlab.core.core_imports import *
from sauronlab.model.metrics import *
from sauronlab.viz._internal_viz import *
from sauronlab.viz.figures import FigureTools


@dataclass(frozen=True)
class MetricPlotter:
    """
    Plots ROC and Precision-Recall curves as 2D line plots.
    """

    metric_info: MetricInfo

    def plot(self, data: Sequence[MetricData]) -> Figure:
        """


        Args:
            data: Sequence[MetricData]:

        Returns:

        """
        figure = plt.figure()
        ax = figure.add_subplot(1, 1, 1)
        colors = InternalVizTools.assign_colors_x(
            [d.label for d in data], [d.control for d in data]
        )
        for value, color in zip(data, colors):
            # print(type(value.false), type(value.true), type(value.label), type(color))
            label = "" if value.label is None else FigureTools.fix_labels(value.label)
            ax.plot(value.false, value.true, label=label, color=color, alpha=0.8, clip_on=False)
        ax.set_xlabel(FigureTools.fix_labels(self.metric_info.false))
        ax.set_ylabel(FigureTools.fix_labels(self.metric_info.true))
        pad = 0
        ax.set_xlim(-pad, 100)
        # scale to get a similar % of padding per axis, rather than raw amount
        ax.set_ylim(0, 100 + pad * sauronlab_rc.width / sauronlab_rc.height)
        # we already know we won't use the lower right
        FigureTools.manual_legend(ax, [d.label for d in data], colors)
        ax.set_aspect("equal", adjustable="box")
        return figure


@enum.unique
class AccuracyPlotStyle(enum.Enum):
    """"""

    SWARM = 1
    VIOLIN = 2
    BAR = 3

    @classmethod
    def of(cls, s: Union[AccuracyPlotStyle, str]) -> AccuracyPlotStyle:
        """


        Args:
            s:

        Returns:

        """
        if isinstance(s, AccuracyPlotStyle):
            return s
        try:
            return AccuracyPlotStyle[s.upper()]
        except KeyError:
            raise XValueError(f"No style {s}")


@abcd.auto_eq()
@abcd.auto_repr_str()
class AccuracyPlotter(KvrcPlotting):
    """"""

    def __init__(
        self,
        style: Union[str, AccuracyPlotStyle],
        y_bounds: Tup[float, float] = (0, 100),
        y_label: str = "accuracy (%)",
        extra_params: Optional[Mapping[str, Any]] = None,
    ):
        """
        Plots a graph of accuracy or another score on the y-axis, and labels on the x-axis.
        Can perform a bar, swarm, or violin plot.
        If there are bounds present in the BaseScoreFrame plotted, will happily plot error bars for bar plots.
        See ``AccuracyPlotter.plot?`` for more info.

        Args:
            style: Can be 'swarm', 'violin', or 'bar'
            y_bounds:
            y_label:
            extra_params:
        """
        self._style = AccuracyPlotStyle.of(style)
        self._y_bounds = y_bounds
        self._y_label = y_label
        self._extra_params = {} if extra_params is None else extra_params

    def plot(
        self,
        df: BaseScoreFrame,
        renamer: Union[None, Mapping[str, str], Callable[[str], str]] = None,
    ) -> Figure:
        """
        TODO This is way too complex
        Note that ``df`` should have replicate rows (with the same label but different scores) to plot a violin or swarm.
        But for barplots, it should have columns 'upper' and 'lower' for upper and lower bounds if you want error bars.
        If those columns are not present, no error bars will be shown.
        (Plotting code will never do calculations such as determining bounds from replicates -- you need to that yourself.)
        If ``df`` has column 'control', that will be used to inform colors.
        If it has a column 'class', that will be used to group labels and give them the same color.
        Otherwise pretty straightforward.
        It relies on sauronlab_rc/KVRC params beginning with 'acc_'; ex: ``acc_bar_edge_width`` and ``acc_point_size``.

        Args:
            df: Any BaseScoreFrame (DataFrame) with columns (at least) 'label' and 'score'
            renamer: Alter the labels for display. Ex, by setting ``renamer={'optovin': 'opto'}``.

        Returns:
            The Figure

        """
        if isinstance(renamer, Mapping):
            renamer = lambda s: renamer[s]
        has_repeats = defaultdict(lambda: 0)
        for label in df["label"]:
            has_repeats[label] += 1
        has_repeats = max(has_repeats.values()) > 1
        labels = df["label"]
        controls = df["control"] if "control" in df.columns else None
        scores = df["score"]
        hue = df["class"].tolist() if "class" in df.columns else None
        lower = df["lower"] if "lower" in df.columns else None
        upper = df["upper"] if "upper" in df.columns else None
        x_labels = labels if renamer is None else [renamer(v) for v in labels]
        fig, ax = plt.subplots()
        ################################################################################################################
        # IT'S __NOT__ A BARPLOT
        ################################################################################################################
        if self._style is AccuracyPlotStyle.SWARM:
            color = sauronlab_rc.acc_point_color
            # seaborn sets s=5 instead of lines.markersize
            # AND it expects the sqrt
            import seaborn as sns

            ax = sns.swarmplot(
                x_labels,
                scores,
                color=color,
                s=np.sqrt(sauronlab_rc.acc_point_size),
                dodge=True,
                ax=ax,
                **self._extra_params,
            )
        elif self._style is AccuracyPlotStyle.VIOLIN:
            import seaborn as sns

            ax = sns.violinplot(
                x_labels,
                scores,
                color=color,
                inner="point",
                fliersize=0,
                ax=ax,
                **self._extra_params,
            )
        ################################################################################################################
        # IT'S A BARPLOT
        ################################################################################################################
        elif self._style is AccuracyPlotStyle.BAR:
            fill_color, edge_color, err_color = (
                sauronlab_rc.acc_bar_color,
                sauronlab_rc.acc_bar_edge_color,
                sauronlab_rc.acc_error_color,
            )
            bars = ax.bar(
                x_labels,
                scores,
                yerr=(scores - lower, upper - scores),
                color=fill_color,
                edgecolor=edge_color,
                lw=sauronlab_rc.acc_bar_edge_width,
                error_kw=sauronlab_rc.acc_error_kwargs,
                **self._extra_params,
            )
            # And now correct the colors, sizes, and bounds
            if hue is not None:
                if controls is None:
                    colors = InternalVizTools.assign_colors(labels)
                else:
                    colors = InternalVizTools.assign_colors_x(labels, controls)
                for label, color, bar in Tools.zip_list(labels, colors, bars):
                    bar.set_color(color)
            ax.set_xticklabels(FigureTools.fix_labels(labels))
            ax.set_xlim(-0.5, len(set(labels)) - 0.5)
            self._change_width(ax, sauronlab_rc.acc_bar_width_fraction)
        return self._fix(x_labels, ax)

    def _change_width(self, ax, new_value):
        """


        Args:
            ax:
            new_value:

        Returns:

        """
        for patch in ax.patches:
            current_width = patch.get_width()
            diff = current_width - new_value
            patch.set_width(new_value)
            patch.set_x(patch.get_x() + diff * 0.5)  # recenter

    def _fix(self, x_labels, ax) -> Figure:
        """


        Args:
            x_labels:
            ax:

        Returns:

        """
        ax.set_ylabel(FigureTools.fix_labels(self._y_label))
        ax.set_xticklabels(
            FigureTools.fix_labels(ax.get_xticklabels()), rotation=sauronlab_rc.acc_x_tick_rotation
        )
        ax.set_ylim(*self._y_bounds)
        ax.set_ylabel(ax.get_ylabel())
        ax.set_xlabel("")
        ax.set_xlabel(ax.get_xlabel())
        return ax.get_figure()


class AccuracyDistPlotter(KvrcPlotting):
    """
    Plots a Kernel Density Estimate with seaborn for probability (or score) across compounds.
    Chooses decent defaults. Change the axis/figure after if needed.

    """

    def __init__(
        self,
        sig_x: Optional[float] = None,
        sig_text: Optional[str] = None,
        treatment_label: str = "treatment",
        negative_label: str = "negative",
        positive_label="positive",
    ):
        self.sig_x, self.sig_text = sig_x, sig_text
        self.treatment_label, self.negative_label, self.positive_label = (
            treatment_label,
            negative_label,
            positive_label,
        )

    def plot(
        self,
        treatments: KdeData,
        negatives: Optional[KdeData] = None,
        positives: Optional[KdeData] = None,
    ) -> Figure:
        """
        Each argument is a 2-tuple of (support, density).

        Args:
            treatments: Support and density for non-controls, typically covered in black.
            negatives: Support and density for negative controls
            positives: Support and density for positive controls

        Returns:

        """
        figure = plt.figure()
        ax = figure.add_subplot(1, 1, 1)
        # args = dict(hist=False, kde=True, rug=False, bins=self.n_bins, ax=ax)
        if negatives is not None:
            ax.plot(
                negatives.support,
                negatives.density,
                alpha=sauronlab_rc.dist_control_alpha,
                color=sauronlab_rc.dist_negative_control_color,
                label=FigureTools.fix_labels(self.negative_label),
            )
        if positives is not None:
            ax.plot(
                positives.support,
                positives.density,
                alpha=sauronlab_rc.dist_control_alpha,
                color=sauronlab_rc.dist_positive_control_color,
                label=FigureTools.fix_labels(self.positive_label),
            )
        ax.plot(
            treatments.support,
            treatments.density,
            alpha=sauronlab_rc.dist_treatment_alpha,
            color=sauronlab_rc.dist_treatment_color,
            label=FigureTools.fix_labels(self.treatment_label),
        )
        # TODO this shouldn't be needed! why does matplotlib truncate?
        ax.set_ylim(0, 1.000001 * ax.get_ylim()[1])
        ax.set_xlim(0, 100)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.set_yticks([])
        ax.set_xlabel("accuracy (%)")
        ax.set_ylabel("N compounds")
        if self.sig_x is not None:
            self._add_sig_line(ax, self.sig_x, self.sig_text)
        ax.legend(loc="upper left")  # typically no density below ~25%
        return figure

    def _add_sig_line(
        self,
        ax: Axes,
        x: float,
        label: Optional[str],
        textx: Optional[float] = None,
        texty: Optional[float] = None,
        text_kwargs=None,
    ) -> Axes:
        """
        Adds a line indicating a significance threshold at x-value ``x``.
        If you have multiple labels, use line breaks (\n) in ``label``.

        """
        ax.axvline(
            x=x,
            c=sauronlab_rc.dist_sig_line_color,
            lw=sauronlab_rc.dist_sig_line_width,
            linestyle=sauronlab_rc.dist_sig_line_style,
        )
        if label is not None:
            text_kwargs = {} if text_kwargs is None else text_kwargs
            # TODO depends on font size?
            textx = x + 0.02 * (ax.get_xlim()[1] - ax.get_xlim()[0]) if textx is None else textx
            texty = (
                ax.get_ylim()[1] - 0.02 * (ax.get_ylim()[1] - ax.get_ylim()[0])
                if texty is None
                else texty
            )
            FigureTools.add_note_data_coords(
                ax,
                textx,
                texty,
                label,
                horizontalalignment="left",
                verticalalignment="top",
                **text_kwargs,
            )
        return ax


__all__ = ["AccuracyPlotter", "AccuracyPlotStyle", "MetricPlotter", "AccuracyDistPlotter"]

from __future__ import annotations

from dataclasses import dataclass

from sauronlab.core.core_imports import *
from sauronlab.model.metrics import *
from sauronlab.viz._internal_viz import *
from sauronlab.viz.figures import FigureTools


class AccuracyPlotStyle(CleverEnum):

    SWARM = 1
    VIOLIN = 2
    BAR = 3


@abcd.auto_eq()
@abcd.auto_repr_str()
class AccuracyPlotter(KvrcPlotting):
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
        for patch in ax.patches:
            current_width = patch.get_width()
            diff = current_width - new_value
            patch.set_width(new_value)
            patch.set_x(patch.get_x() + diff * 0.5)  # recenter

    def _fix(self, x_labels, ax) -> Figure:
        ax.set_ylabel(FigureTools.fix_labels(self._y_label))
        ax.set_xticklabels(
            FigureTools.fix_labels(ax.get_xticklabels()), rotation=sauronlab_rc.acc_x_tick_rotation
        )
        ax.set_ylim(*self._y_bounds)
        ax.set_ylabel(ax.get_ylabel())
        ax.set_xlabel("")
        ax.set_xlabel(ax.get_xlabel())
        return ax.get_figure()


__all__ = ["AccuracyPlotter", "AccuracyPlotStyle"]

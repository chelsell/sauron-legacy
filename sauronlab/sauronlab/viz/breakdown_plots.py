"""
Plotting code for distributions by class,
especially for info from Mandos.
"""
from dataclasses import dataclass

from sauronlab.core.core_imports import *
from sauronlab.viz._internal_viz import *
from sauronlab.viz.figures import *


@dataclass(frozen=True)
class BreakdownBarPlotter(KvrcPlotting):
    """"""

    bar_width: float = sauronlab_rc.acc_bar_width_fraction
    kwargs: Optional[Mapping[str, Any]] = None

    def plot(self, labels, sizes, colors=None, ax=None):
        """


        Args:
          labels:
          sizes:
          colors:
          ax:

        Returns:

        """
        if ax is None:
            figure = plt.figure()
            ax = figure.add_subplot(1, 1, 1)
        if colors is True:
            colors = InternalVizTools.assign_colors(labels)
        elif colors is False or colors is None:
            colors = ["black" for _ in labels]
        kwargs = {} if self.kwargs is None else self.kwargs
        bars = ax.bar(labels, sizes, **kwargs)
        if colors is not None:
            for bar, color in zip(bars, colors):
                patch = bar
                current_width = patch.get_width()
                diff = current_width - self.bar_width
                patch.set_width(self.bar_width)
                patch.set_x(patch.get_x() + diff * 0.5)  # recenter
                bar.set_color(color)
                # bar.set_linewidth(1)
                bar.set_edgecolor("black")
        ax.set_ylabel("N compounds")
        ax.set_xticklabels(FigureTools.fix_labels(labels), rotation=90)
        ax.set_xlim(-0.5, len(set(labels)) - 0.5)
        return ax.get_figure()


@dataclass(frozen=True)
class BreakdownPiePlotter(KvrcPlotting):
    """Code to make pretty pie charts with holes in the center."""

    radius: float = 1.0
    kwargs: Optional[Mapping[str, Any]] = None

    def plot(self, labels, sizes, colors=None, explode=None, ax=None) -> Figure:
        """


        Args:
            labels:
            sizes:
            colors:
            explode:
            ax:

        Returns:

        """
        if colors is False or colors is None:
            colors = ["black" for _ in labels]
        if explode is None:
            explode = [0.0 for _ in sizes]
        if ax is None:
            figure = plt.figure(figsize=(sauronlab_rc.width, sauronlab_rc.width))
            ax = figure.add_subplot(1, 1, 1)
        kwargs = {} if self.kwargs is None else self.kwargs
        wedges, labs = ax.pie(
            sizes,
            colors=colors,
            labels=labels,
            autopct=None,
            startangle=90,
            pctdistance=sauronlab_rc.breakdown_pie_pct_distance,
            explode=explode,
            wedgeprops={
                "edgecolor": "black",
                "linewidth": sauronlab_rc.breakdown_pie_outline_width,
                "linestyle": "-",
                "antialiased": True,
            },
            textprops={"linespacing": sauronlab_rc.general_linespacing},
            radius=self.radius,
            **kwargs,
        )
        for i, t in enumerate(labs):
            t.set_color(colors[i])
        # draw circle
        centre_circle = plt.Circle(
            (0, 0),
            sauronlab_rc.breakdown_pie_center_circle_fraction,
            lw=sauronlab_rc.breakdown_pie_outline_width,
            fc="white",
            edgecolor="black",
        )
        fig = plt.gcf()
        fig.gca().add_artist(centre_circle)
        # Equal aspect ratio ensures that pie is drawn as a circle
        # ax.axis('equal')
        ax.set_aspect("equal", adjustable="box")
        return ax.get_figure()


__all__ = ["BreakdownPiePlotter", "BreakdownBarPlotter"]

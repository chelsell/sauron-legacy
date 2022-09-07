from __future__ import annotations

from sauronlab.core.core_imports import *
from sauronlab.model.well_frames import WellFrame
from sauronlab.viz._internal_viz import *
from sauronlab.viz.figures import *


class WellPlotter(KvrcPlotting):
    """"""

    def plot(self, df: WellFrame) -> Figure:
        """


        Args:
            df: WellFrame:

        Returns:

        """
        raise NotImplementedError()


class TwoDWellPlotter(WellPlotter):
    """"""

    def __init__(self, alpha: float = 0.8):
        """

        Args:

        """
        self.alpha = alpha

    def plot(self, df: WellFrame) -> Figure:
        """


        Args:
            df: WellFrame:

        Returns:

        """
        if df.feature_length() != 2:
            raise LengthMismatchError(
                f"{self.__class__.__name__} only applies to WellFrames with precisely 2 features"
            )
        if len(df["name"].unique()) < len(df["color"].unique()):
            raise LengthMismatchError(
                "{} unique names < {} colors".format(
                    len(df["name"].unique()), len(df["color"].unique())
                )
            )
        str_sizes = [s for s in df["size"].unique() if Tools.try_none(lambda: float(s)) is None]
        if len(str_sizes) > 0:
            logger.warning(f"Sizes {str_sizes} could not be converted to floats. Ignoring.")
        cls = df.__class__
        logger.trace(f"Plotting with {self.__class__.__name__}...")
        figure = plt.figure()
        ax = figure.add_subplot(1, 1, 1)
        for marker in df["marker"].unique():
            df_by_marker = cls.retype(df[df["marker"] == marker])
            for name in df_by_marker["name"].unique():
                df_by_label = cls.retype(df_by_marker[df_by_marker["name"] == name])
                color = df_by_label.only("color")
                for size in df_by_label["size"].unique():
                    df_by_size = cls.retype(df_by_label[df_by_label["size"] == size])
                    try:
                        s = float(size)
                    except ArithmeticError:
                        s = 1
                    if len(df_by_size) > 0:
                        ax.scatter(
                            df_by_size[0],
                            df_by_size[1],
                            s=sauronlab_rc.tsne_marker_size * s,
                            c=color,
                            marker=marker,
                            label=name,
                            edgecolor=sauronlab_rc.tsne_marker_edge_color,
                            linewidths=sauronlab_rc.tsne_marker_edge_width,
                            rasterized=sauronlab_rc.rasterize_scatter,
                            alpha=self.alpha,
                        )
        ax.set_xticks([])
        ax.set_yticks([])
        ordered_names = df["name"].unique().tolist()
        ordered_colors = df["color"].unique().tolist()
        kwargs = (
            dict(ncol=sauronlab_rc.tsne_legend_n_cols)
            if sauronlab_rc.tsne_legend_n_cols is not None
            else {}
        )
        FigureTools.manual_legend(
            ax,
            ordered_names,
            ordered_colors,
            bbox_to_anchor=sauronlab_rc.tsne_legend_bbox,
            loc=sauronlab_rc.tsne_legend_loc,
            **kwargs,
        )
        FigureTools.stamp_runs(ax, df["run"])
        ax.set_aspect("equal", adjustable="box")
        return figure


class WellPlotters:
    """"""

    @classmethod
    def basic(cls, df: WellFrame, recolor: bool = False, **kwargs) -> Figure:
        """
        Plots a standard 2D well plot such as t-SNE or PCA.

        Args:
            df: WellFrame with exactly 2 features
            recolor: Overrides the color column of the WellFrame, selecting 1 color per name and accounting for control types
            df: WellFrame:
            recolor:
            **kwargs:

        Returns:

        """
        if recolor:
            df = df.set_meta(
                "color", InternalVizTools.assign_colors_x(df["name"], df["control_type"])
            )
        return TwoDWellPlotter(**kwargs).plot(df)


__all__ = ["WellPlotter", "TwoDWellPlotter", "WellPlotters"]

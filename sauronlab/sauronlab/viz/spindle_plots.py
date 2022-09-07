from natsort import natsorted

from sauronlab.core.core_imports import *
from sauronlab.core.tools import *
from sauronlab.model.responses import DoseResponseFrame2D
from sauronlab.viz._internal_viz import *
from sauronlab.viz.figures import *


@abcd.auto_repr_str()
@abcd.auto_html()
class SpindlePlotter:
    """
    Plots difference from a negative control on the x-axis and difference from a positive control on the y-axis.
    WARNING: CURRENTLY NOT GUARANTEED TO WORK.

    """

    def __init__(
        self,
        x_label: str = "vs-solvent acc. (%)",
        y_label: str = "vs-lethal acc. (%)",
        x_thresh: Union[None, float, Tup[float, str]] = None,
        y_thresh: Union[None, float, Tup[float, str]] = None,
    ):
        """

        Args:
            x_label:
            y_label:
            x_thresh:
            y_thresh:
        """
        self.x_label, self.y_label = x_label, y_label
        self.x_thresh, self.y_thresh = x_thresh, y_thresh

    def plot(self, df: DoseResponseFrame2D) -> Figure:
        """


        Args:
            df: DoseResponseFrame2D:

        Returns:

        """
        worst_negative = Tools.ifloor(df["score_1"].min() / 10) * 10
        worst_positive = Tools.ifloor(df["score_2"].min() / 10) * 10
        figure = plt.figure()
        ax = figure.add_subplot(1, 1, 1)  # type: Axes
        df = df.copy()
        if "size" not in df:
            df["size"] = (
                (df["x_value"] - df["x_value"].mean() + 1)
                / df["x_value"].std()
                * sauronlab_rc["lines.markersize"]
            )
        if "color" not in df.columns:
            df["color"] = InternalVizTools.assign_colors_x(df["label"], df["control"])
        zzz, yyy = [], []
        for label in natsorted(df["label"].unique()):
            dfx = df[df["label"] == label]
            # TODO these are the wrong params
            ax.scatter(
                dfx["score_1"],
                dfx["score_2"],
                label=FigureTools.fix_labels(label),
                c=dfx["color"],
                edgecolor=sauronlab_rc.tsne_marker_edge_color,
                linewidths=sauronlab_rc.tsne_marker_edge_width,
                alpha=0.8,
                s=dfx["size"],
            )
            yyy.append(label)
            zzz.append(Tools.only(dfx["color"]))
        x0, x1 = worst_negative - sauronlab_rc.spindle_jitter, 100 + sauronlab_rc.spindle_jitter
        y0, y1 = worst_positive - sauronlab_rc.spindle_jitter, 100 + sauronlab_rc.spindle_jitter
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
        ax.set_xticks(np.arange(worst_negative, 101, 10))
        ax.set_yticks(np.arange(worst_positive, 101, 10))
        # ax.set_xticklabels(np.arange(0, 101, 20))
        # ax.set_yticklabels(np.arange(0, 101, 20))
        ax.set_xlabel(FigureTools.fix_labels(self.x_label))
        ax.set_ylabel(FigureTools.fix_labels(self.y_label))

        if self.x_thresh is not None:
            val, txt = self._line(self.x_thresh)
            ax.axvline(val, linestyle=sauronlab_rc.spindle_sig_line_style)
            if txt is not None:
                ax.text(
                    val,
                    100 + sauronlab_rc.spindle_jitter,
                    txt,
                    rotation=90,
                    verticalalignment="top",
                    horizontalalignment="right",
                )
        if self.y_thresh is not None:
            val, txt = self._line(self.y_thresh)
            ax.axhline(val, linestyle=sauronlab_rc.spindle_sig_line_style)
            if txt is not None:
                ax.text(
                    100 + sauronlab_rc.spindle_jitter,
                    val,
                    txt,
                    horizontalalignment="right",
                    verticalalignment="bottom",
                )
        ordered_names = df["label"].unique().tolist()
        ordered_colors = df["color"].unique().tolist()
        FigureTools.manual_legend(ax, ordered_names, ordered_colors)
        return figure

    def _line(self, thresh):
        """


        Args:
            thresh:

        Returns:

        """
        if thresh is None:
            return None, None
        if isinstance(thresh, tuple):
            return thresh
        else:
            return thresh, None


_all__ = ["SpindlePlotter"]

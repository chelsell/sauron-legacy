from dataclasses import dataclass

from sauronlab.core.core_imports import *
from sauronlab.viz._internal_viz import *
from sauronlab.viz.figures import FigureTools


@dataclass(frozen=True)
class ConfusionPlotter(KvrcPlotting):

    vmin: float = 0
    vmax: float = 1
    renamer_fn: Callable[[str], str] = lambda s: s
    label_color_fn: Optional[Callable[[str], str]] = None
    label_colorbar: Optional[str] = "predictions (%)"

    def plot(self, confusion, runs: Optional[Sequence[int]] = None) -> Figure:
        figure = plt.figure()
        ax = figure.add_subplot(111)
        data = confusion.values if hasattr(confusion, "values") else confusion
        # beware of the weird order of elements in extent!
        # it's because we set origin='upper'
        extent = (0, data.shape[1], data.shape[0], 0)
        mat = ax.pcolormesh(
            data * 100,
            cmap=sauronlab_rc.confusion_cmap,
            vmin=100 * self.vmin,
            vmax=100 * self.vmax,
        )
        cbar = FigureTools.add_aligned_colorbar(ax, mat)
        if cbar is not None and self.label_colorbar:
            cbar.ax.set_ylabel(FigureTools.fix_labels(self.label_colorbar), rotation=90)
        # ax.set_xlim(-1.0, data.shape[0] - 1.0)
        # axis labels
        ax.set_ylabel("actual")
        ax.set_xlabel("prediction")
        # ticks and tick labels
        ax.xaxis.set_ticks([i + 0.5 for i, _ in enumerate(confusion.index.values)])
        ax.yaxis.set_ticks([i + 0.5 for i, _ in enumerate(confusion.columns.values)])
        ax.grid(False)
        ax.xaxis.set_ticks([], minor=True)
        ax.yaxis.set_ticks([], minor=True)
        ax.set_xticklabels(
            [FigureTools.fix_labels(self.renamer_fn(k)) for k in confusion.index.values],
            rotation=90,
        )
        ax.set_yticklabels(
            [FigureTools.fix_labels(self.renamer_fn(k)) for k in confusion.columns.values]
        )
        ax.xaxis.set_ticks_position("bottom")
        # for t in ax.xaxis.get_ticklines(minor=False):
        #     print(t.__dict__)
        for label_x, tick_x, spine_x, label_y, tick_y, spine_y in zip(
            confusion.index.values,
            ax.get_xticklabels(),
            [z for z in ax.xaxis.get_ticklines(minor=False) if z._yorig[0] == 0],
            confusion.columns.values,
            ax.get_yticklabels(),
            [z for z in ax.yaxis.get_ticklines(minor=False) if z._xorig[0] == 0],
        ):
            assert label_x == label_y and tick_x.get_text() == tick_y.get_text(), str(
                [label_x, tick_x.get_text(), label_y, tick_y.get_text()]
            )
            name = label_x
            color = self.label_color_fn(name)
            spine_x.set_color(color)
            spine_y.set_color(color)
            tick_x.set_color(color)
            tick_y.set_color(color)
        if runs is not None:
            FigureTools.stamp_runs(ax, runs)
        # https://github.com/matplotlib/matplotlib/issues/14675
        # THIS IS TOTALLY REQUIRED
        ax.set_ylim(data.shape[1], 0)
        return figure


class ConfusionPlots:
    @classmethod
    def plot(
        cls,
        confusion,
        vmin: float = 0,
        vmax: float = 1,
        runs: Optional[Sequence[int]] = None,
        renamer: Union[None, Mapping[str, str], Callable[[str], str]] = None,
        label_colors: Union[bool, Mapping[str, str]] = False,
    ) -> Figure:
        # colors
        if label_colors is None or label_colors is False:

            def label_color_fn(s):
                return "black"

        elif label_colors is True:

            def label_color_fn(s):
                return sauronlab_rc.pref_control_color_dict.get(
                    s, sauronlab_rc.pref_name_color_dict.get(s, "black")
                )

        elif isinstance(label_colors, Mapping):

            def label_color_fn(s: str):
                return label_colors.get(s, "black")

        elif callable(label_colors):
            label_color_fn = label_colors
        else:
            raise XTypeError(type(label_colors))
        # now labels
        if renamer is None:

            def renamer_fn(s):
                return s

        elif isinstance(renamer, Mapping):

            def renamer_fn(s: str):
                return renamer.get(s, s)

        elif callable(renamer):
            renamer_fn = renamer
        else:
            raise XTypeError(type(renamer))
        plotter = ConfusionPlotter(
            vmin=vmin, vmax=vmax, renamer_fn=renamer_fn, label_color_fn=label_color_fn
        )
        return plotter.plot(confusion, runs=runs)


__all__ = ["ConfusionPlotter", "ConfusionPlots"]

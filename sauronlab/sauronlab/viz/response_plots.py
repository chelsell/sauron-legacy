from dataclasses import dataclass

import matplotlib.ticker as ticker

from sauronlab.core.core_imports import *
from sauronlab.model.responses import *
from sauronlab.viz._internal_viz import *
from sauronlab.viz.figures import FigureTools


class UnsupportedPlotOption(UnsupportedOpError):
    """ """

    pass


@dataclass(frozen=True)
class Position:
    """"""

    left: bool
    right: bool
    top: bool
    bottom: bool
    first: bool
    last: bool


class Miniaxis:
    """"""

    def __init__(self, ax: Axes, position: Position):
        """

        Args:
            ax:
            position:
        """
        self.ax, self.position = ax, position
        self.twin = self.ax.twinx()

    def plot(self, x, mean, upper, lower, label: str, color: str, twin: bool) -> None:
        """


        Args:
            x:
            mean:
            upper:
            lower:
            label: str:
            color: str:
            twin: bool:

        """
        x, mean, upper, lower = self._mk2(x, mean, upper, lower)
        ax = self.twin if twin else self.ax
        if sauronlab_rc.response_bound_alpha > 0:
            ax.fill_between(
                x, lower, upper, facecolor=color, alpha=sauronlab_rc.response_bound_alpha
            )
        if sauronlab_rc.response_mean_alpha > 0:
            ax.plot(x, mean, label=label, color=color, alpha=sauronlab_rc.response_mean_alpha)
        if sauronlab_rc.response_mean_marker != "":
            ax.scatter(
                x,
                mean,
                marker=sauronlab_rc.response_mean_marker,
                color=color,
                alpha=sauronlab_rc.response_mean_alpha,
            )

    def _mk2(self, x, v, u, w):
        """
        When there's only 1 point, turn it into 2 so we still get a line.

        Args:
            x:
            v:
            u:
            w:

        Returns:

        """
        if len(x) == len(v) == len(u) == len(w) == 1:
            x0 = next(iter(x))
            v0, u0, w0 = next(iter(v)), next(iter(u)), next(iter(w))
            x = [x0 - 1, x0 + 1]
            v, u, w = [v0, v0], [u0, u0], [w0, w0]
        return x, v, u, w

    def _plot(self, x, v, label, color, marker, alpha, twin) -> None:
        """


        Args:
            x:
            v:
            label:
            color:
            marker:
            alpha:
            twin:

        """
        ax = self.twin if twin else self.ax
        if v is not None and alpha > 0:
            if sauronlab_rc.response_bound_marker != "":
                ax.scatter(x, v, marker=marker, label=label, color=color, alpha=alpha)
            if len(x) == len(v) == 1:
                x0, v0 = next(iter(x)), next(iter(v))
                x = [x0 - 1, x0 + 1]
                v = [v0, v0]
            ax.plot(x, v, label=label, color=color, alpha=alpha)

    def adjust(
        self,
        label: str,
        x_label: str,
        left_label: str,
        right_label: str,
        x_ticks: Sequence[float],
        x_tick_labels: Sequence[str],
        y_ticks: Sequence[float],
        y_tick_labels: Sequence[str],
        right_ticks: Sequence[float],
        right_tick_labels: Sequence[str],
        force_ylim=None,
    ) -> None:
        """


        Args:
            label: str:
            x_label: str:
            left_label: str:
            right_label: str:
            x_ticks: Sequence[float]:
            x_tick_labels: Sequence[str]:
            y_ticks: Sequence[float]:
            y_tick_labels: Sequence[str]:
            right_ticks: Sequence[float]:
            right_tick_labels: Sequence[str]:
            force_ylim:  (Default value = None)

        """
        if right_label is None:
            right_label = ""
        if right_ticks is None:
            right_ticks = [0]
        if right_tick_labels is None:
            right_tick_labels = []
        ax, twin = self.ax, self.twin
        ax.set_title(FigureTools.fix_labels(label))
        # set x and y ticks
        ax.set_xticks(x_ticks)
        ax.set_yticks(y_ticks)
        twin.set_yticks(right_ticks)
        # TODO this shouldn't be needed
        ax.set_xlim(0, max(x_ticks))
        # and set the tick labels
        ax.set_xticklabels(x_tick_labels)
        ax.set_yticklabels(["" for _ in y_tick_labels])
        twin.set_yticklabels(["" for _ in right_tick_labels])
        # set the y limits
        if force_ylim is None:
            ax.set_ylim(min(y_ticks), max(y_ticks))
            twin.set_ylim(min(right_ticks), max(right_ticks))
        else:
            ax.set_ylim(force_ylim)
            twin.set_ylim(force_ylim)
        # colors and spines
        ax.tick_params(axis="y", colors=sauronlab_rc.response_color_left)
        ax.yaxis.label.set_color(sauronlab_rc.response_color_left)
        ax.spines["left"].set_color(sauronlab_rc.response_color_left)
        twin.tick_params(axis="y", colors=sauronlab_rc.response_color_right)
        twin.yaxis.label.set_color(sauronlab_rc.response_color_right)
        ax.spines["right"].set_color(sauronlab_rc.response_color_right)
        # now change the tick labels when necessary
        # show tick labels only if on edge
        # A NOTE:
        # this is confusing, but think about how the figures are arranged: left to right, then top to bottom
        # this means that the last row will always be filled --- so we always have a bottom left corner
        # but the right corner might not be filled
        # in this case we could either add the label to the cell directly above the lower right corner
        # but this looked weird. so instead, I filled the *last* cell
        if self.position.left:
            ax.set_yticklabels(y_tick_labels)
        if self.position.right or self.position.last:
            twin.set_yticklabels(right_tick_labels)
        # show the axis labels only in corners
        if self.position.left and self.position.bottom:
            ax.set_xlabel(x_label)
            ax.set_ylabel(FigureTools.fix_labels(left_label))
        if self.position.last:
            twin.set_ylabel(FigureTools.fix_labels(right_label))
        # set again?
        ax.xaxis.set_major_formatter(ticker.FormatStrFormatter("%s"))
        ax.xaxis.set_minor_formatter(ticker.FormatStrFormatter("%s"))


class Grid:
    """"""

    def __init__(
        self,
        n_rows: int,
        n_columns: int,
        x_label,
        left_label,
        right_label,
        y_ticks,
        y_tick_labels,
        right_ticks,
        right_tick_labels,
        force_ylim: Optional[Tup[float, float]],
        rotate_x_ticks: bool,
        summary: pd.DataFrame,
        figure: Figure,
    ):
        """

        Args:
            n_rows:
            n_columns:
            x_label:
            left_label:
            right_label
            y_ticks:
            y_tick_labels:
            right_ticks:
            right_tick_labels:
            force_ylim:
            rotate_x_ticks:
            summary:
            figure:
        """
        self.n_rows, self.n_columns = n_rows, n_columns
        self.x_label, self.left_label, self.right_label = x_label, left_label, right_label
        y_tick_labels = [
            Tools.strip_empty_decimal(Tools.round_to_sigfigs(z, 2)) for z in y_tick_labels
        ]
        if right_tick_labels is not None:
            right_tick_labels = [
                Tools.strip_empty_decimal(Tools.round_to_sigfigs(z, 2)) for z in right_tick_labels
            ]
        self.right_ticks, self.right_tick_labels = right_ticks, right_tick_labels
        self.y_ticks, self.y_tick_labels = y_ticks, y_tick_labels
        self.force_ylim = force_ylim
        self.rotate_x_ticks = rotate_x_ticks
        self.summary = summary.copy()
        self.summary["x_value"] = self.summary["x_value"].astype(np.float32)
        self.summary = self.summary.sort_values(["label", "x_value"])
        self._drugs = self.summary["label"].unique()
        self._multi_x = len(self.summary["x_text"].unique()) != len(self.summary) // len(
            self.summary["label"].unique()
        )
        self.figure = figure
        self._gs = GridSpec(n_rows, n_columns, figure=figure)
        self._i = 0

    def spawn(self) -> Axes:
        """

        Returns:

        """
        """ """
        i, row, col = self._i + 1, self._i // self.n_columns + 1, self._i % self.n_columns + 1
        drug = self._drugs[self._i]
        data = self.summary[self.summary["label"] == drug].copy()
        data["x_text"] = data["x_text"].map(Tools.strip_empty_decimal)

        ax = self.figure.add_subplot(self._gs[self._i])
        # include the case where we don't have an even number and this is the last time the cell is on the right edge
        n = len(self._drugs)
        is_even = n % self.n_columns == 0
        is_short = self.n_columns < n
        is_last = (
            is_short
            and col == n
            or is_even
            and i == n
            or not is_even
            and col == self.n_columns
            and row == self.n_rows - 1
        )
        position = Position(
            col == 1, col == self.n_columns, row == 1, row == self.n_rows, self._i == 0, is_last
        )
        mini = Miniaxis(ax, position)

        def get(c):
            return data[c] if c in data.columns else None

        mean, upper, lower = get("score_1"), get("upper_1"), get("lower_1")
        mini.plot(
            data["x_value"], mean, upper, lower, drug, sauronlab_rc.response_color_left, twin=False
        )
        if self.right_label is not None:
            mean, upper, lower = get("score_2"), get("upper_2"), get("lower_2")
            mini.plot(
                data["x_value"],
                mean,
                upper,
                lower,
                drug,
                sauronlab_rc.response_color_right,
                twin=True,
            )
        mini.adjust(
            drug,
            self.x_label,
            self.left_label,
            self.right_label,
            data["x_value"],
            data["x_text"],
            self.y_ticks,
            self.y_tick_labels,
            self.right_ticks,
            self.right_tick_labels,
            force_ylim=self.force_ylim,
        )
        if self._multi_x or position.bottom:
            ax.set_xticklabels(data["x_text"])
        else:
            ax.set_xticklabels([])
        if self.rotate_x_ticks:
            for tick in ax.get_xticklabels():
                tick.set_rotation(90)
        self._i += 1
        return ax


class DoseResponsePlotter:
    """
    Plots a grid of input and response axes. The responses can include an axis on the right.
    """

    def __init__(
        self,
        x_label: str = "conc. (µM)",
        left_label: str = "Δ solvent (%)",
        right_label: Optional[str] = "Δ lethal (%)",
        y_ticks: Union[Sequence[float]] = None,
        right_ticks=None,
        n_rows: Optional[int] = None,
        n_cols: Optional[int] = None,
        ylim: Optional[Tup[float, float]] = None,
        rotate_x_ticks: bool = False,
    ):
        """

        Args:
            x_label:
            left_label:
            right_label:
            y_ticks
            right_ticks:
            n_rows:
            n_cols:
            ylim:
            rotate_x_ticks:
        """
        self.x_label, self.left_label, self.right_label, self.y_ticks, self.right_ticks = (
            x_label,
            left_label,
            right_label,
            y_ticks,
            right_ticks,
        )
        self.n_rows, self.n_cols = n_rows, n_cols
        self.ylim = ylim
        self.rotate_x_ticks = rotate_x_ticks

    def plot(self, summary: DoseResponseFrame) -> Figure:
        """
        Plot a grid of minplots.

        Args:
            summary: A DoseResponseFrame (dataframe subclass)

        Returns:
            A Figure

        """
        n_rows, n_cols = self.n_rows, self.n_cols
        summary = summary.sort_values(["label", "x_value"])
        n_total = len(summary["label"].unique())
        if self.y_ticks is None:

            def get_ticks(n) -> np.array:
                """


                Args:
                    n:

                Returns:

                """
                print(n)
                top = np.max(
                    [
                        summary[c].max()
                        for c in ["score_" + str(n), "upper_" + str(n), "lower_" + str(n)]
                        if c in summary.columns
                    ]
                )
                bottom = np.min(
                    [
                        summary[c].min()
                        for c in ["score_" + str(n), "upper_" + str(n), "lower_" + str(n)]
                        if c in summary.columns
                    ]
                )
                delta = (top - bottom) / 6
                return np.arange(bottom - 0.5 * delta, top + 1.5 * delta, delta)

            self.y_ticks = get_ticks(1)
            self.right_ticks = None if self.right_ticks is None else get_ticks(2)
        if n_cols is None:
            n_cols = Tools.iceil(np.sqrt(n_total))
        if n_rows is None:
            n_rows = Tools.iceil(n_total / n_cols)
        figure = plt.figure(figsize=(sauronlab_rc.width, sauronlab_rc.height))
        grid = Grid(
            n_rows,
            n_cols,
            self.x_label,
            self.left_label,
            self.right_label,
            self.y_ticks,
            self.y_ticks,
            self.right_ticks,
            self.right_ticks,
            self.ylim,
            self.rotate_x_ticks,
            summary,
            figure,
        )
        for i in range(n_total):
            grid.spawn()
        return figure


__all__ = ["DoseResponsePlotter"]

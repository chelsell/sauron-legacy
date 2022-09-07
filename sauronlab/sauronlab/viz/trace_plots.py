from __future__ import annotations

import matplotlib.ticker as ticker

from sauronlab.core.core_imports import *
from sauronlab.model.assay_frames import *
from sauronlab.model.features import *
from sauronlab.model.stim_frames import *
from sauronlab.model.well_frames import *
from sauronlab.viz import CakeLayer
from sauronlab.viz._internal_viz import *
from sauronlab.viz.figures import FigureTools
from sauronlab.viz.stim_plots import *


@abcd.auto_eq()
@abcd.auto_repr_str()
class TraceBase(CakeLayer, KvrcPlotting):
    def __init__(
        self,
        top_bander: Callable[[WellFrame], pd.DataFrame] = (
            lambda group: group.agg_by_name("quantile", q=0.8).smooth(window_size=10)
        ),
        bottom_bander: Callable[[WellFrame], pd.DataFrame] = (
            lambda group: group.agg_by_name("quantile", q=0.2).smooth(window_size=10)
        ),
        mean_bander: Optional[Callable[[WellFrame], pd.DataFrame]] = None,
        mean_band_color: Optional[str] = None,
        with_bar: bool = False,
        feature: FeatureType = FeatureTypes.MI,
    ):
        self._banded = top_bander is None or bottom_bander is None or mean_bander is None
        self._top_bander = top_bander
        self._bottom_bander = bottom_bander
        self._mean_bander = mean_bander
        self._mean_band_color = mean_band_color
        self._with_bar = with_bar
        self._feature = feature
        self._y_label = (
            sauronlab_rc.get_feature_names()[feature.internal_name] + " " + feature.recommended_unit
        )
        self._y_axis_formatter = ticker.FuncFormatter(
            lambda x, pos: "{0:g}".format(round(x / feature.recommended_scale), 0)
        )

    def plot(
        self,
        subdf: AbsWellFrame,
        s: str,
        control_names: Sequence[str],
        ax1: Axes,
        colors: Mapping[str, str],
        alphas: Mapping[str, float],
        y_bounds: Optional[Tup[float, float]],
        starts_at_ms: int,
        run_dict: Optional[Mapping[str, str]],
    ) -> Axes:
        ax1.set_rasterization_zorder(1)
        ax1.grid(b=False)
        ax1.set_facecolor("white")
        ax1.set_xticks([])
        ordered_names, ordered_colors = [], []
        for i, mininame in enumerate(reversed(subdf.unique_names())):
            group = subdf.with_name(mininame)
            color = colors[mininame]
            alpha = alphas[mininame]
            ordered_names.append(mininame)
            ordered_colors.append(color)
            self._plot_single(group, mininame, color, alpha, ax1, y_bounds)
        if sauronlab_rc.trace_legend_on:
            if sauronlab_rc.trace_legend_ignore_controls:
                legend_labels, legend_colors = [], []
                for i, s in enumerate(ordered_names):
                    if s not in control_names:
                        legend_labels.append(s)
                        legend_colors.append(ordered_colors[i])
            else:
                legend_labels, legend_colors = ordered_names, ordered_colors
            FigureTools.manual_legend(
                ax1,
                legend_labels,
                legend_colors,
                bbox_to_anchor=sauronlab_rc.trace_legend_bbox,
                ncol=sauronlab_rc.trace_legend_n_cols,
                loc=sauronlab_rc.trace_legend_loc,
            )
        ax1.set_ylabel(self._y_label)
        ax1.yaxis.set_major_formatter(self._y_axis_formatter)
        if self._with_bar:
            ax1.axhline(
                0,
                0,
                len(subdf.columns),
                c=sauronlab_rc.trace_bar_color,
                linestyle=sauronlab_rc.trace_bar_style,
                linewidth=sauronlab_rc.trace_bar_width,
                alpha=sauronlab_rc.trace_bar_alpha,
            )
        if run_dict is not None:
            FigureTools.stamp_runs(ax1, run_dict[s])
        return ax1

    def _plot_single(self, group, name, color, alpha, ax1, y_bounds):
        viz_name = FigureTools.fix_labels(name)
        if self._banded and len(group) > 2:
            if self._mean_bander is None:
                mean_band = (
                    group.agg_by_name("mean").smooth(window_size=10).iloc[0, :].values
                )  # won't matter
                ax1.plot(
                    mean_band,
                    alpha=0,
                    color=color,
                    label=viz_name,
                    zorder=0,
                    linewidth=sauronlab_rc.trace_line_width,
                    rasterized=sauronlab_rc.rasterize_traces,
                )
            else:
                mean_band = self._mean_bander(group).iloc[0, :].values
                mbc = color if self._mean_band_color is None else self._mean_band_color
                ax1.plot(
                    mean_band,
                    alpha=1,
                    color=mbc,
                    label=viz_name,
                    zorder=0,
                    linewidth=sauronlab_rc.trace_line_width,
                    rasterized=sauronlab_rc.rasterize_traces,
                )
            if len(group) > 1:
                top_band = self._top_bander(group).iloc[0, :].values
                bottom_band = self._bottom_bander(group).iloc[0, :].values
                ax1.fill_between(
                    np.arange(0, len(bottom_band)),
                    bottom_band,
                    top_band,
                    facecolor=color,
                    linewidth=0,
                    alpha=alpha,
                    zorder=0,
                )
        else:
            ax1.plot(
                group.T.values,
                alpha=alpha,
                color=color,
                label=viz_name,
                zorder=0,
                linewidth=sauronlab_rc.trace_line_width,
                rasterized=sauronlab_rc.rasterize_traces,
            )
        if y_bounds is not None:
            ax1.set_ylim(y_bounds[0], y_bounds[1])
        ax1.set_xbound(0, group.feature_length())


@abcd.auto_eq()
@abcd.auto_repr_str()
class TracePlotter(KvrcPlotting):
    @classmethod
    def default_top_bander(cls, group: AbsWellFrame):
        return group.agg_by_name("quantile", q=0.8).smooth(window_size=10)

    @classmethod
    def default_bottom_bander(cls, group: AbsWellFrame):
        return group.agg_by_name("quantile", q=0.8).smooth(window_size=10)

    DEFAULT_BOTTOM_BANDER = lambda group: group.agg_by_name("quantile", q=0.2).smooth(
        window_size=10
    )

    def __init__(
        self,
        stimframes_plotter: Optional[StimframesPlotter] = None,
        y_bounds: Optional[Tup[float, float]] = None,
        trace_to_stimuli_height_ratio: Optional[Tup[float, float]] = None,
        always_plot_control: bool = False,
        top_bander: Callable[[WellFrame], pd.DataFrame] = default_top_bander,
        bottom_bander: Callable[[WellFrame], pd.DataFrame] = default_bottom_bander,
        mean_bander: Optional[Callable[[WellFrame], pd.DataFrame]] = None,
        mean_band_color: Optional[str] = None,
        with_bar: bool = False,
        feature: FeatureType = FeatureTypes.MI,
        extra_gridspec_slots: Optional[Sequence[float]] = None,
    ):
        self._stimframes_plotter = (
            stimframes_plotter if stimframes_plotter is not None else StimframesPlotter()
        )
        self._y_bounds = y_bounds
        self._trace_to_stimuli_height_ratio = trace_to_stimuli_height_ratio
        self._always_plot_control = always_plot_control
        self._top_bander = top_bander
        self._bottom_bander = bottom_bander
        self._mean_bander = mean_bander
        self._mean_band_color = mean_band_color
        self._with_bar = with_bar
        self._feature = feature
        self._extra_gridspec_slots = [] if extra_gridspec_slots is None else extra_gridspec_slots
        self._banded = top_bander is None or bottom_bander is None or mean_bander is None

    def plot(
        self,
        df: WellFrame,
        stimframes: Union[None, StimFrame, Mapping[str, StimFrame]] = None,
        control_names: Union[
            Sequence[str], str, None, Mapping[str, Sequence[str]], Mapping[str, Set[str]]
        ] = None,
        starts_at_ms: Optional[int] = None,
        extra: Optional[Callable[[Figure, GridSpec], None]] = None,
        assays: Optional[AssayFrame] = None,
        run_dict: Optional[Mapping[str, str]] = None,
        battery: Union[None, Batteries, int, str] = None,
    ) -> Generator[Tup[str, Figure], None, None]:
        """
        Plots.

        Yields:
            Tuples mapping the name (from ``df['name']``) to figures
        """
        # prep
        t0 = time.monotonic()
        if starts_at_ms is None:
            starts_at_ms = 0
        # calc names of controls and number of plots
        control_names = self._assign_control_names(df, control_names)
        n_plots = len(
            [
                name
                for name in df.names().unique()
                if self._always_plot_control
                or len(df.without_controls()) == 0
                or (name in control_names and name not in control_names[name])
            ]
        )
        logger.info(f"Plotting {n_plots} traces...")
        # set viz defaults
        figsize, trace_height, stim_height = self._assign_sizes(len(self._extra_gridspec_slots))
        y_bounds = (0, df.max().max()) if self._y_bounds is None else self._y_bounds
        # yield a new figure for every name
        all_control_names = set()
        for s in control_names.values():
            for ss in s:
                all_control_names.add(ss)
        for i, name in enumerate(df.unique_names()):
            if self._always_plot_control or (
                name in control_names and name not in all_control_names
            ):
                sub = self._select(df, name, control_names)
                logger.info(f"Plotting {name} against {control_names[name]}")
                yield self._plot_single(
                    sub,
                    name,
                    starts_at_ms,
                    control_names[name],
                    stimframes,
                    assays,
                    run_dict,
                    extra,
                    figsize,
                    trace_height,
                    stim_height,
                    y_bounds,
                    battery,
                )
        logger.trace(
            "Plotted {} traces. Took {}.".format(
                n_plots, Tools.delta_time_to_str(time.monotonic() - t0)
            )
        )

    def _assign_control_names(
        self, df: Union[WellFrame, Sequence[str], Set[str], str], control_names
    ) -> Mapping[str, Sequence[str]]:
        if control_names is None:
            cn = {n: [] for n in df.names().unique()}
        elif isinstance(control_names, list) or isinstance(control_names, set):
            cn = {n: control_names for n in df.names().unique()}
        elif isinstance(control_names, str):
            cn = {n: [control_names] for n in df.names().unique()}
        elif isinstance(control_names, dict):
            cn = control_names
        else:
            raise XTypeError(f"Bad type {type(control_names)}")
        # TODO
        # flat_list = [item for sublist in cn.values() for item in sublist]
        # missing_names = set(flat_list)
        # if len(missing_names):
        #     warnings.warn("The control names {} are missing".format(missing_names))
        return cn

    def _assign_sizes(self, n_extra_slots: int) -> Tup[Tup[float, float], float, float]:
        trace_height, stim_height = (
            sauronlab_rc.trace_height,
            sauronlab_rc.trace_layer_const_height + sauronlab_rc.trace_layer_height * n_extra_slots,
        )
        figsize = sauronlab_rc.trace_width, trace_height + stim_height
        return figsize, trace_height, stim_height

    def _plot_single(
        self,
        sub: AbsWellFrame,
        name,
        starts_at_ms,
        control_names: Sequence[str],
        stimframes,
        assays,
        run_dict,
        extra,
        figsize,
        trace_height,
        stim_height,
        y_bounds,
        battery,
    ):
        logger.debug(f"Plotting trace for {name}")
        all_names = [*sub.unique_names(), *control_names]
        all_is_control = [s if s in control_names else None for s in all_names]
        the_colors = InternalVizTools.assign_color_dict_x(all_names, all_is_control)
        the_alphas = self._assign_alphas(control_names, name)
        figure = plt.figure(figsize=figsize, num=1, clear=True)
        n_gridspec_slots = 2 + len(self._extra_gridspec_slots)
        height_ratios = [trace_height] + self._extra_gridspec_slots + [stim_height]
        gs = GridSpec(n_gridspec_slots, 1, height_ratios=height_ratios, figure=figure)
        gs.update(hspace=sauronlab_rc.trace_hspace)
        ax1 = figure.add_subplot(gs[0])
        if extra is not None:
            extra(figure, gs, name)
        ax2 = None if stimframes is None else figure.add_subplot(gs[n_gridspec_slots - 1])
        trace_base = TraceBase(
            top_bander=self._top_bander,
            bottom_bander=self._bottom_bander,
            mean_bander=self._mean_bander,
            mean_band_color=self._mean_band_color,
            with_bar=self._with_bar,
            feature=self._feature,
        )
        member = trace_base.plot(
            sub, name, control_names, ax1, the_colors, the_alphas, y_bounds, starts_at_ms, run_dict
        )
        if ax2 is not None:
            self._stimframes_plotter.plot(
                stimframes, battery, ax2, assays=assays, starts_at_ms=starts_at_ms
            )
            ax2.set_rasterization_zorder(1)
        return name, member.get_figure()

    def _select(
        self, df: WellFrame, name: str, control_names: Mapping[str, Sequence[str]]
    ) -> AbsWellFrame:
        z = AbsWellFrame.of(
            pd.concat(
                [
                    df.with_name(name),
                    *[
                        df.with_name(control_name)
                        for control_name in control_names[name]
                        if name != control_name
                    ],
                ]
            )
        )
        return z

    def _assign_alphas(self, control_names: Sequence[str], name: str) -> Dict[str, float]:
        return {
            **{
                control_name: sauronlab_rc.band_control_alpha
                if self._banded
                else sauronlab_rc.trace_control_alpha
                for control_name in control_names
            },
            name: sauronlab_rc.band_treatment_alpha
            if self._banded
            else sauronlab_rc.trace_treatment_alpha,
        }


__all__ = ["TracePlotter"]

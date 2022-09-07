from dataclasses import dataclass

import matplotlib.ticker as ticker

from sauronlab.core.core_imports import *
from sauronlab.core.valar_tools import *
from sauronlab.model.assay_frames import *
from sauronlab.model.stim_frames import *
from sauronlab.viz import *
from sauronlab.viz._internal_viz import *
from sauronlab.viz.figures import FigureTools


@dataclass(frozen=True)
class StimframesPlotter(CakeLayer, KvrcPlotting):
    """


    Attributes:
        should_label: Show axis labels
        mark_every_n_ms: Explicitly control the number of x ticks per ms; otherwise chooses nice defaults.
        audio_waveform: Show audio stimuli as waveforms. This requires that the stimframes passed have embedded (expanded) waveforms.
        assay_labels: Show a label at the bottom for each assay
    """

    should_label: bool = True
    mark_every_n_ms: Optional[int] = None
    audio_waveform: bool = True
    assay_labels: bool = False

    def plot(
        self,
        stimframes: StimFrame,
        battery: Union[Batteries, str, int],
        ax: Optional[Axes] = None,
        assays: AssayFrame = None,
        starts_at_ms: int = 0,
    ) -> Axes:
        """


        Args:
             stimframes:
             battery:
             ax:
             assays:
             starts_at_ms:
             battery:

        Returns:

        """
        # prep / define stuff
        t0 = time.monotonic()
        battery = Batteries.fetch(battery)
        logger.debug(f"Plotting battery {battery.id} with {len(stimframes)} stimframes...")
        if starts_at_ms is None:
            starts_at_ms = 0
        sfps = ValarTools.battery_stimframes_per_second(battery)
        n_ms = int(len(stimframes) * 1000 / sfps)
        if ax is None:
            figure = plt.figure(
                figsize=(sauronlab_rc.trace_width, 2 * sauronlab_rc.trace_layer_const_height)
            )
            ax = figure.add_subplot(111)
        # the figure should always have a white background
        ax.set_facecolor("white")
        # Matt's historical pre-sauronx sauron used a definition of 0 to 1 instead of 255
        # This corrects for that.
        # Unfortunately, if the stimframes are always 0 or 1 in a range of 0-255, this will be wrong
        if stimframes.max().max() > 1:
            # noinspection PyTypeChecker
            #stimframes /= 255.0 #this happens each loop iteration causing the stimframes to become tiny
            scaleframes = stimframes / 255.0
            pass
        all_stims = {s.name: s for s in Stimuli.select()}
        # plot all the stimuli
        ordered = []
        # sort by type first; this affects which appears on top; also skip 'none'
        #logger.debug(f"Got stimuli: {stimframes.columns}")
        stimulus_list = sorted(
            [(ValarTools.stimulus_type(s).value, s) for s in scaleframes.columns if s not in ["none","ms"]]
        )
        for kind, c in stimulus_list:
            stim = all_stims[c]
            kind = ValarTools.stimulus_type(stim)
            _ax, _name, _color = self._plot_stim(stim, scaleframes[c].values, ax)
            if _name is not None and stim.audio_file_id is None:  # TODO permit
                ordered.append((kind.value, _name, _color))  # kind first for sort order later
        ordered = sorted(ordered)
        # plot the assay bounds / labels as needed
        if assays is not None:
            self._plot_assays(assays, starts_at_ms, n_ms, ax, battery)
        # set the axis labels and legend
        self._axis_labels(scaleframes, ax, starts_at_ms=starts_at_ms, total_ms=n_ms, battery=battery)
        if sauronlab_rc.stimplot_legend_on:
            ordered_names, ordered_colors = [k[1] for k in ordered], [k[2] for k in ordered]
            FigureTools.manual_legend(
                ax,
                ordered_names,
                ordered_colors,
                bbox_to_anchor=sauronlab_rc.stimplot_legend_bbox,
                ncol=sauronlab_rc.stimplot_legend_n_cols,
                loc=sauronlab_rc.stimplot_legend_loc,
            )
        # cover up line at y=0:
        if sauronlab_rc.stimplot_cover_width > 0:
            ax.hlines(
                y=0,
                xmin=0,
                xmax=len(scaleframes),
                color=sauronlab_rc.stimplot_cover_color,
                linewidth=sauronlab_rc.stimplot_cover_width,
                zorder=20,
                alpha=1,
            )
        ax.set_ybound(0, 1)
        ax.set_xbound(0, len(stimframes))
        logger.debug(f"Finished plotting battery. Took {round(time.monotonic() - t0, 1)}s.")
        return ax

    def _plot_stim(
        self, stim: Stimuli, r: pd.Series, ax: Axes
    ) -> Tup[Axes, Optional[str], Optional[str]]:
        """


        Args:
            stim:
            r:
            ax:

        Returns:

        """
        c = stim.name
        n_stimframes = len(r)
        if isinstance(r, pd.Series):
            # https://github.com/numpy/numpy/issues/15555
            # https://github.com/pandas-dev/pandas/issues/35331
            r = r.values
        x = np.argwhere(r > 0)
        y = r[r > 0]
        if not np.any(r > 0):
            return ax, None, None
        if stim.audio_file is not None and self.audio_waveform:
            ax.scatter(
                x,
                y,
                label=c,
                s=sauronlab_rc.stimplot_audio_point_size,
                clip_on=sauronlab_rc.stimplot_clip,
                rasterized=sauronlab_rc.rasterize_traces,
                marker=".",
                facecolors=sauronlab_rc.stimplot_audio_point_color,
                edgecolors="none",
            )
            return ax, ValarTools.stimulus_display_name(c), sauronlab_rc.stimplot_audio_point_color
        if sauronlab_rc.stimplot_line_alpha > 0:
            ax.plot(
                r,
                color=sauronlab_rc.get_stimulus_colors()[stim.name],
                alpha=sauronlab_rc.stimplot_line_alpha,
                label=c,
                linewidth=sauronlab_rc.stimplot_line_width,
                clip_on=sauronlab_rc.stimplot_clip,
                rasterized=sauronlab_rc.rasterize_traces,
                drawstyle="steps-post",
            )
        if sauronlab_rc.stimplot_fill_alpha > 0:
            ax.fill_between(
                range(0, n_stimframes),
                r,
                0,
                alpha=sauronlab_rc.stimplot_fill_alpha,
                facecolor=sauronlab_rc.get_stimulus_colors()[c],
                edgecolor="none",
                linewidth=0,
                clip_on=sauronlab_rc.stimplot_clip,
                rasterized=sauronlab_rc.rasterize_traces,
            )
        return (
            ax,
            ValarTools.stimulus_display_name(c),
            sauronlab_rc.get_stimulus_colors()[stim.name],
        )

    def _plot_assays(
        self, assays: pd.DataFrame, starts_at_ms: int, n_ms: int, ax: Axes, battery: Batteries
    ) -> None:
        """


        Args:
            assays:
            starts_at_ms:
            n_ms:
            ax:

        Returns:

        """
        if not self.assay_labels and not sauronlab_rc.assay_lines_without_text:
            return
        sfps = ValarTools.battery_stimframes_per_second(battery)
        for a in assays.itertuples():
            start = (a.start_ms - starts_at_ms) * sfps / 1000
            end = (a.end_ms - starts_at_ms) * sfps / 1000
            if start < 0 or end < 0:
                continue
            if a.end_ms > n_ms + starts_at_ms:
                continue
            if ValarTools.assay_is_background(a.assay_id):
                continue
            # STIMPLOT_ASSAY_LINE_HEIGHT should depend on the height and the font size
            # for some reason, setting alpha= here doesn't work
            width = sauronlab_rc.assay_line_width
            color = sauronlab_rc.assay_line_color
            alpha = sauronlab_rc.assay_line_alpha
            height = (
                sauronlab_rc.assay_line_with_text_height
                if self.assay_labels
                else sauronlab_rc.assay_line_without_text_height
            )
            lines = ax.vlines(
                start, -height, 0, lw=width, colors=color, clip_on=False, alpha=0.0, zorder=1
            )
            lines.set_alpha(alpha)
            lines = ax.vlines(
                end, -height, 0, lw=width, colors=color, clip_on=False, alpha=0.0, zorder=1
            )
            lines.set_alpha(alpha)
            lines = ax.hlines(
                -height, start, end, lw=width, colors=color, clip_on=False, alpha=0.0, zorder=1
            )
            lines.set_alpha(alpha)
            if self.assay_labels and not ValarTools.assay_is_background(a.assay_id):
                minsec = a.start
                text = (
                    a.simplified_name + " (" + minsec + ")"
                    if sauronlab_rc.assay_start_times
                    else a.simplified_name
                )
                ax.annotate(
                    text,
                    (0.5 * start + 0.5 * end, -0.5),
                    horizontalalignment="center",
                    rotation=90,
                    color=sauronlab_rc.assay_text_color,
                    annotation_clip=False,
                    alpha=sauronlab_rc.assay_text_alpha,
                )

    def _axis_labels(self, stimframes, ax, starts_at_ms, total_ms, battery):
        """


        Args:
            stimframes:
            ax:
            starts_at_ms:
            total_ms:

        Returns:

        """
        if self.should_label:
            self._label_x(stimframes, ax, starts_at_ms, total_ms, battery)
            ax.grid(False)
            ax.set_ylabel(sauronlab_rc.stimplot_y_label)
        else:
            ax.set_xticks([])
        ax.get_yaxis().set_ticks([])

    def _label_x(
        self,
        stimframes: pd.DataFrame,
        ax2: Axes,
        starts_at_ms: int,
        total_ms: int,
        battery: Batteries,
    ) -> None:
        """


        Args:
            stimframes:
            ax2:
            starts_at_ms:
            total_ms:

        Returns:

        """
        sfps = ValarTools.battery_stimframes_per_second(battery)
        mark_every = self._best_marks(stimframes, sfps)
        units, units_per_sec = InternalVizTools.preferred_units_per_sec(mark_every, total_ms)
        mark_freq = mark_every / 1000 * sfps
        # TODO  + 5*mark_freq ??
        ax2.set_xticks(np.arange(0, np.ceil(len(stimframes)) + mark_freq, mark_freq))
        ax2.set_xlabel(f"time ({units})")
        ax2.xaxis.set_major_formatter(
            ticker.FuncFormatter(
                lambda frame, pos: "{0:g}".format(
                    round((frame / sfps + starts_at_ms / 1000) * units_per_sec),
                    sauronlab_rc.trace_time_n_decimals,
                )
            )
        )

    def _best_marks(self, stimframes, sfps):
        """


        Args:
            stimframes:

        Returns:

        """
        return InternalVizTools.preferred_tick_ms_interval(len(stimframes) / sfps * 1000)


__all__ = ["StimframesPlotter"]

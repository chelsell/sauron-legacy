from __future__ import annotations

from cycler import cycler

from sauronlab.core.core_imports import *
from sauronlab.viz import plt
from sauronlab.viz._kvrc_utils import *


@abcd.not_thread_safe
@abcd.auto_repr_str()
@abcd.auto_info()
class SauronlabRc(KvrcCore):
    """
    A container for important matplotlib style settings, which can be referenced by plotters.
    """

    def _load_settings(self, config: KvrcConfig):
        """

        Args:
            config:

        Returns:
        """

        def mget(key: str):
            return plt.rcParams[key]

        # ______________________________________________________________________________________________________________

        # basic layout not in matplotlib
        self.general_suptitle_y = config.new_length("general_suptitle_y", 1.08)
        self.general_subtitle_y = config.new_length("general_subtitle_y", 1.04)
        self.general_colorbar_left_pad = config.new_length("general_colorbar_left_pad", 0.05)
        self.general_color_cycler = config.new_classmethod(
            "general_color_cycler",
            None,
            FancyColorSchemes,
            desc="Override cycler with the name of a function in KvrcColorCyclers.",
        )
        self.general_note_font_size = config.new_font_size(
            "general_note_font_size",
            mget("font.size"),
            desc="Font size for 'notes' or textual annotations inside plots",
        )
        self.general_colorbar_on = config.new_bool("general_colorbar_on", True)
        self.general_dims_sigfigs = config.new_int(
            "general_dims_sigfigs",
            6,
            desc="Number of sigfigs to round to when calculating fractional ref sizes (ex '1/3 twocol')",
        )
        self.general_linespacing = config.new_float(
            "general_linespacing", 1.2, desc="Matplotlib parameter to ``text``."
        )

        # legends in general (also see tsne and trace legend settings)
        self.legend_n_cols = config.new_int("legend_n_cols", 1)
        self.legend_expand = config.new_bool("legend_expand", False)
        self.legend_bbox = config.new_float_tuple(
            "legend_bbox", None, desc="Default bbox_to_alpha for legends"
        )
        self.legend_marker_size = config.new_float("legend_marker_size", 1)

        # the text in the upper-left corner labeling the subfigure letter
        self.panel_letter_on = config.new_bool("panel_letter_on", False)
        self.panel_letter_size = config.new_font_size(
            "panel_letter_size",
            mget("figure.titlesize"),
            desc="The font size of labels for subfigures.",
        )
        self.panel_letter_weight = config.new_font_weight(
            "panel_letter_weight", "ultrabold", desc="The font weight of the subfigure label"
        )
        self.panel_letter_str_format = config.new_str(
            "panel_letter_str_format", "{}", desc="For ex: '{})' to get 'a)' etc."
        )

        # fix common problems with label text
        self.label_fix = config.new_bool(
            "label_fix",
            True,
            "Fixes common problems with labels, such as minus signs where hyphens were used",
        )
        self.label_force_math_mode = config.new_bool(
            "label_force_math_mode",
            True,
            "Forces text mode to be used in TeX. Strips surrounding dollar signs.",
        )
        self.label_force_text_mode = config.new_bool(
            "label_force_text_mode",
            False,
            "Forces math mode to be used in TeX. Surrounds labels with dollar signs.",
        )
        self.label_replace_dict = config.new_color_dict(
            "label_replace_dict",
            {},
            "Overrides label names. Applied both before and after fixing labels.",
        )

        # the run IDs at the upper left of traces
        self.stamp_on = config.new_bool(
            "stamp_on", True, "Show run IDs at the top of many kinds of plots"
        )
        self.stamp_font_size = config.new_font_size("stamp_font_size", mget("font.size"))
        self.stamp_max_runs = config.new_int("stamp_max_runs", 10, False)

        # general colors and markers
        self.pref_markers = config.new_marker_list("pref_markers", KvrcDefaults.markers)
        self.pref_dark_colors = config.new_rgb_list("pref_dark_colors", KvrcDefaults.dark_colors)
        self.pref_light_colors = config.new_rgb_list("pref_light_colors", KvrcDefaults.light_colors)
        self.pref_treatment_colors = config.new_rgb_list(
            "pref_treatment_colors", KvrcDefaults.treatment_colors
        )
        self.pref_control_colors = config.new_rgb_list(
            "pref_control_colors", KvrcDefaults.control_colors
        )
        self.pref_control_color_dict = config.new_color_dict(
            "pref_control_color_dict", KvrcDefaults.control_color_dict
        )
        self.pref_name_color_dict = config.new_color_dict(
            "pref_name_color_dict", {}, desc="Override colors for specific labels."
        )

        # rasterization (vs. vectorization)
        self.rasterize_plain = config.new_bool("rasterize_plain", False)
        self.rasterize_scatter = config.new_bool("rasterize_scatter", False)
        self.rasterize_traces = config.new_bool("rasterize_traces", True)
        self.rasterize_heatmaps = config.new_bool("rasterize_heatmaps", True)
        self.rasterize_waveforms = config.new_bool("rasterize_waveforms", True)

        # choosing units and tick frequencies for traces
        self.trace_pref_tick_ms_interval = config.new_float_list(
            "trace_pref_tick_ms_interval", KvrcDefaults.trace_pref_tick_ms_interval
        )
        self.trace_pref_n_ticks = config.new_int("trace_pref_n_ticks", 14)
        self.trace_ms_cutoff = config.new_int("trace_ms_cutoff", 4 * 1000)
        self.trace_sec_cutoff = config.new_int("trace_sec_cutoff", 4 * 60000)
        self.trace_min_cutoff = config.new_int("trace_min_cutoff", 4 * 3600000)
        self.trace_time_n_decimals = config.new_int("trace_time_n_decimals", 0)
        self.trace_force_time_units = config.new_time_unit("trace_force_time_units", None)

        # reference heights; not used inside sauronlab
        # heights are the same as the correspdoning widths, except for the page height
        # the page height is a gross estimation of 11" with a 1" margin at the top and bottom
        self.height_page = config.new_length(
            "height_page", 9, desc="Height of a full page for a full-page figure"
        )

        # trace sizes
        self.trace_width = config.new_length("trace_width", self.width * 2)
        self.trace_height = config.new_length("trace_height", self.height / 2)
        self.trace_layer_const_height = config.new_length(
            "trace_layer_const_height", self.height / 4
        )
        self.trace_layer_height = config.new_length("trace_layer_height", self.height / 6)
        self.trace_hspace = config.new_length("trace_hspace", self.height / 24)
        if self.trace_hspace != self.height / 24:
            logger.warning(
                f"trace_hspace={self.trace_hspace} will be ignored due to a matplotlib bug."
            )

        # trace legends
        self.trace_legend_on = config.new_bool("trace_legend_on", True)
        self.trace_legend_ignore_controls = config.new_bool(
            "trace_legend_ignore_controls", False, desc="Don't show labels for controls"
        )
        self.trace_legend_loc = config.new_str("trace_legend_loc", "upper right")
        self.trace_legend_bbox = config.new_float_tuple("trace_legend_bbox", None)
        self.trace_legend_marker_size = config.new_float(
            "trace_legend_marker_size", self.legend_marker_size
        )
        self.trace_legend_n_cols = config.new_int("trace_legend_n_cols", 8)

        # trace colors
        self.trace_line_width = config.new_line_width("trace_line_width", mget("lines.linewidth"))
        self.trace_control_alpha = config.new_alpha("trace_control_alpha", 0.7)
        self.trace_treatment_alpha = config.new_alpha("trace_treatment_alpha", 1.0)
        self.band_control_alpha = config.new_alpha("band_control_alpha", 0.35)
        self.band_treatment_alpha = config.new_alpha("band_treatment_alpha", 0.6)
        self.band_zmear_trace_color = config.new_rgb("band_zmear_trace_color", "#0099ee")

        # horizontal bars across traces (marking 0), when used
        self.trace_bar_color = config.new_rgb("trace_bar_color", "red")
        self.trace_bar_width = config.new_length("trace_bar_width", 2 * mget("lines.linewidth"))
        self.trace_bar_alpha = config.new_alpha("trace_bar_alpha", 1.0)
        self.trace_bar_style = config.new_line_style("trace_bar_style", "--")

        # heatmap sizes
        self.heatmap_width = config.new_length("heatmap_width", self.width * 2)
        self.heatmap_row_height = config.new_length("heatmap_row_height", self.height / 24)
        self.heatmap_hspace = config.new_length("heatmap_hspace", 0)
        self.heatmap_stimplot_height = config.new_length("heatmap_stimplot_height", self.height / 4)

        # horizontal lines separating unique names on heatmaps
        self.heatmap_name_sep_color_symmetric = config.new_rgb(
            "heatmap_name_sep_color_symmetric", "grey"
        )
        self.heatmap_name_sep_color_asymmetric = config.new_rgb(
            "heatmap_name_sep_color_asymmetric", "red"
        )
        self.heatmap_name_sep_alpha = config.new_alpha("heatmap_name_sep_alpha", 0.8)
        self.heatmap_name_sep_width = config.new_line_width(
            "heatmap_name_sep_width", mget("lines.linewidth")
        )
        self.heatmap_name_sep_style = config.new_line_style("heatmap_name_sep_style", "-")

        # horizontal lines separating control types on heatmaps
        self.heatmap_control_sep_color_symmetric = config.new_rgb(
            "heatmap_control_sep_color_symmetric", "grey"
        )
        self.heatmap_control_sep_color_asymmetric = config.new_rgb(
            "heatmap_control_sep_color_asymmetric", "red"
        )
        self.heatmap_control_sep_alpha = config.new_alpha("heatmap_control_sep_alpha", 0.8)
        self.heatmap_control_sep_width = config.new_line_width(
            "heatmap_control_sep_width", mget("lines.linewidth")
        )
        self.heatmap_control_sep_style = config.new_line_style("heatmap_control_sep_style", "-")

        # stimplot
        self.stimplot_y_label = config.new_str("stimplot_y_label", "intensity")

        # stimplot legend
        self.stimplot_legend_on = config.new_bool("stimplot_legend_on", False)
        self.stimplot_legend_n_cols = config.new_int("stimplot_legend_n_cols", self.legend_n_cols)
        self.stimplot_legend_loc = config.new_str("stimplot_legend_loc", mget("legend.loc"))
        self.stimplot_legend_bbox = config.new_float_tuple("stimplot_legend_bbox", self.legend_bbox)
        self.stimplot_legend_marker_size = config.new_float(
            "stimplot_legend_marker_size", self.legend_marker_size
        )

        # stimplot transparency and line widths
        self.stimplot_clip = config.new_bool("stimplot_clip", True)
        self.stimplot_line_alpha = config.new_alpha("stimplot_line_alpha", 0.8)
        self.stimplot_fill_alpha = config.new_alpha("stimplot_fill_alpha", 0.6)
        self.stimplot_line_width = config.new_line_width(
            "stimplot_line_width", mget("lines.linewidth")
        )
        self.stimplot_audio_point_color = config.new_rgb("stimplot_audio_point_color", "black")
        self.stimplot_audio_point_size = config.new_point_size(
            "stimplot_audio_point_size", 0.1 * mget("lines.markersize")
        )
        self.stimplot_cover_width = config.new_line_width(
            "stimplot_cover_width", 1.4 * self.stimplot_line_width
        )
        self.stimplot_cover_color = config.new_rgb("stimplot_cover_color", "black")

        # the labels and little lines marking assays
        self.assay_lines_without_text = config.new_bool("assay_lines_without_text", False)
        self.assay_start_times = config.new_bool("assay_start_times", True)
        self.assay_line_alpha = config.new_alpha("assay_line_alpha", 0.25)
        self.assay_line_width = config.new_line_width(
            "assay_line_width", 1.5 * mget("lines.linewidth")
        )
        self.assay_line_with_text_height = config.new_length("assay_line_with_text_height", 0.28)
        self.assay_line_without_text_height = config.new_length(
            "assay_line_without_text_height", 0.15
        )
        self.assay_line_color = config.new_rgb("assay_line_color", "#555566")
        self.assay_text_color = config.new_rgb("assay_text_color", "#555566")
        self.assay_text_alpha = config.new_alpha("assay_text_alpha", 0.85)

        # dose-response plots
        self.response_color_left = config.new_rgb("response_color_left", "#000088")
        self.response_color_right = config.new_rgb("response_color_right", "#880000")
        self.response_mean_marker = config.new_marker("response_mean_marker", "")
        self.response_mean_alpha = config.new_alpha("response_mean_alpha", 1.0)
        self.response_bound_alpha = config.new_alpha("response_bound_alpha", 0.1)

        # confusion matrices
        self.confusion_cmap = config.new_cmap("confusion_cmap", KvrcDefaults.cmap)

        # accuracy plots
        self.acc_x_tick_rotation = config.new_float("acc_x_tick_rotation", 90, 0, 360)
        self.acc_point_size = config.new_point_size("acc_point_size", mget("lines.markersize"))
        self.acc_point_color = config.new_rgb("acc_point_color", "black")
        self.acc_bar_color = config.new_rgb("acc_bar_color", "#c0c0c0")
        self.acc_bar_edge_color = config.new_rgb("acc_bar_edge_color", "#000000")
        self.acc_bar_edge_width = config.new_line_width(
            "acc_bar_edge_width", 0.25 * mget("lines.linewidth")
        )
        self.acc_error_kwargs = config.new_raw_dict(
            "acc_error_kwargs",
            dict(linewidth=3 * mget("lines.linewidth")),
            desc="Keyword arguments to pass to error bars for accuracy plots.",
        )
        self.acc_error_color = config.new_rgb("acc_err_color", "#770000")
        self.acc_bar_width_fraction = config.new_float(
            "acc_bar_width_fraction", 0.8, minimum=0, maximum=1
        )

        # accuracy distribution plots
        self.dist_sig_line_color = config.new_rgb("dist_sig_line_color", "#666666")
        self.dist_sig_line_width = config.new_line_width(
            "dist_sig_line_width", mget("axes.linewidth")
        )
        self.dist_sig_line_style = config.new_line_style("dist_sig_line_style", "-")
        self.dist_sig_label_x_offset = config.new_float("dist_sig_label_x_offset", 0.02)
        self.dist_sig_label_y_offset = config.new_float("dist_sig_label_y_offset", -0.1)
        self.dist_negative_control_color = config.new_rgb("dist_negative_control_color", "#000088")
        self.dist_positive_control_color = config.new_rgb("dist_positive_control_color", "#880000")
        self.dist_treatment_color = config.new_rgb("dist_treatment_color", "#000000")
        self.dist_control_alpha = config.new_alpha("dist_control_alpha", 0.8)
        self.dist_treatment_alpha = config.new_alpha("dist_treatment_alpha", 0.8)

        # spindle accuracy plots
        self.spindle_jitter = config.new_float("spindle_jitter", 2)
        self.spindle_sig_line_style = config.new_line_style("spindle_sig_line_style", "dotted")
        self.spindle_rect_alpha = config.new_alpha("spindle_rect_alpha", 0.25)

        # diagnostic/sensor display settings
        self.sensor_line_width = config.new_line_width(
            "sensor_line_width", 0.04 * mget("lines.markersize")
        )
        self.sensor_line_color = config.new_rgb("sensor_line_color", "#000000")
        self.sensor_mic_point_size = config.new_point_size(
            "sensor_mic_point_size", 0.1 * mget("lines.markersize")
        )
        self.sensor_mic_color = config.new_rgb("sensor_mic_color", "#000000")
        self.sensor_use_symbols = config.new_bool("sensor_use_symbols", False)
        self.sensor_rasterize = config.new_bool("sensor_rasterize", True)

        # spectrogram and other audio settings
        self.audio_spectrogram_cmap = config.new_cmap("audio_spectrogram_cmap", None)
        self.audio_waveform_point_size = config.new_point_size(
            "audio_waveform_point_size", 0.075 * mget("lines.markersize")
        )
        self.audio_waveform_color = config.new_rgb("audio_waveform_color", "black")

        # weight plots
        self.weight_scatter_color = config.new_rgb("weight_scatter_color", "black")

        # highlighting and borders on videos
        self.video_roi_line_width = config.new_line_width("video_roi_line_width", 1)
        self.video_roi_color = config.new_rgb("video_roi_color", "black")
        self.video_plain_color = config.new_rgb("video_plain_color", "#000000")
        self.video_positive_control_color = config.new_rgb("video_positive_control_color", "red")
        self.video_negative_control_color = config.new_rgb("video_negative_control_color", "blue")
        self.video_neutral_control_color = config.new_rgb("video_neutral_control_color", "purple")

        # library-overview pie charts
        self.breakdown_pie_center_circle_fraction = config.new_fraction(
            "breakdown_pie_center_circle_fraction", 0.6
        )
        self.breakdown_pie_outline_width = config.new_line_width(
            "breakdown_pie_outline_width", mget("lines.linewidth")
        )
        self.breakdown_pie_pct_distance = config.new_line_width("breakdown_pie_pct_distance", 4.0)

        # p-value markers on bar plots
        self.pval_color = config.new_rgb("pval_color", "#333333")
        self.pval_n_decimals = config.new_line_width("pval_n_decimals", 2)
        self.pval_line_width = config.new_line_width("pval_line_width", mget("lines.linewidth"))
        self.pval_line_style = config.new_line_style("pval_line_style", "--")

        # "biomarker" plot settings
        self.massspec_null_color = config.new_rgb("massspec_null_color", "#999999")
        self.tissue_sep_color = config.new_rgb("tissue_sep_color", "black")
        self.tissue_sep_alpha = config.new_alpha("tissue_sep_alpha", 1.0)
        self.tissue_sep_line_style = config.new_line_style("tissue_sep_line_style", "--")

        # tSNE settings
        self.tsne_marker_size = config.new_point_size("tsne_marker_size", mget("lines.markersize"))
        self.tsne_marker_edge_color = config.new_rgb("tsne_marker_edge_color", "black")
        self.tsne_marker_edge_width = config.new_line_width(
            "tsne_marker_edge_width", 0.25 * mget("lines.linewidth")
        )
        self.tsne_legend_loc = config.new_str("tsne_legend_loc", "upper left")
        self.tsne_legend_bbox = config.new_float_tuple("tsne_legend_bbox", (1.0, 1.0))
        self.tsne_legend_n_cols = config.new_int("tsne_legend_n_cols", 1)

        # other settings
        self.timeline_marker_shape = config.new_marker("timeline_marker_shape", "s")
        self.timeline_marker_size = config.new_point_size(
            "timeline_marker_size", mget("lines.markersize")
        )

        # override names and colors of control types, features, stimuli stimuli
        # these begin with an underscore because we'll build up the full version later
        self._stimulus_names = config.new_str_dict("stimulus_names", {})
        self._stimulus_colors = config.new_color_dict("stimulus_colors", {})
        self._feature_names = config.new_str_dict("feature_names", {})
        self._control_names = config.new_str_dict("control_names", {})

        # ______________________________________________________________________________________________________________
        if self.general_color_cycler is not None:
            plt.rcParams["axes.prop_cycle"] = cycler(color=self.general_color_cycler())
        if self.label_force_math_mode and self.label_force_text_mode:
            raise ContradictoryRequestError("Cannot force math mode and force text mode")
        if plt.rcParams["figure.constrained_layout.use"] is not True:
            logger.warning("Setting figure.constrained_layout.use to true is strongly recommended.")
        if plt.rcParams["savefig.bbox"] == "tight":
            logger.warning("savefig.bbox should be 'standard'")
        for z, v in {"svg": "none", "pdf": 42, "ps": 42}.items():
            if self[z + ".fonttype"] != v:
                warn(f"{z}.fonttype != {v}, which may cause problems. Changing globally.", XWarning)
                self[z + ".fonttype"] = v


sauronlab_rc = SauronlabRc(sauronlab_env.matplotlib_style, sauronlab_env.sauronlab_style)

__all__ = ["sauronlab_rc", "KvrcDefaults", "SauronlabRc"]

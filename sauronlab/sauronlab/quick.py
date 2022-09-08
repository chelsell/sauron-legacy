from __future__ import annotations

import dataclasses
import traceback

from pocketutils.tools.loop_tools import LoopTools

from sauronlab.caches.audio_caches import *
from sauronlab.caches.caching_wfs import *
from sauronlab.caches.sensor_caches import *
from sauronlab.caches.stim_caches import *
from sauronlab.caches.wf_caches import *
from sauronlab.core.core_imports import *
from sauronlab.extras.video_caches import *
from sauronlab.ml import *
from sauronlab.ml.classifiers import *
from sauronlab.ml.transformers import *
from sauronlab.model.app_frames import *
from sauronlab.model.assay_frames import *
from sauronlab.model.compound_names import *
from sauronlab.model.concern_rules import *
from sauronlab.model.concerns import *
from sauronlab.model.features import *
from sauronlab.model.sensors import *
from sauronlab.model.stim_frames import *
from sauronlab.model.well_names import *
from sauronlab.model.wf_builders import *
from sauronlab.viz._internal_viz import *
from sauronlab.viz.figures import *
from sauronlab.viz.heatmaps import *
from sauronlab.viz.importance_plots import *
from sauronlab.viz.sensor_plots import *
from sauronlab.viz.stim_plots import *
from sauronlab.viz.timeline_plots import *
from sauronlab.viz.trace_plots import *
from sauronlab.viz.well_plots import *

QLike = Union[ExpressionLike, pd.DataFrame, str, int, float, Runs, Submissions]
QsLike = Union[
    ExpressionLike,
    WellFrame,
    Union[int, Runs, Submissions, str],
    Iterable[Union[int, Runs, Submissions, str]],
]

generation_feature_preferences = {
    **{g: FeatureTypes.MI for g in DataGeneration.pike_generations()},
    **{g: FeatureTypes.cd_10_i for g in DataGeneration.pointgrey_generations()},
}


class AggType(CleverEnum):
    """"""

    NONE = enum.auto()
    NAME = enum.auto()
    IMPORTANT = enum.auto()
    PACK = enum.auto()
    RUN = enum.auto()

    def function(self) -> Callable[[WellFrame], WellFrame]:
        """"""
        return {
            "none": lambda df: df,
            "name": lambda df: df.agg_by_name(),
            "important": lambda df: df.agg_by_important(),
            "pack": lambda df: df.agg_by_pack(),
            "run": lambda df: df.agg_by_run(),
        }[self.name.lower()]

    def agg(self, df: WellFrame) -> WellFrame:
        """


        Args:
            df: WellFrame:

        Returns:

        """
        return self.function()(df)


@dataclass(frozen=True)
class Quick:
    """
    A collection of ways to get data and plot data with nice defaults.

    Each instance can (and generally should) hold every kind of on-disk cache in the caches package.
    Quick has enough arguments that they're best called using :class:``Quicks``.

    ### Methods

    Fetching methods:
        - ``Quick.df``:                  Returns a WellFrame for one or more runs
        - ``Quick.stim``:                Returns a StimFrame from a battery
        - ``Quick.df_and_stims``:        Returns a WellFrame and a StimFrame
        - ``Quick.video``:               Returns a SauronX video for a run
        - ``Quick.microphone_waveform``: Returns the waveform from the microphone for a run
        - ``Quick.stim_waveform``:       Returns the waveform from an audio stimulus
        - Some methods delegating to ``Quick.sensor_cache``

    ### Plotting

    There are also plotting methods of a few types:

    - streaming, which return iterators of (name, Figure) tuples. These include:
        * ``Quick.traces``:        Simple time-traces of motion averaged for each name
        * ``Quick.smears``:        Time-traces of 'confidence' intervals (80th by default)
        * ``Quick.zmears``:        Time-traces of 'confidence' intervals after taking a Z-score with respect to the controls.
    - heatmaps:
        * ``Quick.rheat``:         White-to-black heatmaps of the raw features.
        * ``Quick.zheat``:         Blue-to-white-to-red heatmaps of the Z-scores with respect to controls.
    - misc:
        * *diagonstics*:         Data from the time-dependent sensors alongside the stimframes
        * *bar*:                 Barplot of mean (or other aggregation) of the features per name
    - images:
        * ``Quick.webcam_snap``:         Pillow image from the webcam
        * ``Quick.roi_snap``:            Pillow image from the main camera's initial snapshot, with the well grid ROI overlaid
        * ``Quick.structures_on_plate``: A grid of the chemical structures on the plate

    The streaming plotters each have two variants:
        - *singular* (ex ``Quick.trace``), which call plt.show and return None.
        - *plural* (ex ``Quick.traces``), which return the iterators and don't display them

    Attributes:
        feature: Generate WellFrames and plots using this feature.
        generation: Generation permitted
        as_of: Enables additional methods by setting max datetime for those queries. This includes querying by flexible Peewee Expressions
        well_cache: A FrameCache for saving WellFrames on disk
        facade: An optional FrameFacade for saving WellFrames into memory
        stim_cache: A StimCache for saving StimFrames objects on disk
        default_namer: By default, draw WellFrames with this Namer
        enable_checks: Warn about missing frames, 'concern' rows in the annotations table, suspicious batches, and more; see Concerns.warn_common_checks for full info
        auto_fix: Applies fixes to WellFrames
        sensor_cache: A SensorCache.
        video_cache: A VideoCache.
        compound_namer: Fill in 'compound_names' column in WellFrame using this function. May also be used in other places.
                        NOTE: A copy will be made with ``compound_namer.as_of`` set to ``as_of``.
        audio_stimulus_cache: An AudioStimulusCache for caching audio files, etc.
        quantile: A quantile for setting min and max on various plot types, including sensor plots and z-score plots (also see zscore_min_max)
        trace_ymax: If set, limit the y axis on traces to this; great for features like cd(10) but less so for MI
        zscore_min_max: If set, limit zmear bounds to +/- this value; otherwise a percentile will be chosen
        discard_trash: Automatically discard wells with control type in Concerns.trash_controls if True, or a passed set
        smoothing_factor: This times the frames per second = default smoothing window size
        label_assays:
        always_plot_control:
        smear_show_mean:
        threshold: Show anything with a value +/- this as pure white
        show_name_lines: Show horizontal lines between different names
        show_control_lines: Show horizontal lines between different control types
        ignore_controls: Don't plot any control wells
        tsne_recolor:
        enable_audio_waveform:

    """

    DEFAULT_NAMER = WellNamers.elegant()

    feature: Union[str, FeatureType]
    generation: Union[str, DataGeneration]
    as_of: datetime
    cache: WellCache
    stim_cache: StimframeCache
    audio_stimulus_cache: AudioStimulusCache
    sensor_cache: SensorCache
    video_cache: VideoCache
    enable_checks: bool = True
    auto_fix: bool = True
    discard_controls: Set[ControlLike] = ValarTools.trash_controls()
    compound_namer: CompoundNamer = CompoundNamers.tiered()
    well_namer: Optional[WellNamer] = DEFAULT_NAMER
    quantile: Optional[float] = 0.95
    trace_ymax: Optional[float] = None
    zscore_min_max: Optional[float] = None
    smoothing_factor: float = 0.1
    label_assays: bool = False
    always_plot_control: bool = False
    show_smear_means: bool = False
    smear_ci: float = 0.8
    min_log_severity: Severity = Severity.CAUTION
    zheat_threshold: float = 1.0
    zheat_show_control_lines: bool = True
    zheat_show_name_lines: bool = True
    zheat_ignore_controls: bool = False
    enable_audio_waveform: bool = True

    def __post_init__(self):
        if self.as_of > datetime.now():
            logger.warning(
                f"as_of is set {Tools.delta_time_to_str((self.as_of - datetime.now()).total_seconds())} in the future"
            )

    @property
    def _expanded_stim_cache(self) -> StimframeCache:
        return StimframeCache(waveform_loader=self.audio_stimulus_cache.load_waveform)

    def _get_smoothing(self, fps: int) -> int:
        return int(round(self.smoothing_factor * fps))

    def using(self, **kwargs) -> Quick:
        """
        Makes a copy of this Quick with altered fields.

        Example:
            Simple::

                quick = quick.using(namer=Namers.well(), smoothing=1)

        Args:
            **kwargs: Fields to change

        Returns:
            A new Quick with the attributes changed
        """

        return Quick(
            **{
                field.name: kwargs.get(field.name, getattr(self, field.name))
                for field in dataclasses.fields(self.__class__)
            }
        )

    def traces(
        self,
        run: QsLike,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
        control_names=None,
        control_types=None,
        weights: Optional[np.array] = None,
        agg_type: Union[AggType, str] = AggType.NAME,
    ) -> Generator[Tup[str, Figure], None, None]:
        """


        Args:
            run: QsLike:
            start_ms:
            end_ms:
            control_names:
            control_types:
            weights:
            agg_type:

        """
        (
            df,
            stimframes,
            assays,
            control_names,
            fps,
            stimplotter,
            extra_gs,
            extra_fn,
        ) = self._everything(run, start_ms, end_ms, control_names, control_types, weights)
        battery = df.only("battery_id")
        smoothing = self._get_smoothing(fps)
        tracer = TracePlotter(
            feature=self.feature,
            stimframes_plotter=stimplotter,
            extra_gridspec_slots=extra_gs,
            always_plot_control=self.always_plot_control,
            y_bounds=(0, self.trace_ymax) if self.trace_ymax else None,
        )
        run_dict = {
            n: df.with_name(n).unique_runs() for n in df.unique_names()
        }  # prior to agg_samples
        agged = AggType.of(agg_type).agg(df)
        return tracer.plot(
            agged,#.smooth(window_size=smoothing), #this empties out the dataframe for some reason
            stimframes,
            control_names=control_names,
            starts_at_ms=start_ms,
            extra=extra_fn,
            run_dict=run_dict,
            assays=assays,
            battery=battery,
        )

    def smears(
        self,
        run: QsLike,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
        control_names=None,
        control_types=None,
        weights: Optional[np.array] = None,
    ) -> Generator[Tup[str, Figure], None, None]:
        """


        Args:
            run: QsLike:
            start_ms:
            end_ms:
            control_names:
            control_types:
            weights:

        Yields:

        """
        (
            df,
            stimframes,
            assays,
            control_names,
            fps,
            stimplotter,
            extra_gs,
            extra_fn,
        ) = self._everything(run, start_ms, end_ms, control_names, control_types, weights)
        battery = df.only("battery_id")
        smoothing = self._get_smoothing(fps)
        top_bander, bottom_bander, mean_bander = self._banders(smoothing)
        run_dict = {
            n: df.with_name(n).unique_runs() for n in df.unique_names()
        }  # prior to agg_samples
        tracer = TracePlotter(
            feature=self.feature,
            stimframes_plotter=stimplotter,
            always_plot_control=self.always_plot_control,
            bottom_bander=bottom_bander,
            top_bander=top_bander,
            mean_bander=mean_bander,
            extra_gridspec_slots=extra_gs,
            y_bounds=(0, self.trace_ymax),
        )
        return tracer.plot(
            df,
            stimframes,
            control_names=control_names,
            starts_at_ms=start_ms,
            extra=extra_fn,
            run_dict=run_dict,
            battery=battery,
        )

    def zmears(
        self,
        run: QsLike,
        control_type: Union[None, str, int, ControlTypes] = None,
        control_name: Optional[str] = None,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
        weights: Optional[np.array] = None,
        subtraction=None,
    ) -> Generator[Tup[str, Figure], None, None]:
        """


        Args:
            run:
            control_type:
            control_name
            start_ms:
            end_ms:
            weights:
            subtraction:

        Yields:

        """
        (
            df,
            stimframes,
            assays,
            control_name,
            fps,
            stimplotter,
            extra_gs,
            extra_fn,
        ) = self._everything(run, start_ms, end_ms, control_name, control_type, weights)
        battery = df.only("battery_id")
        smoothing = self._get_smoothing(fps)
        if control_name is None:
            control_name = df.with_controls().unique_names()
        control_name = Tools.only(control_name, name="control types")
        zscores = self._control_subtract(
            df, control_type, control_name, subtraction=subtraction
        ).agg_by_name("mean")
        if self.zscore_min_max is None:
            y_min = zscores.quantile(0.001, axis=1).min()
            y_max = zscores.quantile(0.999, axis=1).max()
        else:
            y_min, y_max = -self.zscore_min_max, self.zscore_min_max
        top_bander, bottom_bander, mean_bander = self._banders(smoothing)
        run_dict = {
            n: df.with_name(n).unique_runs() for n in df.unique_names()
        }  # prior to agg_samples
        tracer = TracePlotter(
            feature=self.feature,
            stimframes_plotter=stimplotter,
            bottom_bander=bottom_bander,
            top_bander=top_bander,
            mean_bander=mean_bander,
            mean_band_color="black",
            with_bar=True,
            extra_gridspec_slots=extra_gs,
            y_bounds=(y_min, y_max),
        )
        traces = tracer.plot(
            zscores,
            stimframes,
            starts_at_ms=start_ms,
            extra=extra_fn,
            control_names=control_name,
            run_dict=run_dict,
            battery=battery,
        )
        for name, figure in traces:
            figure.axes[0].set_ylabel(
                f"Z-score [{sauronlab_rc.feature_names[self.feature.internal_name]}]"
            )
            yield name, figure

    def _banders(self, smoothing):
        """


        Args:
            smoothing:

        Returns:

        """
        top_bander = lambda group: group.agg_by_name(
            ["name"], "quantile", q=1 - self.smear_ci
        ).smooth(window_size=smoothing)
        bottom_bander = lambda group: group.agg_by_name(
            ["name"], "quantile", q=1 - self.smear_ci
        ).smooth(window_size=smoothing)
        mean_bander = (
            (lambda group: group.agg_by_name("mean").smooth(window_size=smoothing))
            if self.show_smear_means
            else None
        )
        return top_bander, bottom_bander, mean_bander

    def zheat(
        self,
        run: QsLike,
        control_type: Union[None, str, int, ControlTypes] = None,
        control_name: Optional[str] = None,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
    ) -> Figure:
        """
        Makes a heatmap of z-scores with respect to controls.
        If neither control_type nor control_name are set, looks for a single negative control and uses that.
        If either is set, uses that one. Will raise a UserContradictionError if both are set.

        Args:
            run: A run ID, name, or object
            control_type: The name, ID, or object of a ControlTypes; or None
            control_name: The name of an item in WellFrame.names(); or None
            start_ms: Cuts the dataframes, calculating milliseconds from the known framerate
            end_ms: Cuts the dataframes, calculating milliseconds from the known framerate

        Returns:
          The matplotlib Figure
        """
        df = self.df(run, start_ms, end_ms)
        battery = df.only("battery_name")
        stimframes = self.stimframes(battery, start_ms, end_ms, audio_waveform=True)
        stimplotter = StimframesPlotter()
        zscores = self._control_subtract(df, control_type, control_name).threshold_zeros(
            self.zheat_threshold
        )
        if self.zheat_ignore_controls:
            zscores = zscores.without_controls()
        heater = HeatPlotter(
            symmetric=True,
            stimframes_plotter=stimplotter,
            vmax_quantile=self.quantile,
            name_sep_line=self.zheat_show_name_lines,
            control_sep_line=self.zheat_show_control_lines,
        )
        figure = heater.plot(zscores, stimframes, starts_at_ms=start_ms, battery=battery)
        return figure

    def rheat(
        self,
        run: QsLike,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
    ) -> Figure:
        """


        Args:
            run:
            start_ms:
            end_ms:

        Returns:

        """
        df = self.df(run, start_ms, end_ms)
        battery = df.only("battery_name")
        stimframes = self.stimframes(battery, start_ms, end_ms, audio_waveform=True)
        stimplotter = StimframesPlotter()
        heater = HeatPlotter(
            stimframes_plotter=stimplotter, name_sep_line=self.zheat_show_name_lines
        )
        return heater.plot(df, stimframes, starts_at_ms=start_ms, battery=battery)

    def projection(
        self,
        run: QsLike,
        transform: WellTransform,
        *,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
        path_stub: Optional[PathLike] = None,
    ) -> Tup[WellFrame, Figure]:
        """
        Applies a projection transformation into 2D
        and plots as a scatter plot.
        For example, t-SNE, UMAP, or PCA.
        Saves alongside:

        - ``{path_stub}.transform.feather`` (projected feature data)
        - ``{path_stub}.transform.json`` (metadata)
        - ``{path_stub}.transform.pdf`` (2D plot figure)

        Args:
            run:
            transform:
            start_ms:
            end_ms:
            path_stub:

        Returns:
            A tuple of (transformed ``WellFrame``, ``Figure``)
        """
        df = self.df(run, start_ms=start_ms, end_ms=end_ms)
        trans = transform.fit(df)
        if path_stub is not None:
            path_stub = Path(path_stub)
            feather_path = path_stub.with_suffix(".transform.feather")
            pdf_path = path_stub.with_suffix(".transform.pdf")
            trans.reset_index().to_feather(feather_path)
            logger.info(f"Saved {feather_path}")
        recolor = "color" not in df.index_names() or len(df["color"].unique()) == 1
        figure = WellPlotters.basic(trans, recolor=recolor)
        if path_stub is not None:
            # noinspection PyUnboundLocalVariable
            FigureSaver().save(figure, pdf_path)
        return trans, figure

    def classify(
        self,
        run: QsLike,
        save_dir: PathLike,
        *,
        model_fn: SklearnWfClassifierWithOob = WellForestClassifier,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
        sort: bool = True,
        **kwargs,
    ) -> WellForestClassifier:
        """


        Args:
            run:
            save_dir:
            model_fn:
            start_ms:
            end_ms:
            sort:
            **kwargs:

        Returns:

        """
        save_dir = Tools.prepped_dir(save_dir, exist_ok=False)
        class_path = ClassifierPath(save_dir)
        df = self.df(run, start_ms=start_ms, end_ms=end_ms)
        model = model_fn.build(**kwargs)
        if class_path.exists():
            logger.info(f"Loading existing model at {save_dir}")
            model.load(save_dir)
        else:
            model.train(df)
        if len(df["color"].unique()) == 1:
            controls = df.with_controls().sort_values("control_type")
            label_colors = InternalVizTools.assign_color_dict_x(
                controls.names(), controls["control_type"]
            )
        else:
            label_colors = None
        model.save_to_dir(save_dir, figures=True, sort=sort, label_colors=label_colors)
        # now let's color a confusion matrix
        FigureTools.clear()
        return model

    def sensor_plots(
        self,
        run: RunLike,
        sensors: Optional[Sequence[Union[SensorNames, str]]] = None,
    ) -> Figure:
        """


        Args:
            run:
            sensors:

        Returns:

        """
        run = Tools.run(run, join=True)
        battery = run.experiment.battery
        if sensors is None:
            sensors = [SensorNames.PHOTOSENSOR, SensorNames.THERMOSENSOR, SensorNames.MICROPHONE]
        stimframes = self.stimframes(run.experiment.battery, None, None, audio_waveform=True)
        stimplotter = StimframesPlotter(audio_waveform=True)
        sensor_data = []
        for sensor in sensors:
            if isinstance(sensor, str):
                sensor = SensorNames[sensor]
            if sensor == SensorNames.MICROPHONE or sensor == SensorNames.MICROPHONE_WAVEFORM:
                waveform = self.sensor_cache.load_waveform(run)
                # do NOT slice: already done in waveform
                sensor_data.append(waveform)
            elif sensor.is_time_dependent:
                sdata = self.sensor_cache.load((sensor, run))
                sensor_data.append(sdata)
            else:
                raise TypeError(f"Sensor {sensor} is not time-dependent)")
        logger.error(f"Types are {[type(s) for s in sensor_data]}")
        return SensorPlotter(stimplotter=stimplotter, quantile=self.quantile).diagnostics(
            run, stimframes, battery, sensor_data
        )

    def durations(self, runs: RunsLike, kind: DurationType) -> Figure:
        """


        Args:
            runs:
            kind:

        Returns:

        """
        return RunDurationPlots.of(runs, kind)

    def timeline(
        self,
        runs: QsLike,
        label_with: Union[str, TimelineLabelType] = TimelineLabelType.TIMES,
        *,
        use_experiments: bool = True,
        **kwargs,
    ) -> Figure:
        """


        Args:
            runs:
            label_with:
            use_experiments:
            **kwargs:

        Returns:

        """
        return TimelinePlots.of(runs, label_with, use_experiments=use_experiments, **kwargs)

    def stimframes_plot(
        self,
        battery: Union[StimFrame, Batteries, int, str],
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
        *,
        label_assays: bool = False,
        stimframes: Optional[BatteryStimFrame] = None,
    ) -> Figure:
        """


        Args:
            battery:
            start_ms:
            end_ms:
            label_assays:
            stimframes: If supplied:
                - ``audio_waveform`` is ignored
                - ``start_ms`` and ``end_ms`` will be attempted, BUT!
                   If ``stimframes`` was already sliced, the result will be wrong

        Returns:

        """
        battery = Batteries.fetch(battery)
        assays = AssayFrame.of(battery)
        audio_waveform = self.enable_audio_waveform and not ValarTools.battery_is_legacy(battery)
        if stimframes is None:
            stimframes = self.stimframes(battery, start_ms, end_ms, audio_waveform=None)
        else:
            stimframes = stimframes.slice_ms(battery, start_ms, end_ms)
        plotter = StimframesPlotter(audio_waveform=audio_waveform, assay_labels=label_assays)
        ax = plotter.plot(stimframes, battery, assays=assays, starts_at_ms=start_ms)
        return ax.get_figure()

    def assays(self, battery: Union[Batteries, int, str]) -> AssayFrame:
        """


        Args:
            battery:

        Returns:

        """
        return AssayFrame.of(battery)

    def apps(self, battery: Union[Batteries, int, str]) -> AppFrame:
        """

        Args:
            battery:

        Returns:

        """
        return AppFrame.of(battery)

    def stimframes(
        self,
        battery: BatteryLike,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
        *,
        audio_waveform: Optional[bool] = False,
    ) -> BatteryStimFrame:
        """
        Get a BatteryStimFrame for a battery

        Args:
            battery: A battery name, ID, or instance
            start_ms: The milliseconds after the first frame to slice starting at, or None to mean 0; uses the ideal framerate
            end_ms: The milliseconds after the first frame to slice until, or None to mean the feature end; uses the ideal framerate
            audio_waveform: Replace the audio stimuli with the values of a standardized waveform; great for plotting. Generally only useful for plotting. If None then set True iff the battery is SauronX.

        Returns:
            BatteryStimFrame

        """
        battery = Batteries.fetch(battery)
        if audio_waveform is None:
            audio_waveform = not ValarTools.battery_is_legacy(battery)
        if audio_waveform:
            stimframes = self._expanded_stim_cache.load(battery)
        else:
            stimframes = self.stim_cache.load(battery)
        return stimframes.slice_ms(battery, start_ms, end_ms)

    def df(
        self,
        run: QsLike,
        *,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
    ) -> WellFrame:
        """
        Gets a WellFrame from any of:
            - A run ID, name, tag, or instance, or submission hash or instance
            - An iterable of any of the above
            - A WellFrame or DataFrame to be converted to a WellFrame

        If a WellFrame is passed, will return it immediately if no options are passed.
        For example, will only autofix if the DataFrame is fetched from a cache or Valar.
        More details are below.

        Rules for setting the WellFrame names:
            - In every case, will set the name column if ``namer`` is passed.
            - If ``namer`` is not set and ``run`` is a WellFrame or DataFrame, will keep the names of the passed WellFrame
            - If ``namer`` is not set and ``run`` is neither of those, will set the names with ``self.default_namer``.

        Rules about sorting:
            - If ``run`` is a WellFrame or DataFrame, will keep its sorting
            - Otherwise will call ``WellFrame.sort_std``.

        Applying fixes and checks:
            1) If ``self.enable_checks`` is True, will output warnings about the data to stdout.
            2) If ``self.auto_fix`` is True, will apply data standardization and fixes. These will happen after slicing (if applicable).
            2) If ``self.discard_trash_controls`` is not False, will discard those wells (if fresh).

        Args:
            run: Any of the above
            start_ms: The milliseconds after the first frame to slice starting at, or None to mean 0; uses the ideal framerate
            end_ms: The milliseconds after the first frame to slice until, or None to mean the feature end; uses the ideal framerate

        Returns:
            The WellFrame

        """
        return self._df(run, start_ms, end_ms)

    def errors(self, df: WellFrame) -> None:
        """
        Raises errors for issues with this WellFrame.
        Called internally by ``Quick.df``, but may also be useful outside.

        Args:
            df: WellFrame:

        Raises:
            MultipleGenerationsError: raises IncompatibleGenerationError

        """
        used_generations = {ValarTools.generation_of(run) for run in df.unique_runs()}
        if len(used_generations) > 1:
            raise MultipleGenerationsError(
                f"Got multiple generations in quick.df {used_generations}"
            )
        used_generation = next(iter(used_generations))
        if used_generation is not self.generation:
            raise IncompatibleGenerationError(
                f"Wrong generation {used_generation}; expected {self.generation}"
            )

    def write_concerns(
        self,
        wheres: ExpressionsLike,
        *,
        min_severity: Severity = Severity.GOOD,
        as_of: Optional[datetime] = None,
        path: Optional[PathLike] = None,
    ) -> Sequence[Concern]:
        """
        Finds ``Concern``s on runs matching the conditions ``wheres`` (which are processed by ``Quick.query_runs``).
        Saves the information as a CSV spreadsheet periodically (every 10 runs) while processing.

        Args:
            wheres:
            min_severity:
            as_of:
            path:

        Returns:

        """
        q0 = self.using(
            enable_checks=False, auto_fix=False, as_of=datetime.now() if as_of is None else as_of
        )
        runs = q0.query_runs(wheres)
        logger.notice(f"Spitting issues for {len(runs)} runs")
        coll = SimpleConcernRuleCollection(q0.feature, q0.sensor_cache, as_of, min_severity)
        concerns = []
        for i, run in enumerate(LoopTools.loop(runs, log=logger.info, every_i=10)):
            try:
                df = q0.df(run)
                concerns.extend(list(coll.of(df)))
            except Exception as e:
                concerns.append(
                    LoadConcern(run, Severity.CRITICAL, e, traceback.extract_tb(e.__traceback__))
                )
            if i % 10 == 0 and path is not None:
                Concerns.to_df(concerns).to_csv(path)
        if path is not None:
            Concerns.to_df(concerns).to_csv(path)
        return concerns

    def query_runs(self, wheres: Union[RunsLike, ExpressionsLike]) -> List[Runs]:
        """


        Args:
            wheres:

        Returns:
            The following tables are joined on.
            Runs, Experiments, Projects, ProjectTypes, Batteries, Submissions, SauronConfigs, Saurons, Users, Plates
            Ex: ``query_runs([Batteries.id == 99, Saurons.id == 4)]``

        """
        wheres = InternalTools.listify(wheres)
        try:
            # select while joining on the tables below
            wheres = Runs.id << {r.id for r in Tools.runs(wheres)}
        except Exception:
            pass
        query = (
            Runs.select(
                Runs,
                Experiments,
                Projects,
                ProjectTypes,
                Batteries,
                Submissions,
                SauronConfigs,
                Saurons,
                Users,
                Plates,
            )
            .join(Experiments)
            .join(Projects)
            .join(ProjectTypes, JOIN.LEFT_OUTER)
            .switch(Experiments)
            .join(Batteries)
            .switch(Runs)
            .join(Submissions, JOIN.LEFT_OUTER)
            .switch(Runs)
            .join(SauronConfigs)
            .join(Saurons)
            .switch(Runs)
            .join(Users)
            .switch(Runs)
            .join(Plates)
        )
        for where in wheres:
            query = query.where(where)
        return list(query)

    def log_concerns(self, df: WellFrame, min_severity: Severity = Severity.CAUTION) -> None:
        """
        Emit logger messages for concerns in this WellFrame, only for level >= ``min_severity``.
        Also see ``Quick.concerns``.

        Args:
            df:
            min_severity:

        Returns:

        """
        c = Concerns.of(df, self.feature, self.sensor_cache, as_of=None, min_severity=min_severity)
        Concerns.log_warnings(c)

    def fix(self, df):
        """
        Applies fixes.
        These are performed automatically when ``auto_fix=True``.
        These fixes are:
            - 0s between assays for legacy run
            - NaN "unification": If any well has a NaN in a position, sets all wells to have NaN there
            - Discarding "trash" wells, IF discard_trash is set

        Args:
            df:

        Returns:

        """
        if (
            self.auto_fix
            and self.feature is not None
            and self.feature.time_dependent
            and self.generation in [DataGeneration.PIKE_LEGACY, DataGeneration.PIKE_MGH]
        ):
            # This block deals with a weird problem in legacy data:
            # Because there were hidden gaps of time between assays, the value at the start of each assay
            # was set to 0. This is weird for analysis and plotting.
            # To fix it, we'll use WellFrame.completion to fill in these gaps.
            # _BUT_: WellFrame.completion needs to fill 0s AND NaNs.
            # If there are missing frames at the end represented as NaNs, we want to leave them alone.
            # So, replace the NaNs with -1.0, then call WellFrame.completion, then fill the NaNs again.
            # For simplicity, we'll do all three steps even if there are no assay gaps.
            n_unified = df.unify_last_nans_inplace(fill_value=-1.0)
            if self.feature.internal_name == FeatureTypes.MI.internal_name:
                n_zeros = (df.values == 0).astype(int).sum()
                if n_zeros.any() > 0:
                    logger.warning("MI trace contains 0s and might have breaks between assays.")
                    #df = WellFrame.retype(df.completion().replace(-1.0, np.NaN))
            if n_unified > 0:
                logger.warning(f"Unified {n_unified} NaNs at the end")
            df = WellFrame.retype(df.fillna(0))
        elif self.auto_fix:
            # if the feature is not interpolated, n_unified_start will always be 0
            n_unified_start = df.unify_first_nans_inplace(0)
            n_unified_end = df.unify_last_nans_inplace(0)
            if n_unified_start > 1 or n_unified_end > 1:
                logger.warning(
                    "Unified {} {} at the start and {} at the end".format(
                        n_unified_start, "NaNs" if n_unified_start > 1 else "NaN", n_unified_end
                    )
                )
        n = len(df)
        if len(self.discard_controls) > 0:
            df = df.without_controls(names=self.discard_controls)
            if len(df) != n:
                logger.caution(f"Discarded {len(df) - n} trash controls")
        return df

    def _df(
        self,
        run: QsLike,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
    ) -> WellFrame:
        """


        Args:
            run:
            start_ms:
            end_ms:

        Returns:

        """
        try:
            df, is_fresh = self._fetch_df(run)
            if is_fresh:
                # note that adding compound_names only when is_fresh can lead to unexpected results
                # I don't see a better alternative though
                if self.compound_namer is not None:
                    df = df.with_new_compound_names(self.compound_namer)
                # MAKE SURE to check for errors and warnings BEFORE slicing or fixing
                self.errors(df)
                if self.enable_checks:
                    self.log_concerns(df, min_severity=self.min_log_severity)
                df = df.slice_ms(start_ms, end_ms)
                if self.auto_fix:
                    df = self.fix(df)
            else:
                # we still need to slice it if it's not fresh
                df = df.slice_ms(start_ms, end_ms)
            df = df.with_new_names(self.well_namer)
            df = df.with_new("display_name", df["name"])
        except NoFeaturesError as err:
            # we can't raise in an except block or we'll get a "During handling of the above exception"
            if isinstance(err, NoFeaturesError):
                msg = self._no_such_features_message(run)
                raise NoFeaturesError(msg) from None
            else:
                raise err
        return df

    def _no_such_features_message(self, run) -> str:
        """


        Args:
            run:

        """
        if isinstance(run, (str, int, float, Runs, Submissions)):
            return "The feature {} is not defined on run r{}. These are: {}".format(
                self.feature, run, ", ".join(ValarTools.features_on(run))
            )
        elif isinstance(run, ExpressionLike):
            with Tools.silenced(no_stdout=True, no_stderr=False):
                x = WellFrameBuilder(self.as_of).where(run).build().unique_runs()
            feats_map = {r: ValarTools.features_on(r) for r in x}
            missing = [
                "r" + str(k)
                for k, v in feats_map.items()
                if self.feature.valar_feature.name not in v
            ]
            return "The feature {} is not defined on runs {}.".format(
                self.feature, ",".join(missing)
            )
        else:
            feats_defined = (
                "["
                + "; ".join(
                    [
                        "r" + str(Runs.fetch(r)) + ": " + ", ".join(ValarTools.features_on(r))
                        for r in run
                    ]
                )
                + "]"
            )
            return "The feature {} is not defined on runs {}. These are: {}".format(
                self.feature,
                ",".join(["r" + str(r.id) for r in ValarTools.runs(run)]),
                feats_defined,
            )

    def _fetch_df(self, run) -> Tup[WellFrame, bool]:
        """


        Args:
            run:

        Returns:

        """
        # ignore limit and generation if fresh
        if isinstance(run, WellFrame) or isinstance(run, pd.DataFrame):
            return WellFrame.of(run), False
        # If namer= was passed, it will be used in df()
        # For now, use default_namer if a WellFrame (or WellFrame in disguise) wasn't passed
        # Otherwise, use what was already there
        # If it's a WellFrame or dataframe, leave it alone
        # Ok, great. Now build from the appropriate place
        if isinstance(run, ExpressionLike):
            run = [run]
        is_expression = Tools.is_true_iterable(run) and all(
            (isinstance(r, ExpressionLike) for r in run)
        )
        if is_expression and self.as_of is None:
            raise RefusingRequestError(
                "Will not fetch from flexible queries unless Quick.as_of is set."
            )
        elif is_expression:
            df = CachingWellFrameBuilder(self.cache, self.as_of).where(run).build()
        elif self.cache is not None:
            df = self.cache.load(run)
        else:
            df = (
                WellFrameBuilder.runs(run)
                .with_sensor_cache(self.sensor_cache)
                .with_feature(self.feature)
                .build()
            )
        # instead, we'll build the names in Quick.df()
        df = df.with_new_names(self.well_namer)
        df = df.with_new("display_name", self.well_namer)
        return df.sort_standard(), True

    def _everything(self, run, start_ms, end_ms, control_names, control_types, weights):
        """
        Only for plotting.

        Args:
            run:
            start_ms:
            end_ms:
            control_names:
            control_types:
            weights:

        Returns:

        """
        df = self.df(run, start_ms=start_ms, end_ms=end_ms)
        battery = df.only("battery_name")
        stimframes = self.stimframes(battery, start_ms, end_ms, audio_waveform=True)
        control_names = self._control_names(df, control_names, control_types)
        fps = Tools.only((ValarTools.frames_per_second(run) for run in df.unique_runs()))
        weights = self._slice_weight_ms(df, weights, start_ms, end_ms)
        extra_gs, extra_fn = self._weighter(weights)
        stimplotter = StimframesPlotter(assay_labels=self.label_assays, audio_waveform=True)
        assays = AssayFrame.of(battery)
        return df, stimframes, assays, control_names, fps, stimplotter, extra_gs, extra_fn

    def _control_names(self, df, control_names, control_types):
        if control_names is not None and control_types is not None:
            raise ContradictoryRequestError("Can't supply both control_names and control_types")
        if control_types is not None:
            control_names = df.with_controls(names=control_types).unique_names()
        if control_names is None:
            control_names = df.with_controls().unique_names()
        return control_names

    def _control_subtract(
        self,
        df: WellFrame,
        control_type: Optional[str],
        control_name: Optional[str],
        subtraction=None,
    ) -> WellFrame:
        # use z-score by default
        if subtraction is None:
            subtraction = lambda case, control: (case - control.mean()) / case.std()
        # handle main cases: both, name, type, or neither
        if control_name is not None and control_type is not None:
            raise ContradictoryRequestError(
                f"Can only use control_type OR control_name; got {control_type} and {control_name}"
            )
        elif control_name is not None:
            return df.name_subtract(subtraction, control_name)
        elif control_type is not None:
            return df.control_subtract(subtraction, control_type)
        else:
            control_type = Tools.only(df.unique_controls_matching(positive=False))
            return df.control_subtract(subtraction, control_type)

    def _weighter(self, weights: Optional[np.array]):
        if weights is None:
            return None, None
        else:
            importer = ImportancePlotter()
            return (
                [1],
                lambda f, gs, name: importer.plot(weights, f.add_subplot(gs[1], sharex=f.axes[0])),
            )

    def _slice_weight_ms(
        self,
        df: WellFrame,
        weights: Optional[np.array],
        start_ms: Optional[int],
        end_ms: Optional[int],
    ):
        if weights is None:
            return None
        fpses = {ValarTools.frames_per_second(r) for r in df["run"].unique()}
        assert len(fpses) == 1, str(len(fpses))
        fps = next(iter(fpses))
        return weights[
            None
            if start_ms is None
            else int(np.floor(start_ms * fps / 1000)) : None
            if end_ms is None
            else int(np.ceil(end_ms * fps / 1000))
        ]

    def delete(self, runs: Union[RunsLike, peewee.Query, ExpressionLike]) -> None:
        """
        Deletes one or more runs from self.facade (if it exists) or self.cache (if it exists).
        Does nothing if neither is defined.
        """
        if isinstance(runs, peewee.Query):
            runs = list(runs)
        elif isinstance(runs, ExpressionLike):
            runs = self.query_runs(runs)
        else:
            runs = Tools.runs(runs)
        if not all([isinstance(r, Runs) for r in runs]):
            raise XTypeError("Bad query type")
        for run in runs:
            if self.cache is not None:
                self.cache.delete(run)
        logger.notice(f"Deleted {len(runs)} run(s) from the cache(s)")

    def __repr__(self):
        if self.as_of is None:
            return f"Quick({self.feature})"
        else:
            return f"Quick({self.feature} @ {str(self.as_of)[:-3]})"

    def __str__(self):
        return repr(self)


@abcd.external
class Quicks:
    """ """

    @classmethod
    def pointgrey(cls, as_of: Optional[datetime], **kwargs):
        """


        Args:
            as_of: Optional[datetime]:
            **kwargs:

        Returns:

        """
        return cls.choose(DataGeneration.POINTGREY, as_of=as_of, **kwargs)
    @classmethod
    def pointgrey_alpha(cls, as_of: Optional[datetime], **kwargs):
        return cls.choose(DataGeneration.POINTGREY_ALPHA, as_of=as_of, **kwargs)
    @classmethod
    def new(cls, as_of: Optional[datetime], **kwargs):
        """


        Args:
            as_of: Optional[datetime]:
            **kwargs:

        Returns:

        """
        kwargs = dict(kwargs)
        generation = DataGeneration.POINTGREY
        if "generation" in kwargs:
            generation = kwargs.pop("generation")
        return cls.choose(generation, as_of=as_of, **kwargs)

    @classmethod
    def legacy_pike_sauronx(cls, as_of: Optional[datetime], **kwargs):
        """


        Args:
            as_of: Optional[datetime]:
            **kwargs:

        Returns:

        """
        return cls.choose(DataGeneration.PIKE_SAURONX, as_of=as_of, **kwargs)

    @classmethod
    def legacy_pike_legacy(cls, as_of: Optional[datetime], **kwargs):
        """


        Args:
            as_of: Optional[datetime]:
            **kwargs:

        Returns:

        """
        return cls.choose(DataGeneration.PIKE_LEGACY, as_of=as_of, **kwargs)

    @classmethod
    def legacy_pike_mgh(cls, as_of: Optional[datetime], **kwargs):
        """


        Args:
            as_of: Optional[datetime]:
            **kwargs:

        Returns:

        """
        return cls.choose(DataGeneration.PIKE_MGH, as_of=as_of, **kwargs)

    @classmethod
    def choose(cls, generation: Union[str, DataGeneration], as_of: Optional[datetime], **kwargs):
        """


        Args:
            generation:
            as_of: Optional[datetime]:
            **kwargs:

        Returns:

        """
        generation = DataGeneration.of(generation)
        kwargs = dict(kwargs)
        feature = (
            kwargs.pop("feature")
            if "feature" in kwargs
            else generation_feature_preferences[generation]
        )
        if "namer" in kwargs and "well_namer" not in kwargs:
            kwargs["well_namer"] = kwargs["namer"]
            del kwargs["namer"]  # it's ok -- this is already a copy
        sensor_cache = SensorCache()
        audio_stimulus_cache = AudioStimulusCache()
        return Quick(
            feature,
            generation,
            as_of,
            cache=WellCache(feature).with_sensor_cache(sensor_cache),
            stim_cache=StimframeCache(),
            sensor_cache=sensor_cache,
            video_cache=VideoCache(),
            audio_stimulus_cache=audio_stimulus_cache,
            **kwargs,
        )


__all__ = ["Quick", "Quicks", "AggType"]

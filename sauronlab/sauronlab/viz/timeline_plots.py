from dataclasses import dataclass

from matplotlib import dates as mdates

from sauronlab.core.core_imports import *
from sauronlab.model.metrics import *
from sauronlab.viz._internal_viz import *
from sauronlab.viz.figures import *


class TimelineLabelType(SmartEnum):
    """"""

    NONE = enum.auto()
    TIMES = enum.auto()
    RUNS = enum.auto()
    PLATES = enum.auto()
    TAGS = enum.auto()
    DESCRIPTIONS = enum.auto()

    def process(self, runs: RunsLike) -> Optional[Sequence[str]]:
        """


        Args:
            runs: RunsLike:

        Returns:

        """
        runs = Tools.runs(runs)
        if self is TimelineLabelType.NONE:
            return ["" for _ in runs]
        elif self is TimelineLabelType.TIMES:
            return None
        elif self is TimelineLabelType.RUNS:
            return ["r" + str(r.id) for r in runs]
        elif self is TimelineLabelType.PLATES:
            return ["p" + str(r.plate_id) for r in runs]
        elif self is TimelineLabelType.TAGS:
            return [str(r.tag) for r in runs]
        elif self is TimelineLabelType.DESCRIPTIONS:
            return [str(r.description) for r in runs]
        else:
            raise XTypeError(str(self))


class DurationType(SmartEnum):
    """"""

    WAIT = enum.auto()
    TREATMENT = enum.auto()
    ACCLIMATION = enum.auto()
    TREATMENT_TO_START = enum.auto()
    PLATING_TO_START = enum.auto()

    @property
    def description(self) -> str:
        """

        Returns:

        """
        if self is DurationType.TREATMENT_TO_START:
            return "time since treatment (min)"
        elif self is DurationType.PLATING_TO_START:
            return "time since plating (min)"
        else:
            return self.name.lower() + " duration"

    def get_seconds(self, run: RunLike) -> float:
        """


        Args:
            run: RunLike:

        Returns:

        """
        run = Tools.run(run, join=True)
        if self is DurationType.WAIT:
            return ValarTools.wait_sec(run)
        elif self is DurationType.TREATMENT:
            return ValarTools.treatment_sec(run)
        elif self is DurationType.ACCLIMATION:
            return run.acclimation_sec
        elif self is DurationType.TREATMENT_TO_START:
            return ValarTools.treatment_sec(run) + run.acclimation_sec
        elif self is DurationType.PLATING_TO_START:
            return ValarTools.treatment_sec(run) + ValarTools.wait_sec(run) + run.acclimation_sec
        else:
            raise XTypeError(str(self))


@dataclass(frozen=True)
class TimelinePlotter(KvrcPlotting):
    """
    Plots timelines, mostly for when plates were run.
    Colors are assigned per experiment, with a legend label each.

    Attributes:
        use_times: Sets the y-values to the actual times; great for precision but tends to require a large height
        date_format:
        x_locator:
        n_rows: int
    """

    use_times: bool = False
    date_format: str = "%Y-%m-%d"
    x_locator = mdates.DayLocator()
    n_rows: int = 10

    def plot(
        self,
        dates: Sequence[datetime],
        experiments: Optional[Sequence[str]] = None,
        labels: Optional[Sequence[str]] = None,
    ) -> Figure:
        """


        Args:
            dates:
            experiments:
            labels:

        Returns:

        """
        # fill in default values
        if experiments is None:
            experiments = ["" for _ in dates]
        if labels is None:
            labels = [
                str(idate.hour).zfill(2) + ":" + str(idate.minute).zfill(2) for idate in dates
            ]
        # sort
        data = sorted(list(Tools.zip_strict(dates, experiments)), key=lambda t: t[0])
        dates, experiments = [t[0] for t in data], [t[1] for t in data]
        # get colors
        if len(set(experiments)) > 1:
            colors = InternalVizTools.assign_colors_x(experiments, [None for _ in experiments])
        else:
            colors = ["black" for _ in experiments]
        # get min and max datetimes
        mn, mx = min(dates), max(dates)
        mn = datetime(mn.year, mn.month, mn.day, 0, 0, 0)
        mx = datetime(mx.year, mx.month, mx.day + 1, 0, 0, 0)
        halfway = mn + (mx - mn) / 2
        figure = plt.figure()
        ax = figure.add_subplot(1, 1, 1)
        ###############
        # plot
        ###############
        # the y_index will get reset to 0 each day
        y_index, last_date = 0, dates[0]
        for idate, iexp, icolor, ipretty in Tools.zip_list(dates, experiments, colors, labels):
            # reset so that the level always starts at 0 for each day
            if (
                idate.year != last_date.year
                or idate.month != last_date.month
                or idate.day != last_date.day
            ):
                y_index = 0
            # get the actual y-value in coordinates
            if self.use_times:
                y_val = idate.hour + idate.minute / 60
            else:
                y_val = (y_index % self.n_rows) - self.n_rows // 2
            # plot the markers
            ax.scatter(
                idate,
                y_val,
                marker=sauronlab_rc.timeline_marker_shape,
                s=sauronlab_rc.timeline_marker_size,
                c=icolor,
                alpha=1,
            )
            # weirdly, excluding this breaks everything
            ax.plot((idate, idate), (0, y_val), alpha=0)
            # show text
            horizontalalignment = "left" if idate < halfway else "right"
            xpos_offset = int(sauronlab_rc.timeline_marker_size / 10)  # about right emperically
            xpos = idate + timedelta(
                hours=(xpos_offset if horizontalalignment == "left" else -xpos_offset)
            )
            ax.text(
                xpos,
                y_val,
                ipretty,
                horizontalalignment=horizontalalignment,
                verticalalignment="center",
            )
            y_index += 1
            last_date = idate
        # fix x ticks / locations / labels
        ax.xaxis.set_major_locator(self.x_locator)
        ax.xaxis.set_major_formatter(mdates.DateFormatter(self.date_format))
        ax.set_xlim(mn, mx)
        # remove y tick labels if they're just ordered
        if not self.use_times:
            ax.get_yaxis().set_ticks([])
        # fix x tick labels
        for x in ax.get_xticklabels():
            x.set_rotation(90)
            x.set_ha("center")
        # legend for experiments
        if any((e != "" for e in experiments)):
            FigureTools.manual_legend(ax, experiments, colors)
        return figure


class TimelinePlots:
    """"""

    @classmethod
    def of(
        cls,
        runs: RunsLike,
        label_with: Union[str, TimelineLabelType],
        use_experiments=True,
        **kwargs,
    ) -> Figure:
        """


        Args:
            runs: param label_with: How to label individual runs; common choices are 'runs', 'plates', and 'times'.
            use_experiments: If True, chooses a different color (and legend item) per exeriment (Default value = True)
            kwargs: These are passed to the ``TimelinePlotter`` constructor
            runs:
            label_with:
            **kwargs:

        Returns:

        """
        runs = Tools.runs(runs)
        labels = TimelineLabelType.of(label_with).process(runs)
        experiments = [r.experiment.name for r in runs] if use_experiments else ["" for _ in runs]
        dates = [r.datetime_run for r in runs]
        # Good example: BioMol plate BM-2811, master. Drugs: adrenergic
        figure = TimelinePlotter(**kwargs).plot(dates, experiments, labels=labels)
        return figure


@dataclass(frozen=True)
class RunDurationPlotter:
    """
    Plotters for durations between events like treatment and running (a plate).
    """

    attribute: str

    def plot(self, kde_in_minutes: KdeData) -> Figure:
        """


        Args:
            kde_in_minutes:

        Returns:

        """
        figure = plt.figure()
        ax = figure.add_subplot(1, 1, 1)
        minute_durations, support, density = (
            kde_in_minutes.samples,
            kde_in_minutes.support,
            kde_in_minutes.density,
        )
        ax.plot(support, density, color="black", alpha=0.9)
        ax.plot(minute_durations, np.zeros(len(minute_durations)), "|", color="#0000aa")
        ax.set_ylabel("N runs")
        ax.set_yticks([])
        ax.set_yticklabels([])
        ax.set_xlabel(self.attribute)
        if len({m for m in minute_durations if m < 0}) > 0:
            logger.error(f"Some {self.attribute} durations are negative")
        ax.set_xlim(0, None)
        return ax.get_figure()


class RunDurationPlots:
    """"""

    @classmethod
    def of(
        cls,
        runs: RunsLike,
        kind: Union[DurationType, str],
        kde_params: Optional[Mapping[str, Any]] = None,
    ) -> Figure:
        """


        Args:
            runs: RunsLike:
            kind:
            kde_params:

        Returns:

        """
        t = DurationType.of(kind)
        minutes = [t.get_seconds(r) for r in Tools.runs(runs)]
        kde = KdeData.from_samples(minutes, **({} if kde_params is None else kde_params))
        return RunDurationPlotter(t.description).plot(kde)


__all__ = [
    "TimelinePlotter",
    "RunDurationPlotter",
    "TimelineLabelType",
    "TimelinePlots",
    "DurationType",
    "RunDurationPlots",
]

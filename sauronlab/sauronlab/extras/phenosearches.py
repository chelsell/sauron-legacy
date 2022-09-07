from __future__ import annotations

from scipy.spatial import distance

from sauronlab.core.core_imports import *
from sauronlab.model.app_frames import *
from sauronlab.model.cache_interfaces import ASensorCache
from sauronlab.model.compound_names import *
from sauronlab.model.features import *
from sauronlab.model.stim_frames import *
from sauronlab.model.well_names import *
from sauronlab.model.wf_builders import *


class HitFrame(TypedDf):
    @classmethod
    def reserved_columns(cls):
        """ """
        return ["run_name", "run_id", "well_id", "well_label", "score"]

    def with_runs(self, runs: RunsLike) -> HitFrame:
        runs = [r.id for r in Tools.runs(runs)]
        return HitFrame(self[self["run"].isin(runs)])


@abcd.auto_eq()
@abcd.auto_repr_str()
@abcd.auto_info()
class HitSearch:
    """
    A simple interface for "phenosearching": calculating scores over an interator of target wells.
    The primary score can be any function of the feature array, such as the mean, or the negative L1 distance to a query well.
    Secondary scores can also be added, each with a name and its own functions; these will be included in the output.
    Use as a builder pattern, then call HitSearch.search() to get a HitFrame object back.
    The scores should always be such that more positive is better.
    Alternatively, you can call HitSearch.iterate() to stream over the results, which are pd.Series containing the columns for HitFrame.
    Whether called with search(), will save every n results as a DataFrame .csv to disk (1000 by default).

    Example:
        .. code-block::

            search = HitSearch()\
                    .set_feature('MI')\
                    .set_primary_score(lambda arr, well: -np.abs(arr - prototypical).mean())\
                    .add_secondary_score('mean', lambda arr, well: np.mean(arr))\
                    .set_min_score(-150)\
                    .where(Experiments.id == 12)\
                    .set_save_every(10)\
                    .limit(1000)
            hits = search.search('query_results.csv')  # type: HitFrame

    """

    def __init__(self, as_of: datetime):
        self.as_of = as_of
        self.feature = FeatureTypes.MI
        self.wheres = []
        self.primary_score_fn = None
        self.secondary_score_fns = {}
        self._limit = None
        self._min_scores = {}
        self.save_every = 1000

    def set_save_every(self, n: int) -> HitSearch:
        """
        Save every ``n`` number of iterations. The default is 1000.
        """
        self.save_every = n
        return self

    def set_feature(self, feature: Union[FeatureType, str]) -> HitSearch:
        """
        Sets the feature.

        Args:
            feature: A FeatureType or its 'internal' name.
                     These are not just the feature names in Valar.
                     For example: "MI" is just non-interpolated MI, but "cd(10)_i" is interpolated cd(10).
                     When in doubt, you can pass in ``quick.feature``.
        """
        self.feature = FeatureTypes.of(feature)
        return self

    def where(self, expression: ExpressionLike) -> HitSearch:
        """
        Restrict the wells searched by a WHERE expression.

        Args:
          expression: A peewee WHERE expression such as ``Experiments.id == 1``
                      Can be an expression of Runs, Plates, Experiments, Projects, PlateTypes, Batteries,
                      SauronConfigs, or Saurons.
        """
        self.wheres.append(expression)
        return self

    def set_primary_score(self, function: Callable[[np.array, Wells], float]) -> HitSearch:
        """
        Sets the primary scoring function used. It will be included as a column called 'score' in the results.

        Args:
          function: A function that accepts a numpy array and a Wells valarpy instance and returns a single number
                    Make sure the function returns HIGHER values for BETTER scores.
                    If necessary you can modify the function to return the negative; ex
                    ``set_primary_score(lambda arr, well: -my_scoring_fn(arr, well))``
        """
        self.primary_score_fn = function
        return self

    def add_secondary_score(
        self, function: Callable[[np.array, Wells], float], name: str
    ) -> HitSearch:
        """
        Adds a secondary score, which will be included as an extra column.

        Args:
            function: The same format as in ``set_primary_score``
            name: The name that will be given to the column
        """
        if name in HitFrame.reserved_columns():
            raise ReservedError("Cannot use the name 'score', which is reserved")
        if name in self.secondary_score_fns:
            raise AlreadyUsedError(f"{name} is already used")
        self.secondary_score_fns[name] = function
        return self

    def set_min_score(self, value: float, name: str = "score") -> HitSearch:
        """
        After calculating the scores for a well, exclude it entirely if its score is below this value.

        Args:
            value: The minimum value. For primary scores, higher should always be better.
            name: score: for the primary score or the name of a secondary score
            value: float:
        """
        if name != "score" and (name not in self.secondary_score_fns):
            raise LookupFailedError(f"Score {name} was not found")
        self._min_scores[name] = value
        return self

    def limit(self, n: int) -> HitSearch:
        """
        Only search this number of wells. Stop abruptly after.
        This function is generally only used to help debug a phenosearch.
        """
        if n < 0:
            raise XValueError(f"Limit {n} is negative")
        self._limit = n
        return self

    def search(self, path: Optional[str] = None) -> HitFrame:
        """
        Perform the search over the whole query.
        Will save perodically in the background to file ``path`` if it is not None.

        Args:
            path: The file path; should end with '.csv'; if None will not save

        Returns:
            A HitFrame, a subclass of DataFrame
        """
        if self.primary_score_fn is None:
            raise OpStateError("Primary scoring function is not set")
        t0 = time.monotonic()
        results = []
        for i, hit in enumerate(self.iterate()):
            if i % self.save_every == 0 and i > 0:
                self._save_hits(results, path)
            results.append(hit)
        logger.info(
            "Finished in {} with {} hits".format(
                Tools.delta_time_to_str(time.monotonic() - t0), len(results)
            )
        )
        return self._save_hits(results, path)

    def _save_hits(self, results, path: Optional[str]) -> HitFrame:
        df = HitFrame(results)
        if path is not None:
            df.to_csv(path)
        logger.trace(f"Saved {len(results)} hits")
        return df

    def iterate(self) -> Iterator[pd.Series]:
        """
        A lower-level alternative to calling ``search``.
        Just returns an iterator over the Pandas Series that would be in the HitFrame when calling ``search``.
        Does NOT save the results periodically.

        Example:
            How to use::

                for series in search.iterate():
                    do_something(series)
        """
        for i, wf in enumerate(self._build_query()):
            for row in range(len(wf)):
                floats = wf.values[i]
                dct = dict(
                    well_id=wf["well"][row],
                    well_index=wf["well_index"][row],
                    run_id=wf["run"][row],
                    run_name=wf["run_name"],
                    score=self.primary_score_fn(floats, wf["well"][row]),
                )
                if "score" in self._min_scores and dct["score"] < self._min_scores["score"]:
                    continue
                failed = False
                for name, score in self.secondary_score_fns.items():
                    dct[name] = score(floats, wf.well)
                    if name in self._min_scores and dct[name] < self._min_scores[name]:
                        failed = True
                        break
                if not failed:
                    yield pd.Series(dct)

    def _build_query(self):
        builder = WellFrameBuilder(self.as_of)
        for where in self.wheres:
            builder = builder.where(where)
        if self._limit is not None:
            builder = builder.limit_to(self._limit)
        return builder.build()


class HitWellFrame(WellFrame):
    """ """

    @classmethod
    def build(cls, hits: HitFrame, namer: WellNamer = WellNamers.general()) -> HitWellFrame:
        """
        Converts a HitFrame into a HitWellFrame, which contains well info.
        """
        hitwells = set(hits.reset_index()["well_id"].unique())
        scores = hits.reset_index().set_index("well_id")["score"].to_dict()
        # no features
        hitdf = (
            WellFrameBuilder(None)
            .where(Wells.id << hitwells)
            .with_compound_names(CompoundNamers.tiered())
            .with_names(namer)
            .build()
        )
        hitdf[0] = hitdf["well"].map(lambda w: scores[w])
        return HitWellFrame(HitWellFrame.convert(hitdf))


class HitSearchTools:
    """ """

    @classmethod
    def stimuli_start_stop_ms(
        cls,
        battery: Union[int, str, Batteries],
        stimuli: Set[Union[int, str, Stimuli]],
        start: bool = True,
        stop: bool = True,
        min_duration_ms: float = 1000,
    ) -> Sequence[int]:
        """
        Get a list of the times in stimframes (milliseconds for sauronx)that one or more stimuli of interest changed value.
        If multiple stimuli are passed, does not differentiate. In other words, if red LED is on at 200, then the blue turns on at 255,
            that start will be included (subject to min_duration_ms).

        Args:
            battery: The name, ID, or instance of a battery
            stimuli: Either a stimulus or set of stimuli
            start: Include times the stimulus increased in pwm (or volume)
            stop: Include times the stimulus decreased in pwm or volume
            min_duration_ms: WARNING: Uses the stimframes themselves, which have 25-fps-based values in legacy

        Returns:
            Restrict to a number of milliseconds where the stimulus is unchaged before that value, and the same with after

        """
        apps = AppFrame.of(battery)
        if ValarTools.battery_is_legacy(battery):
            warn(
                "Getting stimulus start and stop positions for a legacy battery."
                "Make sure you're using 25-fps-based values for min_duration_ms instead of milliseconds."
            )
        if min_duration_ms < 0:
            raise XValueError(f"Duration must be >= 0; was {min_duration_ms}")
        stimuli = [s.name for s in Stimuli.fetch_all(stimuli)]
        positions = []
        apps = AppFrame(apps[apps["stimulus"].isin(stimuli)]).insight()
        since = 0  # ms since a transition (whether used or not)
        value = 0
        for row in apps.itertuples():
            if (
                start and row.value > value or stop and row.value < value
            ) and row.start_ms - since >= min_duration_ms:
                positions.append(row.start_ms)
                since = row.end_ms
            if stop and value > 0 and positions[-1] != row.end_ms:
                positions.append(row.end_ms)
                since = row.end_ms
            value = row.value
        return sorted(positions)

    @classmethod
    def triangle_weights(cls, stimframes: BatteryStimFrame, win_size: int = 1000) -> np.array:
        return stimframes.triangles(win_size).sum(axis=0).values


class TruncatingScorer:
    """
    Wraps a similarity score to a query trace into an HitSearch scoring function that truncates to min(query length, target length),
    and warning if the lengths differ by more than 3.

    Returns:
        A function mapping a feature array and a well row into a float where higher is better (more similar).
    """

    def __init__(self, query: np.array, similarity: Callable[[np.array, Wells], float]):
        """
        Constructor.

        Args:
            query: A time trace of MI or cd(10)
            similarity: Any function that computes a similarity between two arrays. If you have a distance function,
                        wrap it in ``lambda x, y: -distance(x, y)``"""
        self.query = query
        self.similarity = similarity
        self.problematic_wells = set()  # type: Set[Wells]
        self.problematic_runs = set()  # type: Set[Runs]
        self._max_missing = 3

    def __call__(self, target: np.array, well: Wells) -> float:
        n = min(len(target), len(self.query))
        if abs(len(target) - len(self.query)) > self._max_missing:
            if well.run not in self.problematic_runs:
                logger.warning(
                    "Mismatch of {} between query length {} and target for run r{} length {}".format(
                        len(target) - len(self.query), len(self.query), well.run_id, len(target)
                    )
                )
            self.problematic_wells.add(well)
            self.problematic_runs.add(well.run)
            trunc_query, trunc_target = target[0:n], self.query[0:n]
            return self.similarity(trunc_query, trunc_target)

    def __repr__(self):
        return (
            self.__class__.__name__
            + "("
            + Tools.pretty_function(self.similarity)
            + ",n="
            + str(len(self.query))
            + " @ "
            + hex(id(self))
            + ")"
        )

    def __str__(self):
        return repr(self)


class HitScores:
    @classmethod
    def pearson(
        cls, query: np.array, weights: Optional[np.array] = None
    ) -> Callable[[np.array, Wells], float]:
        def pearson(x, y):
            return distance.correlation(x, y, weights)

        return TruncatingScorer(query, pearson)

    @classmethod
    def minkowski(
        cls, query: np.array, p: float, weights: Optional[np.array] = None
    ) -> Callable[[np.array, Wells], float]:
        """
        Returns a scoring function corresponding to an distance distance (Lebesgue) for a degree p.
        Only permits positive p (even though zero and negative p have meanings in functional analysis).
        Accepts p=np.inf
        For example:
            - p=1 is Manhattan distance
            - p=2 is Euclidean distance
            - p=3 is a cubic distance
            - p=np.inf is the maximum
            - p=-np.inf is the minimum

        """
        if weights is None:
            weights = 1
        if p == 0:

            def similarity(x, y):
                return np.power(2, np.sum(np.log2(weights * np.abs(x - y))))  # TODO check

        elif np.isneginf(p):

            def similarity(x, y):
                return -np.min(weights * np.abs(x - y))

        elif np.isposinf(p):

            def similarity(x, y):
                return -np.max(weights * np.abs(x - y))

        else:

            def similarity(x, y):
                return -np.power(np.power(weights * np.abs(x - y), p).sum(), 1 / p)

        similarity.__name__ = f"-minkowski(p={p})"
        return TruncatingScorer(query, similarity)


__all__ = [
    "HitFrame",
    "HitSearch",
    "HitWellFrame",
    "HitSearchTools",
    "TruncatingScorer",
    "HitScores",
]

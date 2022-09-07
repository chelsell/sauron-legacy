"""
Ways to build iterators over comparisons between cases and controls.
"""
from __future__ import annotations

from sauronlab.core.core_imports import *
from sauronlab.core.tools import *
from sauronlab.model.well_frames import *


@abcd.auto_eq()
@abcd.auto_repr_str()
class ControlComparison:
    """
    A comparison between ``name`` and ``control`` for some repeat ``repeat``.
    This is intended to be used when many comparisons between wells are made.
    'Name' and 'control' can be any strings.
    'control' may simply reflect something 'different' from 'name' and not actually controls.

    Examples:
        - name=='optovin' and control=='solvent (-)'  where separation is a good thing
        - name=='optovin' and name=='optovin',        as a negative control experiment
        - name=='mk-801' and name=='ketamine',        where the result of the comparison indicates closeness

    """

    def __init__(self, name: str, control: str, repeat: int):
        """

        Args:
            name:
            control:
            repeat:
        """
        self.name, self.control, self.repeat = name, control, repeat

    def to_dict(self) -> Mapping[str, Any]:
        """"""
        return {"name": self.name, "control": self.control, "repeat": self.repeat}

    @property
    def directory(self) -> Path:
        """"""
        return Tools.sanitize_path_nodes([str(self.repeat), self.control, self.name], is_file=False)

    def __hash__(self):
        return hash((self.name, self.control, self.repeat, self.is_control))


@abcd.auto_repr_str(lambda s: s == "smalldf", lambda s: s == "smalldf", lambda s: s == "smalldf")
class TrainableCc:
    """
    An equivalent to ``ControlComparison`` that also contains an attribute ``smalldf``,
    which contains selected wells to intended for the comparison.
    ``smalldf`` always has exactly 2 ``name`` values (``len(smalldf.unique_names()) == 2``).

    """

    def __init__(self, name: str, control: str, repeat: int, smalldf: WellFrame):
        self.name, self.control, self.repeat = name, control, repeat
        self.smalldf = smalldf

    def info(self) -> Mapping[str, Any]:
        """ """
        names = self.smalldf.unique_names()
        replicates = {"\t::n:: " + k: v for k, v in self.smalldf.n_replicates().items()}
        runs = {"\t::runs:: " + name: self.smalldf.with_name(name).unique_runs() for name in names}
        groups = {
            "\t::groups:: " + name: self.smalldf.with_name(name)["well_group"].unique().values
            for name in names
        }
        packs = {
            "\t::packs:: " + name: self.smalldf.with_name(name)["pack"].unique().values
            for name in names
        }
        ctypes = {
            "\t::controls:: " + name: self.smalldf.with_name(name)["control_type"].unique().values
            for name in names
        }
        return {
            "name": self.name,
            "control": self.control,
            "repeat": self.repeat,
            "dir": str(self.directory),
            **replicates,
            **runs,
            **groups,
            **packs,
            **ctypes,
        }

    @property
    def directory(self) -> Path:
        """ """
        return Tools.sanitize_path_nodes([str(self.repeat), self.control, self.name], is_file=False)


class CcIterator(SizedIterator, metaclass=abc.ABCMeta):
    """
    Iterator over ``ControlComparison`` instances.
    """

    def __next__(self) -> ControlComparison:
        raise NotImplementedError()


class CcSelfIterator(CcIterator):
    """
    Iterator over name--name comparisons, where both values are the same. (Ex: 'optovin--optovin', then 'etomidate--etomidate').
    """

    def __init__(self, names: Iterable[str], n_repeats: int):
        self.__n_repeats = n_repeats
        self.__names = list(names)
        self.__i = -1

    def __next__(self) -> ControlComparison:
        self.__i += 1
        s, r = self.__names[self.__i % len(self.__names)], self.__i // len(self.__names)
        return ControlComparison(s, s, r)

    def position(self) -> int:
        """ """
        return self.__i

    def total(self) -> int:
        """ """
        return self.__n_repeats * len(self.__names)


class CcCrossIterator(CcIterator):
    """
    Iterator over name--name comparisons, filtering out those where the names are the same.
    """

    def __init__(self, names: Iterable[str], controls: Iterable[str], n_repeats: int):
        it = [
            cc
            for cc in list(TieredIterator([list(range(n_repeats)), controls, list(names)]))
            if cc[1] != cc[2]
        ]
        self.__it = iter(it)
        self.__n = len(it)
        self.__i = -1

    def __next__(self) -> ControlComparison:
        self.__i += 1
        repeat, control, name = next(self.__it)
        return ControlComparison(name, control, repeat)

    def position(self) -> int:
        """ """
        return self.__i

    def total(self) -> int:
        """ """
        return self.__n


class CcTreatmentSelectors:
    """
    Functions that choose (any number of) 'treatment' wells from a ``WellFrame``.
    """

    @classmethod
    def keep(cls, n: Optional[int] = None) -> Callable[[ControlComparison, WellFrame], WellFrame]:
        """


        Args:
            n:

        Returns:

        """

        def keepn(cc: ControlComparison, df: WellFrame) -> WellFrame:
            dfx = df.with_name(cc.name)
            if n is None:
                return dfx
            else:
                return dfx.subsample(min(n, len(dfx)))

        keepn.__name__ = "keep_" + ("all" if n is None else str(n))
        return keepn


class CcControlSelectors:
    """
    Functions that choose (any number of) 'control' wells from a ``WellFrame``, knowing which treatments were already chosen,

    The arguments for each are:
        1. ControlComparison
        2. WellFrame of all the wells
        3. WellFrame of the chosen treatment wells (from arg #2).

    Then returns:
        - A WellFrame of the controls (selected from arg #2)

      These may include all available control wells or a subset of them, but never any others.

    """

    @classmethod
    def keep(cls) -> Callable[[ControlComparison, WellFrame, WellFrame], WellFrame]:
        """ """
        # noinspection PyUnusedLocal
        def keep_all(cc: ControlComparison, df: WellFrame, by_name: WellFrame) -> WellFrame:
            return df.with_name(cc.control)

        return keep_all

    @classmethod
    def same(
        cls, columns: Union[str, Set[str]], or_null: bool
    ) -> Callable[[ControlComparison, WellFrame, WellFrame], WellFrame]:
        """


        Args:
            columns:
            or_null: bool:

        Returns:

        """
        if not Tools.is_true_iterable(columns):
            columns = [columns]

        def same(cc: ControlComparison, df: WellFrame, by_name: WellFrame) -> WellFrame:
            dfx = df.with_name(cc.control)
            for column in columns:
                if or_null:
                    dfx = dfx[(dfx[column].isna()) | (dfx[column].isin(by_name[column].unique()))]
                else:
                    dfx = dfx[dfx[column].isin(by_name[column].unique())]
            return dfx

        same.__name__ += "_" + "_".join(columns) + ("_or_null" if or_null else "")
        return same


class CcSubsamplers:
    """
    Functions that take two ``WellFrame``s: 1 for 'treatments' and 1 for 'controls',
    and return updated ``WellFrame``s with wells potentially subsampled from each.

    """

    @classmethod
    def keep(
        cls, n: Optional[int], balanced: bool = True
    ) -> Callable[[ControlComparison, WellFrame, WellFrame], Tup[WellFrame, WellFrame]]:
        """


        Args:
            n: Optional[int]:
            balanced:

        Returns:

        """
        # noinspection PyUnusedLocal
        def keepn(
            cc: ControlComparison, by_name: WellFrame, by_control: WellFrame
        ) -> Tup[WellFrame, WellFrame]:
            m_name = len(by_name) if n is None else min(n, len(by_name))
            # noinspection PyTypeChecker
            m_control = len(by_control) if n is None else min(int(n), len(by_control))
            if balanced:
                m = min(m_name, m_control)
                return by_name.subsample(m), by_control.subsample(m)
            else:
                return by_name.subsample(m_name), by_control.subsample(m_control)

        keepn.__name__ = (
            "keep_" + ("all" if n is None else str(n)) + ("_balanced" if balanced else "")
        )
        return keepn

    @classmethod
    def keep_rand(
        cls, rand: Callable[[int], int], balanced: bool = True
    ) -> Callable[[ControlComparison, WellFrame, WellFrame], Tup[WellFrame, WellFrame]]:
        """


        Args:
            rand:
            balanced:

        Returns:

        """
        # noinspection PyUnusedLocal
        def keeprand(
            cc: ControlComparison, by_name: WellFrame, by_control: WellFrame
        ) -> Tup[WellFrame, WellFrame]:
            if balanced:
                m = rand(min(len(by_name), len(by_control)))
                return by_name.subsample(m), by_control.subsample(m)
            else:
                m_name, m_control = rand(len(by_name)), rand(len(by_control))
                return by_name.subsample(m_name), by_control.subsample(m_control)

        keeprand.__name__ += "_" + ("_balanced" if balanced else "") + Tools.pretty_function(rand)
        return keeprand

    @classmethod
    def split_self(
        cls, n: Optional[int], balanced: bool = True, rand: Optional[Callable[[int], int]] = None
    ) -> Callable[[ControlComparison, WellFrame, WellFrame], Tup[WellFrame, WellFrame]]:
        """
        Returns a new function to pass into the ``TrainableCcIterator`` constructor:
            Splits self-comparisons (where the ``name`` is the same for the so-called 'treatments' and 'controls').
            Modifies the ``name`` column in the ``WellFrames`` (passed from the iterator) in-place to ``name+'__a'`` and ``name+'__b'``.
            Will raise a XValueError if the wells of the treatments and controls don't match,
            they both don't have a single name, or that name isn't the one in the ControlComparison.

        Args:
            n: Maximum number of wells to subsample for each (i.e. n treatment wells and n control wells).
               If None, choose all available (except when ``balanced``; see below)
            balanced: If there are an odd number of wells, choose floor(available/2) for both.
                      Otherwise, choose floor(available/2), floor(available/2)+1.
                      If ``n`` is lower than the number of wells available, chooses ``n`` for both.
            rand: If non-None, apply this function on the chosen number of wells for 'a' and 'b'.
                  This happens after everything else.
                  If ``balanced`` is set, raises an AssertionError if the new (returned) values aren't the same for 'a' and 'b'

        Returns:

        """

        def split_self(
            cc: ControlComparison, by_name: WellFrame, by_control: WellFrame
        ) -> Tup[WellFrame, WellFrame]:
            if not (
                by_name.unique_names() == by_control.unique_names() == [cc.name] == [cc.control]
            ):
                raise XValueError(
                    "Names must be the same; got {} {} {} {}".format(
                        by_name.unique_names(), by_control.unique_names(), [cc.name], [cc.control]
                    )
                )
            if by_name["well"].unique().tolist() != by_control["well"].unique().tolist():
                raise XValueError(
                    "{} != {}".format(
                        by_name["well"].unique().tolist(), by_control["well"].unique().tolist()
                    )
                )
            if n is None and (balanced or len(by_name) % 2 == 0):
                m_a = m_b = len(by_name) // 2
            elif n is None:
                # in this case, __b will always have more elements
                m_a, m_b = len(by_name) // 2, len(by_name) // 2 + 1
            else:
                m_a = m_b = n
            if rand is not None:
                if balanced:
                    assert m_a == m_b
                    m_a = m_b = rand(m_a)
                else:
                    m_a, m_b = rand(m_a), rand(m_b)
            a = by_name.subsample(m_a)
            b = by_name[~by_name["well"].isin(a["well"].unique())].subsample(m_b)
            a = a.with_new_names(cc.name + "__a")
            b = b.with_new_names(cc.name + "__b")
            return a, b

        split_self.__name__ += (
            "_"
            + ("all" if n is None else str(n))
            + ("_balanced" if balanced else "")
            + ("" if rand is None else "_" + Tools.pretty_function(rand))
        )
        return split_self


class CcShouldProceeds:
    """
    A collection of functions that decide whether to keep a ``ControlComparison`` after everything else is complete.
    """

    @classmethod
    def keep(
        cls, n_each: Optional[int] = None, req_two_labels: bool = True, fail: bool = True
    ) -> Callable[[ControlComparison, WellFrame, WellFrame], bool]:
        """


        Args:
            n_each:
            req_two_labels:
            fail:

        Returns:

        """
        if n_each is None:
            n_each = 0

        # noinspection PyUnusedLocal
        def if_at_least(cc: ControlComparison, by_name: WellFrame, by_control: WellFrame) -> bool:
            union = set(by_name.unique_names()).union(set(by_control.unique_names()))
            if req_two_labels and len(union) != 2:
                if fail:
                    raise ValueError(len(union))
                return False
            else:
                yes = len(by_name) >= n_each and len(by_control) >= n_each
                if fail and not yes:
                    raise ValueError((len(by_name), len(by_control)))
                return yes

        if_at_least.__name__ += (
            "_" + str(n_each) + ("_req2" if req_two_labels else "") + ("_fail" if fail else "")
        )
        return if_at_least


class TrainableCcIterator(SizedIterator):
    """"""

    def __init__(
        self,
        df: WellFrame,
        it: CcIterator,
        treatment_selector: Callable[
            [ControlComparison, WellFrame], WellFrame
        ] = CcTreatmentSelectors.keep(),
        control_selector: Callable[
            [ControlComparison, WellFrame, WellFrame], WellFrame
        ] = CcControlSelectors.keep(),
        subsampler: Callable[
            [ControlComparison, WellFrame, WellFrame], Tup[WellFrame, WellFrame]
        ] = CcControlSelectors.keep(),
        should_proceed: Callable[
            [ControlComparison, WellFrame, WellFrame], bool
        ] = CcShouldProceeds.keep(),
    ):
        """
        Constructor.

        Args:
            df: A WellFrame with treatments and controls to generate comparisons over
            it: An iterator over ControlComparisons for ``df``
            treatment_selector: A function that maps a ControlComparison and this ``df`` to a smaller WellFrame
                                containing just the desired treatments.
                                These should be all the wells with the ControlComparisons ``name``, or a subset of them
            control_selector: A function that maps a ControlComparison, this ``df``, and the treatments (from ``treatment_selector``)
                              to a smaller WellFrame of the desired control wells.
                              These should be all the control wells for the ControlComparison's ``control``, or a subset of them
            subsampler: A function that maps the ControlComparisons, result from ``treatment_selector``, and result from ``control_selector``,
                        to a new pair of (by_name, by_controls) corresponding to the inputs.
                        The intended purpose is subsampling intelligently after the treatment and control wells are chosen.
                        This function is permitted to be a bit flexible. It should avoid modifying inputs, but may.
            should_proceed: A function that decides whether to keep comparison, taking the ControlComparsion,
                            final subsampled input (by_name, by_controls), and returns True to keep it.
        """
        self.df = df
        self.__it = it
        self.__copyit = copy(it)
        self.treatment_selector = treatment_selector
        self.control_selector, self.subsampler, self.should_proceed = (
            control_selector,
            subsampler,
            should_proceed,
        )

    def __next__(self) -> TrainableCc:
        """

        Returns:

        """
        i = 0
        while self.__it.has_next():
            cc = next(self.__it)
            smalldf = self._select(cc)
            if smalldf is not None:
                logger.debug(f"{cc} has {len(smalldf)} rows")
                return TrainableCc(cc.name, cc.control, cc.repeat, smalldf)
            else:
                logger.debug(f"{cc} is empty")
            i += 1
            if i > self.total():
                raise StopIteration()  # TODO workaround
        raise StopIteration()  # TODO why is this needed?

    def _select(self, cc: ControlComparison) -> Optional[WellFrame]:
        by_name = self.treatment_selector(cc, self.df)
        if len(by_name) == 0:
            return
        by_control = self.control_selector(cc, self.df, by_name)
        if len(by_control) == 0:
            return
        by_name, by_control = self.subsampler(cc, by_name, by_control)
        if self.should_proceed(cc, by_name, by_control):
            z = WellFrame.concat(by_name, by_control)
            if len(z) == 0:
                return
            return z

    def position(self) -> int:
        """ """
        return self.__it.position()

    def total(self) -> int:
        """ """
        return self.__it.total()

    @property
    def controls(self):
        """ """
        return copy(self.__it.controls)

    @property
    def names(self):
        """ """
        return copy(self.__it.names)

    @property
    def n_repeats(self):
        """ """
        return self.__it.n_repeats


class CcIterators:
    """
    A collection of ``TrainableCcIterator`` implementations.
    """

    @classmethod
    def vs_control(
        cls,
        df: WellFrame,
        n_repeats: int = 1,
        restrict_to_same: Union[None, str, Set[str]] = None,
        restrict_include_null: bool = False,
        subsample_to: Optional[int] = None,
        controls: Optional[Iterable[str]] = None,
    ) -> TrainableCcIterator:
        """
        Creates an iterator over comparisons between ``name`` column values (in ``df``) and ``control_type`` values.
        It is recommended but not required that the control_type string for any control well is the same as its name.
        Consequently, ``df.unique_control_types()`` should be a subset of ``df.unique_names()``.

        This docstring has considerably more detail than the other functions in this class.
        If this is too much detail, refer to the others, which have similar arguments.

        Args:
            df: The WellFrame to iterate over.
            n_repeats: Repeat this number of times. Mostly useful when subsampling.
            restrict_to_same: Only include control wells that share one of the values in this column for the treatments.
            restrict_include_null:
            subsample_to:
            controls:

        This happens BEFORE subsampling (with ``subsample_to``, if set).

        For example, setting ``restrict_to_same='run'`` will cause:
        1. Treatment wells are chosen. They're over a set of runs X.
        2. Control wells are chosen, subject to being on a run in X.
        3. If ``subsample_to`` is set, both are subsampled randomly.
        If you need to ensure that the cases and controls in each classifier always share
        the same values AFTER subsampling, you'll need to use another function.
          restrict_include_null: If True, also permits any wells for which the column is None.
        This is designed with the column 'well_group' in mind,
        where you may want to compare against control wells that are appropriate for all well_groups.
          subsample_to: Subsample BOTH the cases and the controls to some number of replicates, OR THE MINIMUM for either
        This means each classifier will get an even number of replicates for the cases and controls.
        It also means a classifier might use fewer replicates, if not enough exist.


        Returns:
          A ``TrainableCcIterator``

        """
        if controls is None:
            controls = df.unique_controls_matching()
        it = CcCrossIterator(df.unique_names(), controls, n_repeats)
        if restrict_to_same is None:
            csel = CcControlSelectors.keep()
        else:
            csel = CcControlSelectors.same(restrict_to_same, restrict_include_null)
        sampler = CcSubsamplers.keep(subsample_to)
        return TrainableCcIterator(df, it, control_selector=csel, subsampler=sampler)

    @classmethod
    def vs_control_rand(
        cls,
        df: WellFrame,
        n_repeats: int = 1,
        restrict_to_same: Union[None, str, Set[str]] = None,
        restrict_include_null: bool = False,
        low: Optional[int] = None,
        high: Optional[int] = None,
        seed: int = 0,
        controls: Optional[Iterable[str]] = None,
    ) -> TrainableCcIterator:
        """


        Args:
            df: WellFrame:
            n_repeats:
            restrict_to_same:
            restrict_include_null:
            low:
            high:
            seed:
            controls:

        Returns:

        """
        if controls is None:
            controls = df.unique_controls_matching()
        it = CcCrossIterator(df.unique_names(), controls, n_repeats)
        if restrict_to_same is None:
            csel = CcControlSelectors.keep()
        else:
            csel = CcControlSelectors.same(restrict_to_same, restrict_include_null)
        rand = cls._rand(low, high, seed)
        if low is None or high is None or low == high:
            logger.warning(f"vs_control_rand has has fixed value for low={low}, high={high}")
        sampler = CcSubsamplers.keep_rand(rand, balanced=True)
        return TrainableCcIterator(df, it, control_selector=csel, subsampler=sampler)

    @classmethod
    def vs_self(
        cls, df: WellFrame, n_repeats: int = 1, subsample_to: Optional[int] = None
    ) -> TrainableCcIterator:
        """
        Iterates over comparisons of name--name.
        Subsampling then separates into "treatment" and "control" groups, relabling each mini-``WellFrame``.
        That is: each ``TrainableCc.smalldf.unique_names() == [original_name+'__a', original_name+'__b']``.
        The split can never result in overlap between wells in the 'a' and 'b' groups.
        ``subsample_to`` is the preferred number of wells per group. Setting it to None is equivalent to setting it to +infinity,
        meaning use the maximum available.
        The split will always use up to ``subsample_to`` wells in 'a' and 'b', subject to those available,
        but will further keep the proportions balanced.
        For example, if you set ``subsample_to=2``, but a comparison only has 3 total wells available,
        the split will result in 1 well for 'a' and 1 well for 'b', because the alternative would be unbalanced.
        So: Each group will have ``floor(min(n_available, subsample_to) / 2)`` wells

        Args:
            df: param n_repeats:
            subsample_to: The "preferred" number of wells per group

        Returns:
            A TrainableCcIterator

        """
        it = CcSelfIterator(df.unique_names(), n_repeats)
        sampler = CcSubsamplers.split_self(subsample_to)
        return TrainableCcIterator(
            df, it, control_selector=CcControlSelectors.keep(), subsampler=sampler
        )

    @classmethod
    def vs_self_random(
        cls,
        df: WellFrame,
        n_repeats: int = 1,
        low: Optional[int] = None,
        high: Optional[int] = None,
        seed: int = 0,
    ) -> TrainableCcIterator:
        """
        Similar to ``vs_self``, but each comparison ``k`` random wells,
        where ``k`` is drawn uniformly between ``min(low, floor(n_available/2))`` and ``min(high, floor(n_available/2)``.
        If there are always enough wells available, this is just between ``low`` and ``high``.

        Args:
            df: WellFrame:
            n_repeats:
            low:
            high:
            seed:

        Returns:

        """
        it = CcSelfIterator(df.unique_names(), n_repeats)
        rand = cls._rand(low, high, seed)
        sampler = CcSubsamplers.split_self(high, rand=rand)
        return TrainableCcIterator(
            df, it, control_selector=CcControlSelectors.keep(), subsampler=sampler
        )

    @classmethod
    def vs_other(
        cls,
        df: WellFrame,
        n_repeats: int = 1,
        restrict_to_same: Union[None, str, Set[str]] = None,
        restrict_include_null: bool = False,
        subsample_to: Optional[int] = None,
    ) -> TrainableCcIterator:
        """
        Comparisons between ``df.unique_names()`` and ``df.unique_names`` where the names are different.
        Note that this means exactly 2 comparisons per unordered (name, name) pair!
        If you don't want that... tough luck. Or write your own function :)
        See ``vs_controls`` for information about the arguments.

        Args:
            df: WellFrame:
            n_repeats:
            restrict_to_same:
            restrict_include_null:
            subsample_to:

        Returns:

        """
        it = CcCrossIterator(df.unique_names(), df.unique_names(), n_repeats)
        if restrict_to_same is None:
            csel = CcControlSelectors.keep()
        else:
            csel = CcControlSelectors.same(restrict_to_same, restrict_include_null)
        sampler = CcSubsamplers.keep(subsample_to)
        return TrainableCcIterator(df, it, control_selector=csel, subsampler=sampler)

    @classmethod
    def _rand(cls, low: Optional[int], high: Optional[int], seed: int):
        if (low is None) != (high is None) or low is not None and low > high:
            raise ContradictoryRequestError("low is {low} but high is {high}")
        elif low is None:
            return None
        else:
            rs = np.random.RandomState(seed)

            def rand(available):
                return rs.randint(low=min(available, low), high=min(available, high) + 1)

            rand.__name__ = f"rand_avail({low}–{high},seed={seed})"
            return rand


__all__ = [
    "ControlComparison",
    "CcIterator",
    "TrainableCc",
    "TrainableCcIterator",
    "CcTreatmentSelectors",
    "CcControlSelectors",
    "CcSubsamplers",
    "CcShouldProceeds",
    "CcIterators",
]

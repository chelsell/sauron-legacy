from __future__ import annotations

from pocketutils.tools.loop_tools import LoopTools

from sauronlab.core.core_imports import *
from sauronlab.ml import ClassifierPath
from sauronlab.ml.classifiers import *
from sauronlab.ml.decision_frames import *
from sauronlab.ml.spindles import SpindleFrame
from sauronlab.model.case_control_comparisons import *
from sauronlab.model.well_frames import *


class MultiTrainerUtils:
    """"""

    @classmethod
    def to_spindle(cls, items: Iterable[Tup[DecisionFrame, TrainableCc]]) -> SpindleFrame:
        """


        Args:
            items:

        Returns:

        """
        accs = []
        for dec, cc in items:
            acc = dec.accuracy().reset_index()
            acc["source"] = cc.name  # as in arrows
            acc["target"] = cc.control
            acc["repeat"] = cc.repeat
            accs.append(acc)
        return SpindleFrame(pd.concat(accs, sort=False))

    def __repr__(self):
        return self.__class__.__name__

    def __str__(self):
        return self.__class__.__name__


@abcd.auto_repr_str()
@abcd.auto_html()
class MultiTrainer:
    """
    A model to train case-vs-control classifiers for all cases and all controls (using a ``TrainableCcIterator``).
    Knows the model used to train, the dir to save to, and an iterator over ``TrainableCc``s.

    """

    def __init__(
        self,
        save_dir: PathLike,
        model_type: SklearnWfClassifierWithOob,
        iterator_fn: Callable[[], TrainableCcIterator],
        always_log: bool = False,
    ):
        """

        Args:
            save_dir: The directory under which to save
            model_type: A WellClassifier supporting an out-of-bag; its ``build`` function will be called without parameters
            iterator_fn: The iterator over case-control comparisons
            always_log: If False, suppresses classifier output after the first one
        """
        self.always_log = always_log
        self.save_dir, self.model_type, self.iterator_fn = Path(save_dir), model_type, iterator_fn
        self.__length = self.iterator_fn().total()

    def simulate(self, df: WellFrame, max_iters: Optional[int] = None) -> None:
        """
        Iterates through comparisons as though they were to be trained (including those that were already trained).
        Prints info about each comparison to stdout.

        Args:
            df: WellFrame:
            max_iters: Optional[int]:  (Default value = None)

        """
        for i, (tt, subdir, n_trained) in enumerate(self._iterate(df)):
            info = {"trained": subdir.exists_with_decision(), **tt.info()}
            lines = []
            for k, v in info.items():
                if isinstance(v, Mapping):
                    lines.append(k + " = {" + Tools.join_kv(v, sep=",") + "}")
                elif Tools.is_true_iterable(v):
                    lines.append(k + " = [" + ",".join([str(q) for q in v]) + "]")
                else:
                    lines.append(k + " = " + str(v))
            print(
                "\n"
                + (tt.name + " – " + tt.control).center(100, Chars.bar)
                + "\n"
                + "\n".join(lines)
            )
            if max_iters is not None and i > max_iters:
                logger.info(f"Exiting after {i} iters")
                break

    def iterate(self, df: WellFrame) -> Generator[TrainableCc, None, None]:
        """
        Just iterates over ``TrainableCc``s to be trained (even if they were already trained).

        Args:
            df: WellFrame:

        Yields:

        """
        for tt, subdir, n_trained in self._iterate(df):
            yield tt

    def just_train(self, df: WellFrame, store_for_spindle: bool = False) -> None:
        """
        Train the whole model.

        Args:
            df: Must correspond to the iterator; this can't be verified
            store_for_spindle: Store results as they're trained. This will consume increasing memory with
                               successive models, but will save time at the end.

        """
        for _ in self.train(df, store_for_spindle=store_for_spindle):
            pass
        self.load_spindle()  # save it

    def train(
        self, df: WellFrame, store_for_spindle: bool = False
    ) -> Generator[Tup[DecisionFrame, TrainableCc], None, None]:
        """
        Train the models, yielding one at a time after they're trained.

        Args:
            df: Must correspond to the iterator; this can't be verified
            store_for_spindle: Store results as they're trained. This will consume increasing memory with successive
                               models, but will save a spindle at the end.

        Yields:

        """
        decisions = []
        for tt, subdir, n_trained in self._iterate(df):
            if subdir.exists_with_decision():
                logger.debug(f"{subdir} already trained")
                decision = DecisionFrame.read_csv(subdir.decision_csv)
            else:
                logger.debug(f"Training {subdir}")
                silence = n_trained > 0 and not self.always_log
                with Tools.silenced(no_stderr=silence, no_stdout=silence):
                    with logger.suppressed(silence):
                        decision = self._train_one(tt, subdir)
                if n_trained == 1:
                    logger.notice("Ignoring future classifier output...\n")
            if store_for_spindle:
                decisions.append((decision, tt))
            yield decision, tt
        if store_for_spindle:
            MultiTrainerUtils.to_spindle(decisions).to_csv(self.spindle_path)
            logger.info("Saved spindle.")

    def _iterate(
        self, df: WellFrame
    ) -> Generator[Tup[TrainableCc, ClassifierPath, int], None, None]:
        """


        Args:
            df: WellFrame:

        Yields:

        """
        it = self.iterator_fn()
        self._startup_messages(it, df)
        n_trained = -1
        current_repeat = None
        for i, tt in enumerate(Tools.loop(it, log=logger.info, every_i=200)):
            if current_repeat is not None and tt.repeat != current_repeat:
                logger.debug(f"Finished with repeat {current_repeat}")
            current_repeat = tt.repeat
            subdir = ClassifierPath(self.save_dir / tt.directory)
            if not subdir.exists_with_decision():
                n_trained += 1
            yield tt, subdir, n_trained
        logger.info("Finished training!")

    def _train_one(self, tt: TrainableCc, subdir: ClassifierPath) -> Tup[DecisionFrame, int]:
        """


        Args:
            tt: TrainableCc:
            subdir: ClassifierPath:

        Returns:

        """
        model = self.model_type.build()
        model.train(tt.smalldf)
        model.save(subdir.model_pkl)
        decision = model.training_decision
        decision.to_csv(subdir.decision_csv)
        return decision

    def read_spindle(self) -> SpindleFrame:
        """
        Reads the ``spindle.csv``. Fast.

        Returns:

        """
        sf = SpindleFrame.read_csv(self.spindle_path)
        if "index" in sf.columns:
            sf = sf.drop("index", axis=1)
        return SpindleFrame(sf)

    def load_spindle(self) -> SpindleFrame:
        """Reads the ``spindle.csv`` if it exists (fast). Otherwise loads from decisions (slow)."""
        if self.spindle_path.exists():
            return self.read_spindle()
        else:
            spindle = MultiTrainerUtils.to_spindle(self.load_decisions())
            spindle.to_csv(self.spindle_path)
            return spindle

    def load_decisions(self) -> Generator[Tup[DecisionFrame, TrainableCc], None, None]:
        """
        Reads in ``DecisionFrame``s. Slow.

        Yields:

        """
        logger.trace(f"Loading decisions at {self.save_dir}")
        for path, cc in LoopTools.loop(
            self.load_paths(), n_total=len(self), log=logger.trace, every_i=1000
        ):
            decision = DecisionFrame.read_csv(path.decision_csv)
            yield decision, cc

    def load_paths(self) -> Generator[Tup[ClassifierPath, TrainableCc], None, None]:
        """
        Returns the paths and corresponding control comparisons. Slow.

        Yields:

        Raises:
            PathDoesNotExistError: If any model wasn't fully trained, including an associated decision.csv

        """
        for path, cc in self.paths():
            path.verify_exists_with_decision()
            yield path, cc

    def paths(self) -> Generator[Tup[ClassifierPath, TrainableCc], None, None]:
        """
        Returns the paths and corresponding control comparisons. Slow.
        The paths MAY OR MAY NOT BE TRAINED.

        Yields:

        """
        for cc in iter(self.iterator_fn()):
            path = ClassifierPath(self.save_dir / cc.directory)
            yield path, cc

    def _startup_messages(self, it: TrainableCcIterator, df) -> None:
        """


        Args:
            it: TrainableCcIterator:
            df:

        """
        logger.debug(f"Iterator has length {len(it)}")
        fn_strs = [
            Tools.pretty_function(it.treatment_selector),
            Tools.pretty_function(it.control_selector),
            Tools.pretty_function(it.subsampler),
            Tools.pretty_function(it.should_proceed),
        ]
        logger.notice(
            "Using: treatment selector {}, control selector {}, subsampler {}, and should_proceed {}".format(
                *fn_strs
            )
        )
        logger.info("Logging every 50 iterations.")

    @property
    def info_path(self) -> Path:
        """"""
        return self.save_dir / "info.properties"

    @property
    def spindle_path(self) -> Path:
        """"""
        return self.save_dir / "spindle.csv"

    def __len__(self):
        """"""
        return self.__length


class MultiTrainers:
    """"""

    @classmethod
    def vs_control(
        cls,
        df: WellFrame,
        save_dir: PathLike,
        model_type: SklearnWfClassifierWithOob,
        n_repeats: int = 1,
        restrict_to_same: Union[None, str, Set[str]] = None,
        restrict_include_null: bool = False,
        subsample_to: Optional[int] = None,
        controls: Optional[Iterable[str]] = None,
    ) -> MultiTrainer:
        """


        Args:
            df: WellFrame:
            save_dir: PathLike:
            model_type: SklearnWfClassifierWithOob:
            n_repeats: int:  (Default value = 1)
            restrict_to_same:
            restrict_include_null: bool:  (Default value = False)
            subsample_to: Optional[int]:  (Default value = None)
            controls:

        Returns:

        """

        def it_gen():
            """ """
            return CcIterators.vs_control(
                df,
                n_repeats=n_repeats,
                restrict_to_same=restrict_to_same,
                restrict_include_null=restrict_include_null,
                subsample_to=subsample_to,
                controls=controls,
            )

        return MultiTrainer(save_dir, model_type, it_gen)

    @classmethod
    def vs_control_rand(
        cls,
        df: WellFrame,
        save_dir: PathLike,
        model_type: SklearnWfClassifierWithOob,
        n_repeats: int = 1,
        restrict_to_same: Union[None, str, Set[str]] = None,
        restrict_include_null: bool = False,
        low: Optional[int] = None,
        high: Optional[int] = None,
        seed: int = 0,
        controls: Optional[Iterable[str]] = None,
    ) -> MultiTrainer:
        """


        Args:
            df: WellFrame:
            save_dir: PathLike:
            model_type: SklearnWfClassifierWithOob:
            n_repeats: int:  (Default value = 1)
            restrict_to_same:
            restrict_include_null: bool:  (Default value = False)
            low:
            high:
            seed:
            controls:

        Returns:

        """

        def it_gen():
            """ """
            return CcIterators.vs_control_rand(
                df,
                n_repeats=n_repeats,
                restrict_to_same=restrict_to_same,
                restrict_include_null=restrict_include_null,
                low=low,
                high=high,
                seed=seed,
                controls=controls,
            )

        return MultiTrainer(save_dir, model_type, it_gen)

    @classmethod
    def vs_self(
        cls,
        df: WellFrame,
        save_dir: PathLike,
        model_type: SklearnWfClassifierWithOob,
        n_repeats: int = 1,
        subsample_to: Optional[int] = None,
    ) -> MultiTrainer:
        """


        Args:
            df: WellFrame:
            save_dir: PathLike:
            model_type: SklearnWfClassifierWithOob:
            n_repeats: int:  (Default value = 1)
            subsample_to: Optional[int]:  (Default value = None)

        Returns:

        """

        def it_gen():
            """ """
            return CcIterators.vs_self(df, n_repeats=n_repeats, subsample_to=subsample_to)

        return MultiTrainer(save_dir, model_type, it_gen)

    @classmethod
    def vs_self_random(
        cls,
        df: WellFrame,
        save_dir: PathLike,
        model_type: SklearnWfClassifierWithOob,
        n_repeats: int = 1,
        low: Optional[int] = None,
        high: Optional[int] = None,
        seed: int = 0,
    ) -> MultiTrainer:
        """


        Args:
            df: WellFrame:
            save_dir: PathLike:
            model_type: SklearnWfClassifierWithOob:
            n_repeats: int:  (Default value = 1)
            low:
            high:
            seed:

        Returns:

        """

        def it_gen():
            """ """
            return CcIterators.vs_self_random(
                df, n_repeats=n_repeats, low=low, high=high, seed=seed
            )

        return MultiTrainer(save_dir, model_type, it_gen)

    @classmethod
    def vs_other(
        cls,
        df: WellFrame,
        save_dir: PathLike,
        model_type: SklearnWfClassifierWithOob,
        n_repeats: int = 1,
        restrict_to_same: Union[None, str, Set[str]] = None,
        restrict_include_null: bool = False,
        subsample_to: Optional[int] = None,
    ) -> MultiTrainer:
        """


        Args:
            df: WellFrame:
            save_dir: PathLike:
            model_type: SklearnWfClassifierWithOob:
            n_repeats: int:  (Default value = 1)
            restrict_to_same:
            restrict_include_null: bool:  (Default value = False)
            subsample_to: Optional[int]:  (Default value = None)

        Returns:

        """

        def it_gen():
            """ """
            return CcIterators.vs_other(
                df,
                n_repeats=n_repeats,
                restrict_to_same=restrict_to_same,
                restrict_include_null=restrict_include_null,
                subsample_to=subsample_to,
            )

        return MultiTrainer(save_dir, model_type, it_gen)

    def __repr__(self):
        return self.__class__.__name__

    def __str__(self):
        return self.__class__.__name__


__all__ = ["MultiTrainer", "MultiTrainers"]

"""
A better and simpler implementation of well classifiers introduced in sauronlab 1.13.0.
"""

import joblib
from sklearn.ensemble import RandomForestClassifier

from sauronlab.core.core_imports import *
from sauronlab.ml import ClassifierPath, SaveableTrainable
from sauronlab.ml.decision_frames import *
from sauronlab.model.wf_builders import *
from sauronlab.viz.figures import *


class ClassifierFailedError(AlgorithmError):
    """ """


class ClassifierTrainFailedError(ClassifierFailedError):
    """ """


class ClassifierPredictFailedError(ClassifierFailedError):
    """ """


class TrainTestOverlapWarning(StrangeRequestWarning):
    """
    Training and test data overlap.
    """


class NotTrainedError(OpStateError):
    """ """


class AlreadyTrainedError(OpStateError):
    """ """


# just for good tab completion
AnySklearnClassifier = RandomForestClassifier


class WellClassifier(SaveableTrainable):
    """
    Has things.

    The important methods are:
        - train(df)
        - test(df)
        - load(path)
        - save(path)

    Some classifiers may also implement:
        - training_decision
        - oob_score
        - weights

    Only three methods need to be implemented: train, test, and the property params.
    When trained, ``info`` contains:
        - wells, labels, features
        - started, finished, seconds_taken

    The saved .info file contains the above, plus the contents of ``params`` and any statistics.
    """

    @abcd.abstractmethod
    def train(self, df: WellFrame) -> None:
        raise NotImplementedError()

    @abcd.abstractmethod
    def test(self, df: WellFrame) -> DecisionFrame:
        raise NotImplementedError()

    @property
    @abcd.abstractmethod
    def params(self) -> Mapping[str, Any]:
        raise NotImplementedError()

    @property
    def is_trained(self) -> bool:
        return "finished" in self.info

    def _update_wf_info(self, df: WellFrame) -> None:
        self.info.update(
            {
                "wells": df["well"].values,
                "runs": df["run"].values,
                "labels": df["name"].values,
                "features": df.columns.values.astype(np.int32),
            }
        )

    def _verify_trained(self) -> None:
        if not self.is_trained:
            raise NotTrainedError("Model is not trained")

    def _verify_untrained(self) -> None:
        if self.is_trained:
            raise AlreadyTrainedError("Model is already trained")

    def _verify_train(self, wells: np.array, names: Sequence[str], features) -> None:
        self._verify_untrained()
        if len(wells) == 0:
            raise EmptyCollectionError("Cannot train on an empty WellFrame")
        if len(set(names)) == 1:
            logger.warning(f"Training a classifier for only 1 label: {names[0]}")

    def _verify_test(self, wells: np.array, names: Sequence[str], features) -> None:
        self._verify_trained()
        overlap = set(names).difference(set(self.info["labels"]))
        if len(overlap) > 0:
            raise LengthMismatchError(
                f"Test labels {set(names)} are not in the train labels {set(self.info['labels'])}"
            )
        intersec = set(self.info["labels"]).intersection(set(wells.values))
        if len(intersec) > 0:
            logger.warning("Test wells {} overlap with training wells")
        if features != self.info["features"]:
            logger.warning("Features don't match")

    def __repr__(self):
        return f"{self.__class__.__name__}({'trained' if self.is_trained else 'not trained'})"

    def __str__(self):
        return repr(self)


class HasOob(WellClassifier, metaclass=abc.ABCMeta):
    @property
    @abcd.abstractmethod
    def oob_score(self) -> float:
        raise NotImplementedError()

    @property
    @abcd.abstractmethod
    def training_decision(self) -> DecisionFrame:
        raise NotImplementedError()


class HasWeights(WellClassifier, metaclass=abc.ABCMeta):
    @property
    @abcd.abstractmethod
    def weights(self) -> Sequence[float]:
        """ """
        raise NotImplementedError()


class BuildableWellClassifier(abcd.ABC):
    """
    A WellClassifier with a classmethod ``build`` that returns a new instance from kwargs.
    This method is separated from the constructor, which might provide a different, more direct interface.
    The idea here is that ``build`` may be willing to assume default parameters.
    """

    @classmethod
    @abcd.abstractmethod
    def build(cls, **kwargs):
        """
        Returns a new classifier from parameters.
        """
        raise NotImplementedError()

    @classmethod
    def load_(cls, path: PathLike):
        x = cls.build()
        x.load(path)
        return x


class SklearnWellClassifier(WellClassifier, BuildableWellClassifier, metaclass=abc.ABCMeta):
    """
    A well classifier backed by a single scikit-learn classifier.
    Note that the constructor is typed as requiring a ``ForestClassifier``, but this is only for better tab completion.
    It can accept any scikit-learn classifier.
    """

    def __init__(self, model: AnySklearnClassifier):
        super().__init__()
        self.model = model
        self._trained_decision = None

    @classmethod
    def model_class(cls) -> Type:
        raise NotImplementedError()

    @property
    def params(self) -> Mapping[str, Any]:
        return self.model.get_params()

    @params.setter
    def params(self, **params):
        self._verify_untrained()
        self.model.set_params(**params)

    @abcd.override_recommended
    def statistics(self) -> Mapping[str, Any]:
        return {}

    def load(self, path: PathLike) -> None:
        self._verify_untrained()
        path = Path(path)
        if path.suffix == ".pkl":
            path = path.parent
        path = ClassifierPath(path)
        path.exists()
        try:
            try:
                self.info = path.load_info()
            except Exception:
                raise LoadError(f"Failed to load model metadata at {path.info_json}")
            try:
                self.model = joblib.load(str(path.model_pkl))
            except Exception:
                raise LoadError(f"Failed to load model at {path.model_pkl}")
            if self.info["params"] != self.params:
                logger.error(
                    f"Loaded model params don't match: {self.info['params']} in info and {self.params} in classifier"
                )
            self.info["params"] = self.params
        except:  # don't allow a partial state
            self.info = None
            self.model = None
            raise
        logger.debug(f"Loaded model at {path.model_pkl}")

    def save(self, path: PathLike) -> None:
        self._verify_trained()
        path = Path(path)
        if str(path).endswith("model.pkl"):
            path = path.parent
        path = ClassifierPath(path)
        logger.debug(f"Saving model to {path.model_pkl} ...")
        info = copy(self.info)
        info["params"] = self.params
        info["stats"] = self.statistics()
        try:
            path.prep()
            path.save_info(info)
        except Exception:
            raise LoadError(f"Failed to save model metadata to {path.info_json}")
        try:
            joblib.dump(self.model, str(path.model_pkl), protocol=5)
        except Exception:
            raise LoadError(f"Failed to save model to {path.model_pkl}")
        logger.debug(f"Saved model to {path.model_pkl}")

    def train(self, df: WellFrame) -> None:
        self._verify_train(df["well"].values, df["name"].values, df.columns.values)
        logger.info(self._startup_string(df))
        reps = df.n_replicates()
        logger.trace(
            "Training with replicates: " + ", ".join([k + "=" + str(v) for k, v in reps.items()])
        )
        with_lt_2 = {k: v for k, v in reps.items() if v < 2}
        if len(with_lt_2) > 20:
            logger.warning(f"{len(with_lt_2)} labels have only 1 replicate.")
        elif len(with_lt_2) > 0:
            logger.warning(
                f"{len(with_lt_2)} labels have only 1 replicate: {','.join(with_lt_2.keys())}."
            )
        if len(df.unique_names()) > 100:
            logger.caution("Training a classifier on >100 labels.")
        if len(set(reps.values())) > 1:
            logger.caution("Training on an imbalanced set.")
        # fit
        t0, d0 = time.monotonic(), datetime.now()
        try:
            self.model.fit(*df.xy())
        except Exception:
            raise ClassifierTrainFailedError(
                f"Failed to train (names {df.unique_names()} and runs {df.unique_runs()})"
            )
        t1, d1 = time.monotonic(), datetime.now()
        # update info
        self._update_wf_info(df)
        self.info["started"], self.info["finished"], self.info["seconds_taken"] = d0, d1, t1 - t0
        # show stats, but don't overwhelm
        # note that calling statistics() here can add some time (ex oob_score)
        # this "inflates" the training time, which is arguably more useful
        stats = [
            str(k) + "=" + ("%.3g" % v if isinstance(v, (int, float)) else str(v))
            for k, v in self.statistics().items()
        ]
        logger.info(
            "Finished training. Took {}s. {}".format(
                round(t1 - t0), ", ".join(stats) if len(stats) < 4 else ""
            )
        )
        if 4 <= len(stats) <= 50:
            logger.trace(f"Statistics: {', '.join(stats)}")

    def test(self, df: WellFrame) -> DecisionFrame:
        logger.trace(f"Testing on names {df.unique_names()} and runs {df.unique_runs()} ...")
        self._verify_test(df["well"].values, df["name"].values, df.columns.values)
        X, y = df.xy()
        labels = self.model.classes_
        try:
            predictions = self.model.predict_proba(X)
        except Exception:
            raise ClassifierPredictFailedError(
                f"Failed to test (names {df.unique_names()} and runs {df.unique_runs()})"
            )
        return DecisionFrame.of(y, labels, predictions, df["well"].values)

    def _startup_string(self, df) -> str:
        return "Training on {} labels and {} features using {} examples, {} runs, and {} estimators on {} core(s).".format(
            len(df.unique_names()),
            df.feature_length(),
            len(df),
            len(df["run"].unique()),
            self.model.n_estimators,
            1 if self.model.n_jobs is None else self.model.n_jobs,
        )


class SklearnWfClassifierWithOob(
    SklearnWellClassifier, HasOob, BuildableWellClassifier, metaclass=abc.ABCMeta
):
    def __init__(self, model: AnySklearnClassifier):
        model.oob_score = True  # ignore user preference so that oob_score() is defined
        super().__init__(model)
        self._trained_decision = None

    def statistics(self) -> Mapping[str, Any]:

        return {**super().statistics(), **{"oob_score": self.oob_score}}

    def save_to_dir(
        self,
        path: PathLike,
        exist_ok: bool = True,
        figures: bool = False,
        sort: bool = True,
        runs: Optional[Sequence[int]] = None,
        label_colors: Optional[Mapping[str, str]] = None,
    ):
        from sauronlab.viz.figures import FigureSaver

        path = Tools.prepped_dir(
            path.path if isinstance(path, ClassifierPath) else path, exist_ok=exist_ok
        )
        path = ClassifierPath(path)
        logger.debug(f"Saving to {path}")
        self._verify_trained()
        self.save(path.model_pkl)
        decision = self.training_decision
        decision.to_csv(path.decision_csv)
        confusion = decision.confusion()
        if sort:
            with logger.suppressed_other("clana", below="WARNING"):
                confusion = confusion.sort(deterministic=True)
        confusion.to_csv(path.confusion_csv, index_label="name")
        accuracy = decision.accuracy()
        accuracy.to_csv(path.accuracy_csv)
        if isinstance(self, HasWeights):
            weights = self.weights
            series = pd.Series(weights, name="weight")
            series.to_csv(str(path.weight_csv))
        if figures:
            with FigureTools.clearing():
                FigureSaver().save(accuracy.swarm(), path.swarm_pdf)
                FigureSaver().save(
                    confusion.heatmap(runs=runs, label_colors=label_colors), path.confusion_pdf
                )

    @property
    def oob_score(self) -> float:
        self._verify_trained()
        logger.debug("Calculating out-of-bag score...")
        return self.model.oob_score_

    @property
    def training_decision(self) -> DecisionFrame:
        logger.debug("Calculating training decision function...")
        self._verify_trained()
        if self._trained_decision is None:
            correct_labels = self.info["labels"]
            labels = self.model.classes_
            self._trained_decision = DecisionFrame.of(
                correct_labels, labels, self.model.oob_decision_function_, self.info["wells"]
            )
        return self._trained_decision


class SklearnWfClassifierWithWeights(SklearnWellClassifier, HasWeights, metaclass=abc.ABCMeta):
    def __init__(self, model: AnySklearnClassifier):
        super().__init__(model)
        self._weights = None

    @property
    def weights(self) -> Sequence[float]:
        logger.debug("Calculating weights...")
        if self._weights is None:
            self._weights = self.model.feature_importances_
        return self._weights


class Ut:
    """
    Tiny utilities.
    """

    @classmethod
    def depths(cls, model) -> Sequence[int]:
        return [t.tree_.max_depth for t in model.model.estimators_]


class WellForestClassifier(SklearnWfClassifierWithOob, SklearnWfClassifierWithWeights):

    cached_name = "WellForestClassifier"

    @classmethod
    def build(cls, **kwargs):
        kwargs = copy(kwargs)
        if "n_estimators" not in kwargs:
            kwargs["n_estimators"] = 1000
        return WellForestClassifier(RandomForestClassifier(**kwargs))

    @classmethod
    def model_class(cls) -> Type[AnySklearnClassifier]:
        return RandomForestClassifier

    def depths(self) -> Sequence[int]:
        return Ut.depths(self)


class WellClassifiers:

    _classifier_cache = {RandomForestClassifier.__qualname__: WellForestClassifier}

    @classmethod
    def forest(cls, **kwargs) -> WellForestClassifier:
        return WellForestClassifier.build(**kwargs)

    @classmethod
    def new_class(
        cls, model: Type[AnySklearnClassifier], **default_kwargs
    ) -> Type[SklearnWellClassifier]:
        qname = (
            model.__qualname__
            + (":" + ",".join([str(k) + "=" + str(v) for k, v in default_kwargs.items()]))
            if len(default_kwargs) > 0
            else ""
        )
        if qname in WellClassifiers._classifier_cache:
            logger.debug(f"Loading existing type {qname}")
            return WellClassifiers._classifier_cache[qname]
        supers = WellClassifiers._choose_classes(model)

        class X(*supers):
            @classmethod
            def model_class(cls) -> Type[AnySklearnClassifier]:
                return model

            @classmethod
            def build(cls, **kwargs):
                args = copy(default_kwargs)
                args.update(kwargs)
                return X(model(**args))

        X.cached_name = qname
        X.__name__ = "Well" + str(model.__name__)
        if isinstance(model, AnySklearnClassifier):
            X.depths = Ut.depths
        WellClassifiers._classifier_cache[qname] = X
        logger.trace(f"Registered new type {qname}")
        return X

    @classmethod
    def _choose_classes(cls, model):
        has_oob = hasattr(model, "oob_score_") and hasattr(model, "oob_decision_function_")
        has_weights = hasattr(model, "feature_importances_")
        supers = []
        if has_oob:
            supers.append(SklearnWfClassifierWithOob)
        if has_weights:
            supers.append(SklearnWfClassifierWithOob)
        if len(supers) == 0:
            supers = [SklearnWellClassifier]
        return supers


__all__ = [
    "WellClassifier",
    "SklearnWfClassifierWithOob",
    "SklearnWfClassifierWithWeights",
    "WellForestClassifier",
    "WellClassifiers",
]

"""
Code for machine learning, most noteably including classifiers of wells.
Can depend on core, model, viz, and calc.
"""
from __future__ import annotations

from pocketutils.tools.filesys_tools import FilesysTools
from pocketutils.tools.path_tools import PathTools

from sauronlab.core.core_imports import *


class ErrorBehavior(CleverEnum):

    FAIL = 1
    LOG_ERROR = 2
    LOG_WARNING = 3
    LOG_CAUTION = 4
    IGNORE = 5


class AbstractSaveLoad(metaclass=abc.ABCMeta):
    """ """

    def save(self, path: PathLike) -> None:
        raise NotImplementedError()

    # noinspection PyAttributeOutsideInit
    def load(self, path: PathLike):
        raise NotImplementedError()


class SaveableTrainable(AbstractSaveLoad):
    """
    A simpler saveable.
    Saves and loads a .info file with these properties.
    To implement, just override save() and load(), and have each call its supermethod

    """

    def __init__(self):
        self.info = {}

    def save(self, path: PathLike) -> None:
        FilesysTools.save_json(self.info, path.with_suffix(path.suffix + ".info"))

    def load(self, path: PathLike):
        path = Path(path)
        self.info = FilesysTools.load_json(path.with_suffix(path.suffix + ".info"))

        def fix(key, value):
            if key in ["started", "finished"]:
                return datetime.isoformat(value)
            elif isinstance(value, list):
                return np.array(value)
            else:
                return value

        self.info = {k: fix(k, v) for k, v in self.info.items()}
        return self


class SaveableTrainableCsv(SaveableTrainable, metaclass=abc.ABCMeta):
    def save(self, path: PathLike):
        path = Path(path)
        super().save(path)
        self.data.to_csv(path)

    # noinspection PyAttributeOutsideInit
    def load(self, path: PathLike):
        path = Path(path)
        super().load(path)
        self.data = pd.read_csv(path)
        return self


class SaveLoadCsv(AbstractSaveLoad, metaclass=abc.ABCMeta):
    """Has an attribute (property) called ``data``."""

    @property
    @abc.abstractmethod
    def data(self) -> pd.DataFrame:
        """ """
        raise NotImplementedError()

    @data.setter
    def data(self, df: pd.DataFrame) -> None:
        raise NotImplementedError()

    @property
    def df_class(self) -> Type[pd.DataFrame]:
        """ """
        return pd.DataFrame

    def save(self, path: PathLike) -> None:
        if not isinstance(self.data, self.df_class):
            raise TypeError(f"Type {type(self.data)} is not a {self.df_class}")
        path = Path(path)
        pd.DataFrame(self.data).to_csv(path)

    def load(self, path: PathLike) -> None:
        path = Path(path)
        self.data = self.df_class(pd.read_csv(path))


class ClassifierPath:
    """
    A path with standard subpaths for trained model, decision functions, and standard plots.
    Sanitize the path beforehand -- it's not done here.
    The classifier might not support all the paths.

    Example:
        Uses::

            path = ClassifierPath('abc')
            print(path.weight_csv)  # will return path/'weight.csv'
            print(path.weight_csv.exists())  # might be false, even for a trained classifier

    Similarly, ``path.decision_csv`` will not exist if the model does not support training decision functions
    (typically out-of-bag).
    """

    def __init__(self, path: PathLike):
        self.path = Path(path)

    def prep(self):
        """ """
        PathTools.prep_dir(self.path, exist_ok=True)

    def load_info(self):
        """ """
        path = self.info_json
        return FilesysTools.load_json(path)

    def save_info(self, info) -> None:
        FilesysTools.save_json(info, self.info_json)

    def verify_exists(self) -> None:

        if not self.exists():
            raise PathError(f"No trained model under {self}", path=self.path)

    def verify_exists_with_decision(self) -> None:

        if not self.exists():
            raise PathError(f"No trained model under {self}", path=self.path)
        if not self.decision_csv.exists():
            raise PathError(f"No decision CSV under {self}", path=self.path)

    def exists_with_decision(self) -> bool:
        return self.exists() and self.decision_csv.exists()

    def exists(self) -> bool:
        return (
            self.path.exists()
            and self.path.is_dir()
            and self.model_pkl.exists()
            and self.model_pkl.is_file()
            and self.info_json.exists()
            and self.info_json.is_file()
        )

    def resolve(self) -> ClassifierPath:
        return ClassifierPath(self.path.resolve())

    def parent(self) -> Path:
        return self.path.parent

    def anchor(self) -> str:
        return self.path.anchor

    def name(self) -> str:
        return self.path.name

    def __truediv__(self, other: PathLike) -> Path:
        return self.path / other

    @property
    def model_pkl(self) -> Path:
        return self / "model.pkl"

    @property
    def info_json(self) -> Path:
        return self / "info.json"

    @property
    def cc_json(self) -> Path:
        return self / "cc.json"

    @property
    def decision_csv(self) -> Path:
        return self / "decision.csv"

    @property
    def weight_csv(self) -> Path:
        return self / "weight.csv.gz"

    @property
    def accuracy_csv(self) -> Path:
        return self / "accuracy.csv"

    @property
    def confusion_csv(self) -> Path:
        return self / "confusion.csv"

    @property
    def confusion_pdf(self) -> Path:
        return self / "confusion.pdf"

    @property
    def swarm_pdf(self) -> Path:
        return self / "swarm.pdf"

    @property
    def bar_pdf(self) -> Path:
        return self / "bar.pdf"

    @property
    def boxplot_pdf(self) -> Path:
        return self / "boxplot.pdf"

    @property
    def violin_pdf(self) -> Path:
        return self / "violin.pdf"

    def __repr__(self):
        return str(self.path)

    def __str__(self):
        return str(self.path)

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.path == other.path

    def __hash__(self):
        return hash(self.path)


__all__ = [
    "AbstractSaveLoad",
    "SaveableTrainable",
    "SaveableTrainableCsv",
    "SaveLoadCsv",
    "ErrorBehavior",
    "ClassifierPath",
]

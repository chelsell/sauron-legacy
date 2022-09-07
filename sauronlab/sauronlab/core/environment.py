from __future__ import annotations

import orjson
from pocketutils.tools.filesys_tools import FilesysTools
from valarpy.connection import Valar

from sauronlab.core._imports import *
from sauronlab.core.valar_singleton import *

MAIN_DIR = os.environ.get("SAURONLAB_DIR", Path.home() / ".sauronlab")
CONFIG_PATH = os.environ.get("SAURONLAB_CONFIG", MAIN_DIR / "sauronlab.config")
if CONFIG_PATH is None:
    raise FileDoesNotExistError(f"No config file at {CONFIG_PATH}")
MAIN_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path):
    return orjson.loads(path.read_text(encoding="utf8").encode(encoding="utf8"))


class PropSet:
    def __init__(self, props: Mapping[str, str]):
        self._props = props

    @classmethod
    def read(cls, config_file: Path) -> PropSet:
        """ """
        try:
            return PropSet(
                {
                    k: v.strip("\t '\"")
                    for k, v in FilesysTools.read_properties_file(config_file).items()
                }
            )
        except ParsingError as e:
            raise MissingConfigKeyError(f"Bad sauronlab config file {config_file}") from e

    def resource(self, *names: str) -> Path:
        return SauronlabResources.path(*names)

    def str(self, key: str, fallback: Optional[str] = None) -> str:
        value = self._props.get(key, fallback)
        if value is None:
            raise MissingConfigKeyError(f"Must specify ${key} in config file")
        return value

    def str_nullable(self, key: str, fallback: Optional[str] = None) -> Optional[str]:
        return self._props.get(key, fallback)

    def int(self, key: str, fallback: Optional[int] = None) -> int:
        return int(self.str(key, str(fallback)))

    def int_nullable(self, key: str, fallback: Optional[str] = None) -> Optional[int]:
        return int(self.str_nullable(key, fallback))

    def bool(self, key: str, fallback: bool) -> bool:
        return CommonTools.parse_bool(self._props.get(key, fallback))

    def dir(self, key: str, fallback: Path) -> Path:
        if key in self._props:
            path = Path(self._props.get(key)).expanduser()
        else:
            path = fallback
        path.mkdir(parents=True, exist_ok=True)
        return path

    def file(self, key: str, fallback: Path) -> Path:
        if key in self._props:
            path = Path(self._props.get(key)).expanduser()
        else:
            path = fallback
        if not path.is_file():
            raise MissingResourceError(f"No viz file at path {path}")
        return path

    def __len__(self) -> int:
        return len(self._props)


@abcd.auto_repr_str()
@abcd.auto_eq(exclude=None)
@abcd.auto_info()
class SauronlabEnvironment:
    """
    A collection of settings for Sauronlab.
    Python files in Sauronlab use this singleton class directly.
    This is loaded from a file in the user's home directory at ~/sauronlab.config.

    Attributes:
        - username: The username in valar.users; no default
        - cache_dir: The location of the top-level cache path; defaults to ~/valar-cache
        - video_cache_dir:  The location of the cache for videos; defaults to  ~/valar-cache/videos
        - shire_path: The local or remote path to the Shire (raw data storage); by default this a location on Valinor
        - audio_waveform: Sauronlab will **save** StimFrame objects to the cache with audio waveforms; Enabling this will cause audio_waveform= arguments to be always true
        - matplotlib_style: The path to a Matplotlib stylesheet; defaults to Matplotlib default
        - use_multicore_tsne: Enable the multicore_tsne package
        - joblib_compression_level: Used in joblib.dump compress parameter if the filename ends with one of (‘.z’, ‘.gz’, ‘.bz2’, ‘.xz’ or ‘.lzma’); 3 by default
        - sauronlab_log_level: The log level recommended to be used for logging statements within Sauronlab; set up by jupyter.py
        - global_log_level: The log level recommended to be used for logging statements globally; set up by jupyter.py
        - viz_file: Path to sauronlab-specific visualization options in the style of Matplotlib RC
        - n_cores: Default number of cores for some jobs, including with parallelize()
        - jupyter_template: Path to a Jupyter template text file

    """

    def __init__(self):
        """"""
        self.config_file = Path(CONFIG_PATH).expanduser()
        if not self.config_file.exists():
            raise MissingResourceError(f"No config file at path {self.config_file}")
        props = PropSet.read(self.config_file)
        # fmt: off
        self.whereami                 = Path(__file__).parent.parent
        self.valarpy_path             = Path(props.str("valarpy_config", MAIN_DIR / "connection.json"))
        self.valarpy_data             = _read_json(self.valarpy_path)
        self.tunnel_host              = props.str_nullable("tunnel_host", None)
        self.tunnel_port              = props.str_nullable("tunnel_port", None)
        self.username                 = props.str("username")
        self.sauronlab_log_level      = props.str("sauronlab_log_level", "MINOR")
        self.global_log_level         = props.str("global_log_level", "INFO")
        self.cache_dir                = props.dir("cache", MAIN_DIR / "cache")
        self.video_cache_dir          = props.dir("video_cache", Path(self.cache_dir, "videos"))
        self.dataset_cache_dir        = props.dir("dataset_cache", Path(self.cache_dir, "datasets"))
        self.shire_path               = props.str_nullable("shire_path", None)
        self.use_multicore_tsne       = props.bool("multicore_tsne", False)
        self.joblib_compression_level = props.int("joblib_compression_level", 3)
        self.n_cores                  = props.int("n_cores", 1)
        self.jupyter_template         = props.file("jupyter_template", props.resource("templates", "jupyter.txt"))
        self.matplotlib_style         = props.file("matplotlib_style", props.resource("styles", "default.mplstyle"))
        self.sauronlab_style          = props.file("viz_file", props.resource("styles", "default.properties"))
        self.user                     = Users.fetch(self.username)
        self.user_ref                 = Refs.fetch_or_none("manual:" + self.username)
        # fmt: on
        # verification
        if self.user_ref is None:
            logger.warning(f"manual:{self.username} is not in ``refs``. Using 'manual'.")
        else:
            self.user_ref = Refs.fetch_or_none("manual")
        # adjust logging, initialization, etc.
        # self._adjust_logging() # _adjust_logging() isn't here defined nor do I know where it might be CH
        logger.info(f"Read {self.config_file} .")
        logger.info(
            f"Set {len(props)} sauronlab config items. Run 'print(sauronlab_env.info())' for details."
        )

    def reload(self) -> None:
        self.__init__()


sauronlab_env = SauronlabEnvironment()

__all__ = ["SauronlabEnvironment", "sauronlab_env"]

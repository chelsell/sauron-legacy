from __future__ import annotations

import ast
import textwrap
from functools import total_ordering

import matplotlib
import matplotlib.cm as cmaps
from matplotlib import colors as mcolors
from matplotlib.figure import Figure
from matplotlib.markers import MarkerStyle
from pocketutils.plotting.color_schemes import *
from pocketutils.plotting.ref_dims import RefDims

from sauronlab.core.core_imports import *
from sauronlab.viz import plt


@total_ordering
class TimeUnit:
    def __init__(self, unit: str, abbrev: str, singlular: str, n_ms: int):
        self.unit, self.abbrev, self.singular, self.plural, self.n_ms = (
            unit,
            abbrev,
            singlular,
            singlular + "s",
            n_ms,
        )

    def to_ms(self, n: int) -> int:
        """


        Args:
            n: int:

        Returns:

        """
        return n * self.n_ms

    def __eq__(self, other):
        return self.n_ms == other.n_ms

    def __lt__(self, other):
        return self.n_ms < other.n_ms

    def __repr__(self):
        return "⟨" + self.abbrev + "⟩"

    def __str__(self):
        return "⟨" + self.abbrev + "⟩"


class TimeUnits:

    MS = TimeUnit("ms", "ms", "millisecond", 1)
    SEC = TimeUnit("s", "sec", "second", 1000)
    MIN = TimeUnit("min", "min", "minute", 1000 * 60)
    HOUR = TimeUnit("hr", "hour", "hour", 1000 * 60 * 60)
    DAY = TimeUnit("day", "day", "day", 1000 * 60 * 60 * 24)
    WEEK = TimeUnit("wk", "week", "week", 1000 * 60 * 60 * 24 * 7)

    @classmethod
    def values(cls):

        return [
            TimeUnits.MS,
            TimeUnits.SEC,
            TimeUnits.MIN,
            TimeUnits.HOUR,
            TimeUnits.DAY,
            TimeUnits.WEEK,
        ]

    @classmethod
    def of(cls, s: Union[TimeUnit, str]) -> TimeUnit:
        if isinstance(s, TimeUnit):
            return s
        s = s.lower().strip()
        for u in TimeUnits.values():
            if s in [u.abbrev, u.plural, u.singular, u.unit]:
                return u
        raise LookupError(f"Unit type {s} not found")


class KvrcDefaults:
    """
    Some default and legacy default values for sauronlab_rc.
    """

    trace_pref_tick_ms_interval = InternalTools.load_resource("viz", "ms_ticks.ints")

    markers = InternalTools.load_resource("viz", "markers.strings")

    dark_colors = FancyColorSchemes.qualitiative_26()
    light_colors = FancyColorSchemes.qualitiative_26()
    treatment_colors = FancyColorSchemes.qualitiative_26()

    control_colors = FancyColorSchemes.grayscales()[1:]

    control_color_dict = {"solvent (-)": "#777777", "killed (+)": "#000000", "empty (-)": "#aaaaaa"}

    legacy_trace_treatment_colors = ["#ff0000", "#00aa44", "#0000ff", "#cc00cc"]
    legacy_trace_control_colors = ["#000000", "#000066", "#550044"]

    cmap = copy(cmaps.get_cmap("Greys"))
    cmap.set_bad("#f8f8ff")


T = TypeVar("T", covariant=True)


@abcd.auto_repr_str()
@abcd.auto_hash()
@abcd.total_ordering
class Key:
    """
    A Key is an available setting in sauronlab_rc.
    It may be 'resolved' -- has a fixed ``value`` -- or not.
    If ``is_resolved``, ``value`` is the ultimate value after reading the config file.
    Otherwise, ``value`` will be None.
    (Note that the ``value`` may actually be None when resolved.)
    """

    __slots__ = ["key", "kind", "fallback", "nullable", "desc", "value", "is_resolved"]

    def __init__(
        self,
        key: str,
        kind: Callable[[str], T],
        fallback: T,
        nullable: bool = False,
        desc: Optional[str] = None,
        value: Optional[T] = None,
        is_resolved: bool = False,
    ):
        self.key, self.kind, self.fallback, self.nullable, self.desc = (
            key,
            kind,
            fallback,
            nullable,
            desc,
        )
        self.value, self.is_resolved = value, is_resolved

    def resolved(self, value: Optional[str]) -> Key:
        """
        Process the user-passed ``value`` (or None if it was not passed).
        Then return a copy of this Key with ``Key.value`` set to the user-passed value or the fallback.

        Args:
            value: Should be None iff it was not set in config file

        Returns:
            A new Key

        Raises:
            OpStateError: If it has a non-None ``Key.value`` (it's already been resolved)
        """
        if self.value is not None:
            raise OpStateError(f"Cannot resolve {self.key} again")
        if value is None:  # not set
            value = self.fallback
        else:
            try:
                value = self._parse(value)
                return Key(self.key, self.kind, self.fallback, self.nullable, self.desc, value)
            except (ValueError, TypeError, ArithmeticError):
                raise ConfigError(f"Value {value} for key {self.key} is not of type {self.kind}")
        return Key(self.key, self.kind, self.fallback, self.nullable, self.desc, value)

    def __lt__(self, other):
        if not isinstance(other, Key):
            raise XTypeError(f"{other} is not a Key")
        return self.key < other.key

    def _parse(self, value: str) -> Optional[T]:
        assert value is not None
        value = self._strip(value)
        if self.nullable and value.strip().lower() == "none":
            return None
        else:
            return self.kind(value)

    def _strip(self, value: str) -> str:
        return value.strip().strip('"').strip("'")


@abcd.mutable
@abcd.auto_repr()
@abcd.auto_str()
class KvrcConfig:
    """
    The collection of resolved (fixed; set from config file) sauronlab_rc ``Key``s.
    It contains ``SauronlabConfig.collection``, which is a dict mapping key strings to resolved ``Key``s.

    Example:
        For ex, ``collection`` might contain::

        {
            'stamp_font_size': Key('stamp_font_size', float, 9).resolved(5)
        }

    ``collection`` is mutable, with keys added through the ``key`` method.
    In practice, we'll instead call the methods corresponding to the desired types, such as ``KvrcCdonfig.new_enum``.

    """

    def __init__(self, passed: Mapping[str, str]):
        self.passed = passed
        self.collection = {}

    def key(
        self,
        key: str,
        kind: Callable[[str], T],
        fallback: T,
        nullable: bool = False,
        d: Optional[str] = None,
    ) -> T:
        """
        Adds a new ``Key`` to the collection. (Calls the ``Key`` constructor.)

        Args:
            key: The name of the key (ex: 'stamp_font_size')
            kind: A function mapping a user-passed string to the required type
            fallback: A default value of type T applied when the key isn't listed in the config file
            nullable: Whether the user can set the key to None (ex: 'stamp_font_size=none'); independent of the fallback
            d: An optional description of the key

        Returns:
            The resolved value of the inserted key; this is the same as ``config.collection['stamp_font_size'].value)

        """
        key_obj = Key(key, kind, fallback, nullable, d)
        key_obj = key_obj.resolved(self.passed.get(key))
        self.collection[key] = key_obj
        if key in self.passed:
            logger.trace(key, key_obj.value, self.passed)
        return key_obj.value

    def __len__(self):
        return len(self.collection)

    def new_str(
        self, key: str, fallback: Optional[str], desc: Optional[str] = None
    ) -> Optional[str]:
        return self.key(key, lambda v: v, fallback, d=desc)

    def new_classmethod(
        self, key: str, fallback: Optional[List[str]], inclass: Type, desc: Optional[str] = None
    ) -> Optional[Callable[[], None]]:
        def find(v):
            return getattr(FancyColorSchemes, v)

        return self.key(key, find, fallback, d=desc)

    def new_enum(
        self, key: str, fallback: Optional[str], choices: Set[str], desc: Optional[str] = None
    ) -> Optional[str]:
        def en(v):
            if v not in choices:
                raise ConfigError(f"{v} is not in {choices}")
            return v

        return self.key(key, en, fallback, d=desc)

    def new_str_list(
        self, key: str, fallback: Optional[List[str]], desc: Optional[str] = None
    ) -> Optional[List[str]]:
        return self.key(key, lambda v: self._eval_list(v, str), fallback, d=desc)

    def new_raw_dict(
        self, key: str, fallback: Optional[Dict[str, Any]], desc: Optional[str] = None
    ) -> Optional[Dict[Any]]:
        return self.key(key, lambda v: self._eval_dict(v, str), fallback, d=desc)

    def new_str_dict(
        self, key: str, fallback: Optional[Dict[str, str]], desc: Optional[str] = None
    ) -> Optional[Dict[str]]:
        return self.key(key, lambda v: self._eval_dict(v, str), fallback, d=desc)

    def new_marker(
        self, key: str, fallback: Optional[str], desc: Optional[str] = None
    ) -> Optional[str]:
        def lam(v):
            if v not in MarkerStyle.markers.keys():
                raise ConfigError(f"{v} is not a valid marker style")

        return self.key(key, lam, fallback, d=desc)

    def new_marker_list(
        self, key: str, fallback: Optional[List[str]], desc: Optional[str] = None
    ) -> Optional[List[str]]:
        return self.key(key, lambda v: self._eval_list(v, str), fallback, d=desc)

    def new_marker_dict(
        self, key: str, fallback: Optional[Dict[str, str]], desc: Optional[str] = None
    ) -> Optional[Dict[str]]:
        return self.key(
            key, lambda v: self._eval_dict(v, str), fallback, d=desc
        )  # exact Python syntax

    def new_color_dict(
        self, key: str, fallback: Optional[Dict[str, str]], desc: Optional[str] = None
    ) -> Optional[Dict[str]]:
        return self.key(
            key,
            lambda values: {k: mcolors.to_rgb(v) for k, v in ast.literal_eval(values)},
            fallback,
            d=desc,
        )  # exact Python syntax

    def new_bool(self, key: str, fallback: bool, desc: Optional[str] = None) -> bool:
        return self.key(key, lambda b: Tools.parse_bool(b), fallback, d=desc)

    def new_float(
        self,
        key: str,
        fallback: float,
        minimum: Optional[float] = None,
        maximum: Optional[float] = None,
        desc: Optional[str] = None,
    ) -> Optional[float]:
        return self.key(
            key,
            lambda v: self._conv_float(key=key, value=v, minimum=minimum, maximum=maximum),
            fallback,
            d=desc,
        )

    def new_time_unit(
        self, key: str, fallback: Optional[TimeUnit], desc: Optional[str] = None
    ) -> Optional[TimeUnit]:
        return self.key(key, TimeUnits.of, fallback, d=desc)

    def new_float_list(
        self, key: str, fallback: List[float], desc: Optional[str] = None
    ) -> List[float]:
        return self.key(key, lambda v: self._eval_list(v, float), fallback, d=desc)

    def new_float_tuple(
        self, key: str, fallback: Optional[Tup[float, float]], desc: Optional[str] = None
    ) -> Optional[Tup[float, float]]:
        def ftup(v) -> Tup[float, float]:
            z = self._eval_list(v, float)
            a, b = float(z[0]), float(z[1])
            return a, b

        return self.key(key, ftup, fallback, d=desc)

    def new_int(
        self,
        key: str,
        fallback: int,
        minimum: Optional[int] = None,
        maximum: Optional[int] = None,
        desc: Optional[str] = None,
    ) -> Optional[int]:
        return self.key(
            key,
            lambda v: self._conv_int(key=key, value=v, minimum=minimum, maximum=maximum),
            fallback,
            d=desc,
        )

    def new_int_list(self, key: str, fallback: List[int], desc: Optional[str] = None) -> List[int]:
        return self.key(key, lambda v: self._eval_list(v, int), fallback, d=desc)

    def new_font_weight(self, key: str, fallback: Optional[str], desc: Optional[str] = None) -> str:
        def fw(value):
            if key not in {"normal", "bold", "heavy", "light", "ultrabold", "ultralight"}:
                raise ConfigError(f"Font weight {value} not understood for {key}")
            return value

        return self.key(key, fw, fallback, d=desc)

    def new_rgb(self, key: str, fallback: str, desc: Optional[str] = None) -> str:
        return self.key(key, lambda v: mcolors.to_rgb(v), fallback, d=desc)

    def new_rgb_list(self, key: str, fallback: List[str], desc: Optional[str] = None) -> List[str]:
        return self.key(key, lambda v: mcolors.to_rgb(v), fallback, d=desc)

    def new_alpha(self, key: str, fallback: float, desc: Optional[str] = None) -> float:
        return self.key(
            key,
            lambda v: self._conv_float(key=key, value=v, minimum=0, maximum=1),
            fallback,
            d=desc,
        )

    def new_fraction(self, key: str, fallback: float, desc: Optional[str] = None) -> float:
        return self.key(
            key,
            lambda v: self._conv_float(key=key, value=v, minimum=0, maximum=1),
            fallback,
            d=desc,
        )

    def new_alpha_list(
        self, key: str, fallback: List[float], desc: Optional[str] = None
    ) -> List[float]:
        def alphas(v: str):
            z = self._eval_list(v, str)
            return [self._conv_float(key, x, minimum=0, maximum=1) for x in z]

        return self.key(key, alphas, fallback, d=desc)

    def new_font_size(self, key: str, fallback: float, desc: Optional[str] = None) -> float:
        return self.key(
            key,
            lambda v: self._conv_float(key=key, value=v, minimum=0, maximum=100),
            fallback,
            d=desc,
        )

    def new_cmap(
        self, key: str, fallback: Optional[str], desc: Optional[str] = None
    ) -> Optional[str]:
        return self.key(key, lambda v: v, fallback, d=desc)

    def new_length(self, key: str, fallback: float, desc: Optional[str] = None) -> float:
        return self.key(
            key,
            lambda v: self._conv_float(key=key, value=v, minimum=0, maximum=None),
            fallback,
            d=desc,
        )

    def new_line_width(self, key: str, fallback: float, desc: Optional[str] = None) -> float:
        return self.key(
            key,
            lambda v: self._conv_float(key=key, value=v, minimum=0, maximum=None),
            fallback,
            d=desc,
        )

    def new_line_style(self, key: str, fallback: Optional[str], desc: Optional[str] = None) -> str:
        return self.key(key, lambda v: v, fallback, d=desc)

    def new_point_size(self, key: str, fallback: float, desc: Optional[str] = None) -> float:
        return self.key(
            key,
            lambda v: self._conv_float(key=key, value=v, minimum=0, maximum=None),
            fallback,
            d=desc,
        )

    def _conv_float(
        self, key: str, value: str, minimum: Optional[float], maximum: Optional[float]
    ) -> float:
        f = float(value)
        if minimum is not None and f < minimum:
            raise ConfigError(f"Value for key {key} below minimum of {minimum}")
        if maximum is not None and f > maximum:
            raise ConfigError(f"Value for key {key} above maximum of {maximum}")
        return f

    def _conv_int(
        self, key: str, value: str, minimum: Optional[int], maximum: Optional[int]
    ) -> int:
        if "." in str(value):
            raise ConfigError(f"Value for key {key} is not an integer")
        f = int(value)
        if minimum is not None and f < minimum:
            raise ConfigError(f"Value for key {key} below minimum of {minimum}")
        if maximum is not None and f > maximum:
            raise ConfigError(f"Value for key {key} above maximum of {maximum}")
        return f

    def _eval_dict(self, value: str, vtypes):
        """
        Parse a string into a dictionary where keys are strings and values are of the type ``vtypes``.
        Requires exact Python syntax using ``ast.literal_eval``.

        """
        raw = ast.literal_eval(value)  # exact Python syntax
        if vtypes is None:
            return {str(a): b for a, b in raw.items()}
        else:
            return {str(a): vtypes(b) for a, b in raw.items()}

    def _eval_list(self, value: str, vtypes) -> List[Any]:
        """
        Parse a string into a list where keys are strings and values are of the type ``vtypes``.
        Strips off any kind of bracket (if paired -- at both start and end), then splits by commas (,).
        """
        return [vtypes(v) for v in Tools.strip_brackets(value).split(",")]


class KvrcCore:
    """
    A base without specific param values.
    """

    def __init__(
        self, matplotlib_style_path: Optional[PathLike], kvrc_style_path: Optional[PathLike]
    ):
        self.stimulus_names, self._stimulus_names = None, None
        self.stimulus_colors, self._stimulus_colors = None, None
        self.feature_names, self._feature_names = None, None
        self.control_names, self._control_names = None, None
        self._matplotlib_style_path, self._kvrc_style_path = matplotlib_style_path, kvrc_style_path
        self.widths = RefDims("width")
        self.heights = RefDims("height")
        self.load(matplotlib_style_path, kvrc_style_path)
        self.widths.n_sigfigs = self.heights.n_sigfigs = self["general_dims_sigfigs"]
        self.collection = None

    def defaults(self) -> Mapping[str, Any]:
        """Gets the fallback (default) values for all available keys."""
        return {k.key: k.fallback for k in self.collection}

    def search(self, s: str) -> Mapping[str, Any]:
        """
        Finds keys with ``s`` as a substring, returning the current values.
        """
        return {k: v for k, v in self.__dict__ if s in k}

    def reload(self) -> None:
        """
        Does two things:
            - Sets the matplotlib style (``plt.style.use``) if it's not None
            - Reloads the sauronlab_rc settings from ``kvrc_style_path`` if it's not None

        Also sets the attributes ``matplotlib_style_path`` and ``kvrc_style_path``, only when they're not None.
        """
        self.load(self._matplotlib_style_path, self._kvrc_style_path)

    def load(
        self, matplotlib_style_path: Optional[PathLike], kvrc_style_path: Optional[PathLike]
    ) -> None:
        """
        Reads and loads the matplotlib and sauronlab_rc style file, if they're not ``None``.
        """
        if matplotlib_style_path is not None:
            self._load_mpl(matplotlib_style_path)
        if kvrc_style_path is not None:
            self._load_kvrc(kvrc_style_path)

    def _load_mpl(self, matplotlib_style_path: PathLike) -> None:
        self._matplotlib_style_path = matplotlib_style_path
        plt.style.use(str(matplotlib_style_path))
        # IT TURNS OUT WE NEED TO SET BOTH!!!!
        matplotlib.rcParams.update(plt.rcParams)
        if matplotlib_style_path is None:
            mpl_read = {}
        else:
            mpl_read = dict(
                matplotlib.rc_params_from_file(
                    str(matplotlib_style_path), use_default_template=False
                )
            )
        logger.info(f"Loaded {len(mpl_read)} matplotlib RC settings from {matplotlib_style_path}")
        logger.debug(f"Set matplotlib settings {mpl_read}")

    def _load_kvrc(self, kvrc_style_path: PathLike) -> None:
        self._kvrc_style_path = kvrc_style_path
        try:
            viz_params = Tools.read_properties_file(str(kvrc_style_path))
        except ParsingError as e:
            raise ConfigError("Bad sauronlab_rc file {kvrc_style_path}") from e
        config = KvrcConfig(viz_params)
        # set everything in subclass
        self._load_settings(config)
        # build our special dictionaries up specially
        # first, set them back to None so they'll be rebuilt (in case we're reloading)
        # then call the so-called 'get' functions to read and set them
        self.stimulus_names = None
        self.stimulus_colors = None
        self.feature_names = None
        self.control_names = None
        # set width and height reference dims
        for k, v in viz_params.items():
            if k.startswith("width_"):
                self.widths[k.replace("width_", "")] = float(v)
            if k.startswith("height_"):
                self.heights[k.replace("height_", "")] = float(v)
        self.get_stimulus_names()
        self.get_stimulus_colors()
        self.get_feature_names()
        # find keys that don't exist to complain
        for k, v in viz_params.items():
            if (
                k not in self.__dict__.keys()
                and not k.startswith("width_")
                and not k.startswith("height_")
            ):
                raise UnrecognizedKeyError(f"Viz key '{k}' was not recognized")
        # log important info
        logger.info(f"Loaded {len(config.passed)} Sauronlab viz settings from {kvrc_style_path}")
        if len(self.widths) + len(self.heights) > 0:
            logger.info(
                "Set {} reference widths and heights. Pad is ({}, {}). Gutter is {}.".format(
                    len(self.widths) + len(self.heights),
                    self.widths.get("pad", 0.0),
                    self.heights.get("pad", 0.0),
                    self.widths.get("gutter", 0.0),
                )
            )
        else:
            logger.info("No reference widths or heights set.")
        logger.debug(f"Set sauronlab_rc settings {viz_params}")

    def _load_settings(self, config: KvrcConfig):
        """
        We'll override this in the subclass.
        """
        raise NotImplementedError()

    # noinspection PyAttributeOutsideInit
    def get_feature_names(self) -> Dict[str, str]:
        """
        Returns ``feature_names`` if it's already built (not None).
        If ``feature_names`` is None, sets it in terms of ``_feature_names`` from the config file.
        The dict maps *internal names* (``Featuretype.internal_name``) to display names.
        If not set in ``_feature_names``, the display name will be ``FeatureType.feature_name``.
        """
        if self.feature_names is None:
            self.feature_names = {}
            from sauronlab.model.features import FeatureTypes

            for f in FeatureTypes.known:
                if f.internal_name not in self._feature_names:
                    self.feature_names[f.internal_name] = f.feature_name
            self.feature_names.update(self._feature_names)
        return self.feature_names

    def set_feature_names(self, **dct):
        """
        Updates items in the ``feature_names`` dictionary, replacing them if they already exist.
        Note: Does not modify ``_feature_names`` (passed in the config file).
        """
        self.feature_names.update(dct)

    # noinspection PyAttributeOutsideInit
    def get_stimulus_names(self) -> Dict[str, str]:
        """
        Returns ``stimulus_names`` if it's already built (not None).
        If ``stimulus_names`` is None, sets it in terms of ``_stimulus_names`` from the config file.
        The dict maps control_type names (``Stimuli.name``) to display names.
        If not set in ``_stimulus_names``, the display name will be ``ValarTools.stimulus_display_name(stimulus.name)``.
        """
        if self.stimulus_names is None:
            self.stimulus_names = {}
            for s in Stimuli.select():
                if s.name not in self._stimulus_names:
                    self.stimulus_names[s.name] = ValarTools.stimulus_display_name(s.name)
        return self.stimulus_names

    def set_stimulus_names(self, **dct) -> None:
        """
        Updates items in the ``stimulus_names`` dictionary, replacing them if they already exist.
        Note: Does not modify ``_stimulus_names`` (passed in the config file).
        """
        self.stimulus_names.update(dct)

    # noinspection PyAttributeOutsideInit
    def get_stimulus_colors(self) -> Dict[str, str]:
        """
        Returns ``stimulus_colors`` if it's already built (not None).
        If ``stimulus_colors`` is None, sets it in terms of ``_stimulus_colors`` from the config file.
        The dict maps control_type names (``Stimuli.name``) to colors.
        If not set in ``_stimulus_colors``, the color will be ``ValarTools.stimulus_display_color(stimulus.name)``.
        """
        if self.stimulus_colors is None:
            self.stimulus_colors = dict(ValarTools.stimulus_display_colors())
            # slightly weird to update; maybe I anticipated stimuli being added?
            for s in Stimuli.select():
                if s.name not in self._stimulus_colors:
                    self.stimulus_colors[s.name] = "#" + s.default_color
            self.stimulus_colors.update(self.stimulus_colors)
        return self.stimulus_colors

    def set_stimulus_colors(self, **dct) -> None:
        """
        Updates items in the ``stimulus_colors`` dictionary, replacing them if they already exist.
        Note: Does not modify ``_stimulus_colors`` (passed in the config file).
        """
        self.stimulus_colors.update(dct)

    @property
    def width(self):
        return plt.rcParams["figure.figsize"][0]

    @width.setter
    def width(self, value):
        raise UnsupportedOpError("Cannot modify width. Use sauronlab_rc['width']")

    @property
    def height(self):

        return plt.rcParams["figure.figsize"][1]

    @height.setter
    def height(self, value):
        raise UnsupportedOpError("Cannot modify height. Use sauronlab_rc['height']")

    @property
    def figsize(self):

        return plt.rcParams["figure.figsize"]

    @contextmanager
    def using(self, *args, **kwargs: Mapping[str, Any]):
        """
        Temporarily sets Sauronlab-specific or matplotlib settings.

        Args:
            args: If present, these are functions that accept *this* SauronlabRc, modifies it, and returns nothing
            kwargs: If present, these are key-value pairs where the keys are of SauronlabRc settings or matplotlib RC params,
                    and the values are the new values.
                    Periods (.) are automatically converted to underscores.

        Returns:
            A Python context manager with these options set

        Examples:
            Example 1::

                with sauronlab_rc.using(trace_legend_n_cols=2, axes_prop_cycle=kbgrcmy):
                quick.trace(5)

            Example 2::

                def my_common_styler(kv):
                kv['trace_legend_n_cols'] = 2
                kv['axes.prop_cycle'] = 'kbgrcmy'
                kv['stamp_on'] = False
                with sauronlab_rc.using(my_common_styler):
                    quck.trace(5)

          You can of course combine these two types of arguments (functions and keyword arguments).
          Has special behavior when setting ``width``, ``height``, and ``figure.figsize``:
          If any of these are set, it sets the others in terms of it.
          Also see: ``set_mplstyle``, which sets

        """
        if not all((callable(a) for a in args)):
            raise XTypeError(
                "Non-keyword arguments to ``sauronlab_rc.using`` (if present), must be functions of the SauronlabEnv that modify its settings."
            )
        if not all((isinstance(k, str) for k, v in kwargs.items())):
            raise XTypeError(
                "Keyword arguments to ``sauronlab_rc.using`` (if present), must map names of matplotlib or sauronlab viz settings to their values."
            )
        mplstuff = deepcopy(plt.rcParams)
        prev = deepcopy(self.__dict__)
        for arg in args:
            arg(self)
        for k, v in kwargs.items():
            self[k] = v
        yield self
        plt.rcParams = mplstuff
        for k in prev.keys():
            setattr(self, k, prev[k])
        logger.debug("Exited kvrc.")

    def __setitem__(self, item: str, value: Any):
        """
        Modifies sauronlab or matplotlib settings in place. Looks up:
            1. ``item`` in the available sauronlab_rc keys
            2. ``item`` in maptlotlib rcParams
            3. ``item.replace('_', '.', 1)``  in matplotlib rcParams

        However, has special behavior for figsize-related arguments:
            If ``item`` is any of ``width``, ``height``, or ``figure.figsize``,
            sets the remaining ones in terms of it.
            Ex: setting ``width`` will also change ``figsize[0]``, and vice versa.

        Raises:
            SauronlabKeyError: If the key wasn't found in any of the 3 places
        """
        item = item.strip()
        if item in self.__dict__.keys():
            setattr(self, item, value)
        elif item == "width":
            width = self.widths.point(value)
            self._update("figure.figsize", (width, self.height))
        elif item == "height":
            height = self.heights.point(value)
            self._update("figure.figsize", (self.width, height))
        elif item == "figsize":
            width = self.widths.point(value[0])
            height = self.heights.point(value[1])
            self._update("figure.figsize", (width, height))
        elif item in plt.rcParams:
            plt.rcParams[item] = value
        elif item.replace("_", ".", 1) in plt.rcParams:
            self._update(item.replace("_", ".", 1), value)
        else:
            raise UnrecognizedKeyError(f"No visualization setting {item}")

    def _update(self, item: str, value):
        plt.rcParams[item] = value
        # IT TURNS OUT WE NEED TO SET BOTH!!!!
        # You can't just set plt.rcParams --- you also need to set matplotlib.rcParams
        matplotlib.rcParams[item] = value
        return value

    def __getitem__(self, item: str) -> Any:
        """
        Looks up:
            1. ``item`` in the available sauronlab_rc keys
            2. ``item`` in matplotlib rcParams
            3. ``item.replace('_', '.', 1)``  in matplotlib rcParams
        """
        item = item.strip()
        if item in self.__dict__.keys():
            return getattr(self, item)
        elif item.startswith("width_"):
            return self.widths[item.replace("width_", "")]
        elif item.startswith("height_"):
            return self.heights[item.replace("height_", "")]
        elif item == "width":
            return plt.rcParams["figure.figsize"][0]
        elif item == "height":
            return plt.rcParams["figure.figsize"][1]
        elif item == "figsize":
            return plt.rcParams["figure.figsize"]
        elif item in plt.rcParams:
            return plt.rcParams[item]
        elif item.replace("_", ".") in plt.rcParams:
            return plt.rcParams[item.replace("_", ".")]
        elif item == "__module__":
            logger.error("sauronlab_rc might be reloading")
            return "sauronlab.viz.kvrc"  # 'No visualization setting __module__'
        else:
            raise UnrecognizedKeyError(f"No visualization setting {item}")

    def __iter__(self) -> Iterator[str]:
        """
        Iterates over all config option keys.
        """
        return iter([key for key in self.__dict__.keys() if not key.startswith("_")])

    def __len__(self):
        """
        Returns the total number of options, whether default or not.
        """
        return len(list(self))

    def plot_palette(self, values: Union[Sequence[str], str]) -> Figure:
        """
        Plots a color palette.

        Args:
            values: A string of a color (starting with #), a sequence of colors (each starting with #),
                    or the name of the sauronlab_rc setting (ex: pref_treatment_colors).
        """
        if isinstance(values, str) and not values.startswith("#"):
            values = list(self[values])
        n = len(values)
        figure = plt.figure(figsize=(8.0, 2.0))
        ax = figure.add_subplot(1, 1, 1)
        ax.pcolormesh(
            np.arange(n).reshape(1, n),
            cmap=mcolors.ListedColormap(values),
        )
        ax.set_yticks([])
        ax.set_yticks([])
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.spines["top"].set_visible(False)
        ax.spines["bottom"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.get_xaxis().set_ticks([])
        ax.get_yaxis().set_ticks([])
        return figure

    def print_defaults(self) -> None:
        """
        Prints the collection of default values.
        """
        print("\n".join(["{:50} = {}".format(v.key, v.fallback) for v in self.collection.values()]))

    def print(self) -> None:
        """
        Prints the collection of current values.
        """
        print("\n".join(["{:50} = {}".format(v.key, v.value) for v in self.collection.values()]))

    def print_wrapped(self, length: int = 75) -> None:
        """
        Print a nice, long, wrapped string describing all the options and their values.

        Args:
            length: Max number of characters per line
        """
        print(
            "\n".join(
                [
                    "{:45} = {}".format(
                        k,
                        "\n".join(
                            [
                                (" " * 46 if i > 0 else "") + t
                                for i, t in enumerate(
                                    textwrap.wrap(str(v).replace("\\n", "\n"), length)
                                )
                            ]
                        ),
                    )
                    for k, v in self.collection.items()
                ]
            )
        )


__all__ = ["KvrcDefaults", "KvrcConfig", "KvrcCore", "FancyColorSchemes"]

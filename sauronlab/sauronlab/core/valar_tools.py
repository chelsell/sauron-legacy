from natsort import natsorted
from PIL import Image
from pocketutils.core.dot_dict import NestedDotDict
from pocketutils.core.enums import CleverEnum

from sauronlab.core._imports import *
from sauronlab.core._tools import *
from sauronlab.core.data_generations import DataGeneration
from sauronlab.core.tools import *
from sauronlab.core.valar_singleton import *
from sauronlab.model.sensor_names import SensorNames

_stimulus_display_colors = {
    s.name: "#" + s.default_color if s.audio_file is None else "black" for s in Stimuli.select()
}
_stimulus_display_colors.update(InternalTools.load_resource("core", "stim_colors.json"))
_stimulus_replace = {s.name: s.name for s in Stimuli.select()}
_stimulus_replace.update(InternalTools.load_resource("core", "stim_names.json"))

_problematic_controls = frozenset(ControlTypes.fetch_all(["near-WT (-)", "low drug transfer"]))
_trash_controls = frozenset(ControlTypes.fetch_all(["ignore", "no drug transfer"]))


class StimulusType(CleverEnum):

    LED = ()
    AUDIO = ()
    SOLENOID = ()
    NONE = ()
    IR = ()


class ValarTools:
    """
    Miscellaneous user-facing tools specific to the data we have in Valar.
    For example, uses our definition of a library plate ID.
    Some of these functions simply call their equivalent Tools or InternalTools functions.

    """

    MANUAL_HIGH_REF = Refs.fetch_or_none("manual:high")
    MANUAL_REF = Refs.fetch("manual")
    # These values were hardcoded into the drivers of a legacy hardware setup
    # The framerate was locked to 25 fps (but could deviate below)
    # In addition, we used a definition for the battery (stimulus frames) of 1 stimulus frame per camera frame
    LEGACY_FRAMERATE = 25
    LEGACY_STIM_FRAMERATE = 25

    @classmethod
    def required_sensors(cls, generation: DataGeneration) -> Mapping[str, Sensors]:
        gens = {x["name"]: x for x in InternalTools.load_resource("core", "generations.json")}
        sensors = gens[generation.name]["sensors"]
        kmap = {s.name: s for s in Sensors.fetch_all(sensors.values())}
        return {key: kmap[value] for key, value in sensors.items()}

    @classmethod
    def standard_sensor(
        cls, sensor_name: Union[str, SensorNames], generation: DataGeneration
    ) -> Sensors:
        if isinstance(sensor_name, SensorNames):
            sensor_name = sensor_name.json_name
        gens = {x["name"]: x for x in InternalTools.load_resource("core", "generations.json")}
        return Sensors.fetch(gens[generation.name]["sensors"][sensor_name])

    @classmethod
    def convert_sensor_data_from_bytes(
        cls, sensor: Union[str, int, Sensors], data: bytes
    ) -> Union[None, np.array, bytes, str, Image.Image]:
        """
        Convert the sensor data to its appropriate type as defined by ``sensors.data_type``.

        .. warning::
            Currently does not handle ``sensors.data_type=='utf8_char'``. Currently there are no sensors in Valar with this data type.

        .. note::
            This function will probably be deprecated soon, replaced by valarpy model methods

        Args:
            sensor: The name, ID, or instance of the sensors row
            data: The data from ``sensor_data.floats``; despite the name this is blob represented as bytes and may not correspond to floats at all

        Returns:
            The converted data, or None if ``data`` is None
        """
        sensor = Sensors.fetch(sensor)
        dt = sensor.data_type
        if data is None:
            return None
        # in case arithmetic is done on these
        # we'll use a bigger dtype than necessary
        # typically, longdouble is 64, 80, or 128 bits and longlong is just 64
        if dt == "byte":
            return np.frombuffer(data, dtype=np.byte).astype(np.int16)
        if dt == "unsigned_byte":
            return np.frombuffer(data, dtype=np.byte).astype(np.int16) + 2**7
        if dt == "short":
            return np.frombuffer(data, dtype=">i2").astype(np.int32)
        if dt == "unsigned_short":
            return np.frombuffer(data, dtype=">i2").astype(np.int32) + 2**15
        if dt == "int":
            return np.frombuffer(data, dtype=">i4").astype(np.int64)
        if dt == "unsigned_int":
            return np.frombuffer(data, dtype=">i4").astype(np.int64) + 2**31
        if dt == "long":
            return np.frombuffer(data, dtype=">i8").astype(np.longlong)
        if dt == "unsigned_long":
            return np.frombuffer(data, dtype=">i8").astype(np.ulonglong) + 2**63
        if dt == "float":
            return np.frombuffer(data, dtype=">f4").astype(np.float64)
        if dt == "double":
            return np.frombuffer(data, dtype=">f8").astype(np.longdouble)
        if dt == "unsigned_double":
            return np.frombuffer(data, dtype=">f8").astype(np.ulongdouble)
        if dt == "string:utf8":
            return str(data, encoding="utf-8")
        if dt == "string:utf16":
            return str(data, encoding="utf-16")
        if dt == "string:utf32":
            return str(data, encoding="utf-32")
        # elif dt.startswith("image:"):
        #    return Image.open(io.BytesIO(data))
        else:
            return data

    @classmethod
    def stimulus_display_colors(cls) -> Mapping[str, str]:
        """
        Returns a mapping from stimulus names to preferred colors.
        See :meth:`stimulus_display_color`.

        Returns:
            A mapping from stimulus names to 6-digit RGB hex codes prefixed by ``#``
        """
        return copy(_stimulus_display_colors)

    @classmethod
    def stimulus_display_color(cls, stim: Union[int, str, Stimuli]) -> str:
        """
        Gets the preferred color to display a stimulus with.

        Returns:
            A 6-digit RGB hex prefixed by ``#``
        """
        stim_name = stim if isinstance(stim, str) else Stimuli.fetch(stim).name
        return copy(_stimulus_display_colors[stim_name])

    @classmethod
    def sort_controls_first(
        cls, df: pd.DataFrame, column: str, more_controls: Optional[Set[str]] = None
    ) -> pd.DataFrame:
        first = ValarTools.controls_first(df[column], more_controls=more_controls)
        return ValarTools.sort_first(df, column, first)

    @classmethod
    def sort_first(
        cls, df: pd.DataFrame, column: Union[str, int, pd.Series], first: Sequence[str]
    ) -> pd.DataFrame:
        """
        Partially sorts the rows of a DataFrame by column ``column``, such that the items in ``first`` appear first.
        The rest of the rows keep the same sorting.
        """
        if isinstance(column, str) or isinstance(column, int):
            column = df[column]
        df = df.copy()
        first = [*first, *[k for k in column if k not in first]]
        df["__sort"] = column.map(lambda s: first.index(s))
        df = df.sort_values("__sort")
        df = df.drop("__sort", axis=1)
        return df

    @classmethod
    def controls_first(
        cls, names: Iterable[str], sorting=natsorted, more_controls: Optional[Set[str]] = None
    ) -> Sequence[str]:
        """
        Sorts a set of names, putting control types first.
        Controls are sorted by: positive/negative (+ first), then name.
        Both controls and their display values are included.
        After the controls, sorts the remainder by name.
        This can be very useful for plotting.
        """
        names = set(names)
        query = list(
            sorted(
                list(ControlTypes.select().order_by(ControlTypes.positive, ControlTypes.name)),
                key=lambda c: -c.positive,
            )
        )
        controls = list(Tools.unique(InternalTools.flatten([(c.name, c) for c in query])))
        if more_controls is not None:
            controls.extend(more_controls)
        new_names = [c for c in controls if c in names]
        new_names.extend(sorting([s for s in names if s not in controls]))
        return new_names

    @classmethod
    def stimulus_type(cls, stimulus: Union[str, int, Stimuli]) -> StimulusType:
        """
        Gets the type of stimulus from a stimulus row.

        Args:
            stimulus: Stimulus ID, name, or instance

        Returns:
            A :class:`StimulusType` enum value
        """
        stimulus = Stimuli.fetch(stimulus)
        if stimulus.audio_file_id is not None:
            return StimulusType.AUDIO
        elif "solenoid" in stimulus.name:
            return StimulusType.SOLENOID
        elif "LED" in stimulus.name:
            return StimulusType.LED
        elif stimulus.name == "none":
            return StimulusType.NONE
        elif stimulus.name == "IR array":
            return StimulusType.IR
        assert False, f"No type for stimulus {stimulus.name} found!"

    @classmethod
    def toml_file(cls, run: RunLike) -> NestedDotDict:
        """
        Get the SauronX TOML config file for a run.
        Is guaranteed to exist for SauronX data, but won't for legacy.

        Args:
            run: A run ID, name, tag, instance, or submission instance or hash

        Returns:
            The wrapped text of the config file
        """
        run = Tools.run(run)
        if run.submission is None:
            raise SauronxOnlyError(f"No config files are stored for legacy data (run r{run.id})")
        t = ConfigFiles.fetch(run.config_file)
        return NestedDotDict(t.toml_text)

    @classmethod
    def treatment_sec(cls, run: RunLike) -> float:
        """
        Total time between dosing and the start of the run.

        Returns:
            The duration in seconds as a float, or ``np.inf`` if something is missing
        """
        run = Runs.fetch(run)
        if run.datetime_dosed is None or run.datetime_run is None:
            return np.inf
        return (run.datetime_run - run.datetime_dosed).total_seconds()

    @classmethod
    def acclimation_sec(cls, run: RunLike) -> float:
        """
        Total acclimation time, the duration between the start of the run and the start of the acquisition.
        (This duration is set on the submission and handled directly by SauronX.)

        Returns:
            The duration in seconds as a float, or ``np.inf`` if something is missing
        """
        # here just for consistency
        run = Tools.run(run)
        if run.acclimation_sec is None:
            return np.inf
        return run.acclimation_sec

    @classmethod
    def wait_sec(cls, run: RunLike) -> float:
        """
        Time between plating and either running or plating.
        The rule is:
            - If dose time < plate time: wait_sec is negative
            - If not dosed: wait_sec = run time - plate time

        Returns:
            the duration in seconds as a float, or ``np.inf`` if something is missing
        """
        run = Tools.run(run)
        plate = Plates.fetch(run.plate)  # type: Plates
        if run.plate.datetime_plated is None:
            return np.inf
        if run.datetime_dosed is None:
            return (run.datetime_run - plate.datetime_plated).total_seconds()
        else:
            return (run.datetime_dosed - plate.datetime_plated).total_seconds()

    @classmethod
    def known_solvent_names(cls) -> Mapping[int, str]:
        """
        Note that this map is manually defined and is not guaranteed to reflect newly-used solvents.
        Currently covers DMSO, water, ethanol, methanol, M-Propyl, DMA, and plutonium (used for testing).

        Returns:
            A mapping from compound IDs to names
        """
        data = InternalTools.load_resource("core", "solvents.json")
        return {int(k): v for k, v in data.items()}

    @classmethod
    def controls_matching_all(
        cls,
        names: Union[None, ControlTypes, str, int, Iterable[Union[ControlTypes, int, str]]] = None,
        **attributes,
    ) -> Set[ControlTypes]:
        """
        Return the control types matching ALL the specified criteria.

        Args:
            names: The set of allowed control_types
            attributes: Any key-value pairs mapping an attribute of ControlTypes to a required value
            names: TODO
            attributes: TODO
        """
        if names is not None and not Tools.is_true_iterable(names):
            names = [names]
        allowed_controls = (
            list(ControlTypes.select())
            if names is None
            else ControlTypes.fetch_all(InternalTools.listify(names))
        )
        return {
            c for c in allowed_controls if all([getattr(c, k) == v for k, v in attributes.items()])
        }

    @classmethod
    def controls_matching_any(
        cls,
        names: Union[None, ControlTypes, str, int, Iterable[Union[ControlTypes, int, str]]] = None,
        **attributes,
    ) -> Set[ControlTypes]:
        """
        Return the control types matching ANY of the specified criteria.

        Args:
            names: A set of control_types
            attributes: Any key-value pairs mapping an attribute of ControlTypes to a required value
            names: TODO
            **attributes: TODO
        """
        if names is None and len(attributes) == 0:
            by_name = list(ControlTypes.select())
        elif names is None:
            by_name = []
        elif Tools.is_true_iterable(names):
            by_name = ControlTypes.fetch_all(names)
        else:
            by_name = [ControlTypes.fetch(names)]
        by_other = {
            c
            for c in ControlTypes.select()
            if any([getattr(c, k) == v for k, v in attributes.items()])
        }
        return {*by_name, *by_other}

    @classmethod
    def generation_of(cls, run: RunLike) -> DataGeneration:
        """
        Determines the "data generation" of the run, specific to Kokel Lab data. See ``DataGeneration`` for more details.

        Args:
            run: A runs instance, ID, name, tag, or submission hash or instance

        Returns:
            A DataGeneration instance
        """
        run = Runs.fetch(run)
        sauronx = run.submission_id is not None
        generations: Sequence[Dict[str, Any]] = InternalTools.load_resource(
            "core", "generations.json"
        )
        # noinspection PyChainedComparisons
        matches = {
            x["name"]
            for x in generations
            if sauronx == x["has_submission"]
            and (
                x["start_date"] == ""
                or run.datetime_run >= datetime.strptime(x["start_date"], "%Y-%m-%d")
            )
            and (
                x["end_date"] == ""
                or run.datetime_run <= datetime.strptime(x["end_date"], "%Y-%m-%d")
            )
            and run.sauron_config.sauron.name in x["saurons"]
        }
        if len(matches) > 1:
            raise MultipleMatchesError(
                f"Run {run.id} ({run.datetime_run}) with{'' if sauronx else 'out'} submission matches {matches}"
            )
        match = Tools.only(matches)
        return DataGeneration.of(match)

    @classmethod
    def features_on(cls, run: RunLike) -> Set[str]:
        """
        Finds all unique features involved in all the wells for a given run.

        Args:
            run: A run ID, name, tag, instance, or submission hash or instance

        Returns:
            The set of features involved in a given run
        """
        run = Runs.fetch(run)
        pt = run.plate.plate_type
        n_wells = pt.n_rows * pt.n_columns
        features = set()
        for feature in Features.select():
            got = len(
                WellFeatures.select(
                    WellFeatures.id, WellFeatures.type_id, WellFeatures.well, Wells.id, Wells.run_id
                )
                .join(Wells)
                .where(Wells.run_id == run)
                .where(WellFeatures.type_id == feature.id)
            )
            if got == n_wells:
                features.add(feature.name)
            assert got == 0 or got == n_wells, f"{got} != {n_wells}"
        return features

    @classmethod
    def sensors_on(cls, run: RunLike) -> Set[Sensors]:
        """
        Finds all unique sensor names that have sensor data for a given run.

        Args:
            run: A run ID, name, tag, instance, or submission hash or instance

        Returns:
            The set of sensor names that have sensor data for a given run
        """
        run = Runs.fetch(run)
        return {
            sd.sensor
            for sd in SensorData.select(SensorData.sensor, SensorData.run, SensorData.id, Runs.id)
            .join(Runs)
            .switch(SensorData)
            .join(Sensors)
            .where(Runs.id == run.id)
        }

    @classmethod
    def looks_like_submission_hash(cls, submission_hash: str) -> bool:
        """
        TODO.

        Args:
            submission_hash: Any string

        Returns:
            Whether the string could be a submission hash (is formatted correctly)
        """
        return InternalTools.looks_like_submission_hash(submission_hash)

    @classmethod
    def battery_is_legacy(cls, battery: Union[Batteries, str, int]) -> bool:
        """
        TODO.

        Args:
            battery: The battery ID, name, or instance

        Returns:
            Whether the battery is a _true_ legacy battery; i.e. can't be run with SauronX

        """
        battery = Batteries.fetch(battery)
        return battery.name.startswith("legacy-")

    @classmethod
    def assay_is_legacy(cls, assay: Union[Assays, str, int]) -> bool:
        """
        TODO.

        Args:
            assay: The assay ID, name, or instance

        Returns:
            Whether the assay is a _true_ legacy battery; i.e. can't be run with SauronX

        """
        assay = Assays.fetch(assay)
        return assay.name.startswith("legacy-")

    @classmethod
    def assay_is_background(cls, assay: Union[Assays, str, int]) -> bool:
        """
        TODO.

        Args:
            assay: The assay ID, name, or instance

        Returns:
            Whether the assay contains real stimuli; the query is relatively fast

        """
        assay = Assays.fetch(assay)
        stimuli_id = {
            s.stimulus for s in StimulusFrames.select().where(StimulusFrames.assay_id == assay.id)
        }
        stimuli_names = {Stimuli.fetch(s_id).name for s_id in stimuli_id}
        return len(stimuli_names) == 0 or stimuli_names == {"none"}  # stimulus 'none'

    @classmethod
    def sauron_name(cls, sauron: Union[Saurons, int, str]) -> str:
        """
        Returns a display name for a Sauron. Currently this just means prepending a 'S' when necessary.
        Does not perform a fetch. Instead, uses a prefetched map of names.

        Args:
            sauron: A Sauron instance, ID, or name
        """
        sauron = Saurons.fetch(sauron)
        if regex.compile(r"[0-9]+", flags=regex.V1).fullmatch(sauron.name) is None:
            return sauron.name
        else:
            return "S" + sauron.name

    @classmethod
    def sauron_config_name(cls, sauron_config: Union[str, int, SauronConfigs]) -> str:
        if isinstance(sauron_config, str) and sauron_config.isdigit():
            sauron_config = int(sauron_config)
        sc = SauronConfigs.fetch(sauron_config)
        return str(sc.sauron.name) + "." + str(sc.id) + ":" + sc.created.strftime("%Y%m%d")

    @classmethod
    def sauron_config(cls, config: SauronConfigLike) -> SauronConfigs:
        """
        Fetches a sauron_configs row.
        Will accept a sauron_config or its ID, or a tuple of (sauron ID/instance/name, datetime modified).
        """
        if isinstance(config, (int, SauronConfigs)):
            return SauronConfigs.fetch(config)
        if (
            isinstance(config, tuple)
            and len(config) == 2
            and isinstance(config[0], SauronLike)
            and isinstance(config[1], datetime)
        ):
            sauron = Saurons.fetch(config[0])
            c = (
                SauronConfigs.select()
                .where(SauronConfigs.sauron == sauron)
                .where(SauronConfigs.datetime_changed == config[1])
            )
            if c is None:
                raise ValarLookupError(f"No sauron_config for sauron {sauron.name} at {config[1]}")
            else:
                return c

    @classmethod
    def hardware_setting(cls, config: SauronConfigLike, key: str) -> Union[str]:
        config = ValarTools.sauron_config(config)
        setting = (
            SauronSettings.select(SauronSettings, SauronConfigs)
            .join(SauronConfigs)
            .where(SauronConfigs.id == config.id)
            .where(SauronSettings.name == key)
            .first()
        )
        return None if setting is None else setting.value

    @classmethod
    def hardware_settings(cls, config: SauronConfigLike) -> Mapping[str, str]:
        config = ValarTools.sauron_config(config)
        return {
            s.name: s.value
            for s in SauronSettings.select(SauronSettings, SauronConfigs)
            .join(SauronConfigs)
            .where(SauronConfigs.id == config.id)
        }

    @classmethod
    def run_tag(cls, run: RunLike, tag_name: str) -> str:
        """
        Returns a tag value from run_tags or raises a ValarLookupError.

        Args:
            run: A run ID, name, tag, submission hash, submission instance or run instance
            tag_name: The value in run_tags.name

        Returns:
            The value as an str
        """
        run = Runs.fetch(run)
        t = RunTags.select().where(RunTags.run_id == run.id).where(RunTags.name == tag_name).first()
        if t is None:
            raise ValarLookupError(f"No run_tags row for name {tag_name} on run {run.name}")
        return t.value

    @classmethod
    def run_tag_optional(cls, run: RunLike, tag_name: str) -> Optional[str]:
        """
        Returns a tag value from run_tags.

        Args:
            run: A run ID, name, tag, submission hash, submission instance or run instance
            tag_name: The value in run_tags.name

        Returns:
            The value as a str, or None if it doesn't exist
        """
        run = Runs.fetch(run)
        t = RunTags.select().where(RunTags.run_id == run.id).where(RunTags.name == tag_name).first()
        return None if t is None else t.value

    @classmethod
    def stimulus_display_name(cls, stimulus: Union[int, str, Stimuli]) -> str:
        """
        Gets a publication-ready name for a stimulus.
        For example:
            - 'violet (400nm)' instead of 'purple LED'
            - 'alarm' instead of 'MP3'
            - '4-peak 50Hz sine' instead of '4-peak_50hz_s'
            - 'whoosh' instead of 'fs_12'

        Args:
            stimulus: A stimulus ID, name, or instance

        Returns:
            The name as a string
        """
        stimulus = stimulus if isinstance(stimulus, str) else Stimuli.fetch(stimulus)
        return _stimulus_replace[stimulus]

    @classmethod
    def datetime_capture_finished(cls, run) -> datetime:
        """
        Only works for SauronX runs.-
        """
        run = Tools.run(run)
        if run.submission is not None:
            raise SauronxOnlyError(
                "Can't get datetime_capture_finished for a legacy run: It wasn't recorded."
            )
        return datetime.strptime(
            ValarTools.run_tag(run, "datetime_capture_finished"), "%Y-%m-%dT%H:%M:%S.%f"
        )

    @classmethod
    def frames_of_ms(cls, ms: np.array, fps: int) -> np.array:
        """
        Obscure.

        Args:
            ms: The array of millisecond values
            fps: The frames per second

        Returns:
            The unique frame seconds, unique, in order
        """
        return np.unique([int(np.round(x * fps / 1000)) for x in ms])

    @classmethod
    def fetch_toml(cls, run: Union[int, str, Runs, Submissions]) -> NestedDotDict:
        """
        Parse NestedDotDict from config_files.
        """
        run = Runs.fetch(run)
        sxt = ConfigFiles.fetch(run.config_file_id)
        return NestedDotDict.parse_toml(sxt.toml_text)

    @classmethod
    def parse_toml(cls, sxt: Union[ConfigFiles, Runs]) -> NestedDotDict:
        """
        Parse NestedDotDict from config_files.
        """
        if isinstance(sxt, Runs):
            sxt = ConfigFiles.fetch(sxt.config_file_id)
        return NestedDotDict.parse_toml(sxt.toml_text)

    @classmethod
    def initials(cls, user: Union[Users, int, str]) -> str:
        """
        Returns the initials of a user.
        For example, 'matt' will be 'MMC', and 'douglas' will be 'DMT'.

        Args:
            user: The name, ID, or instance in the users table

        Returns:
            The initials as a string, in caps
        """
        if isinstance(user, int):
            user = Users.select().where(Users.id == user).first()
        if isinstance(user, str):
            user = Users.select().where(Users.username == user).first()
        if user.first_name.islower():
            user.first_name = user.first_name.capitalize()
        if user.last_name.islower():
            user.last_name = user.last_name.capitalize()
        return "".join([c for c in user.first_name + " " + user.last_name if c.isupper()])

    @classmethod
    def expected_n_frames(cls, run: Union[int, str, Runs, Submissions]) -> int:
        """
        Calculate the number of frames expected for the ideal (configured) framerate of the run.
        Calls

        Args:
            run: A run ID, name, tag, instance, or submission hash or instance

        Returns:
            ValarTools.frames_per_second.
        """
        run = Runs.fetch(run)
        run = (
            Runs.select(
                Runs, Experiments.id, Experiments.battery_id, Batteries.id, Batteries.length
            )
            .join(Experiments)
            .join(Batteries)
            .where(Runs.id == run)
            .first()
        )
        battery = run.experiment.battery
        return (
            ValarTools.frames_per_second(run)
            * battery.length
            / (cls.LEGACY_FRAMERATE if run.submission is None else 1000)
        )

    @classmethod
    def fps_of_sauron_config(cls, sauron_config: Union[SauronConfigs, int]) -> Optional[int]:
        fps = (
            SauronSettings.select()
            .where(SauronSettings.sauron_config == sauron_config)
            .where(SauronSettings.name == "fps")
            .first()
        )
        return None if fps is None else Tools.only(fps, name="framerates").value

    @classmethod
    def sauron_configs_with_fps(
        cls, sauron: Union[Saurons, int, str], fps: int
    ) -> Sequence[SauronConfigs]:
        return ValarTools.sauron_configs_with_setting(sauron, "fps", fps)

    @classmethod
    def sauron_configs_with_setting(
        cls, sauron: Union[Saurons, int, str], name: str, value: Any
    ) -> Sequence[SauronConfigs]:
        query = (
            SauronSettings.select(SauronSettings, SauronConfigs)
            .join(SauronConfigs)
            .where(SauronSettings.name == name)
            .where(SauronSettings.value == str(value))
        )
        if sauron is not None:
            query = query.where(SauronConfigs.sauron == sauron)
        query = query.order_by(SauronConfigs.created)
        return Tools.unique([setting.sauron_config for setting in query])

    @classmethod
    def toml_data(cls, run: RunLike) -> NestedDotDict:
        run = Runs.fetch(run)
        t = ConfigFiles.fetch(run.config_file_id)
        return NestedDotDict.parse_toml(t.toml_text)

    @classmethod
    def toml_item(cls, run: RunLike, item: str) -> Any:
        return cls.toml_data(run)[item]

    @classmethod
    def frames_per_second(cls, run: RunLike) -> int:
        """
        Determines the main camera framerate used in a run.

        .. note::
            This is the IDEAL framerate: The one that was configured.
            To get the emperical framerate for PointGrey data, download the timestamps.
            (The empirical framerate is unknown for pre-PointGrey data.)

        For legacy data, always returns 25. Note that for some MGH data it might actually be a little slower or faster.
        For SauronX data, fetches the TOML data from Valar and looks up sauron.hardware.camera.frames_per_second .

        Args:
          run: A run ID, name, tag, instance, or submission hash or instance

        Returns:
          A Python int
        """
        run = Tools.run(run)
        if run.submission is None:
            return 25
        t = ConfigFiles.fetch(run.config_file_id)
        toml = NestedDotDict.parse_toml(t.toml_text)
        return toml.exactly("sauron.hardware.camera.frames_per_second", int)

    @classmethod
    def battery_stimframes_per_second(cls, battery: Union[int, str, Batteries]) -> int:
        return cls.LEGACY_FRAMERATE if ValarTools.battery_is_legacy(battery) else 1000

    @classmethod
    def assay_ms_per_stimframe(cls, assay: Union[int, str, Assays]) -> int:
        return 1000 / 25 if ValarTools.assay_is_legacy(assay) else 1

    @classmethod
    def frames_per_stimframe(cls, run: Union[int, str, Runs, Submissions]) -> float:
        """
        Returns the number of frames

        Args:
            run: A run ID, name, tag, instance, or submission hash or instance
        """
        run = Runs.fetch(run)
        if run.submission is None:
            return 1
        else:
            return cls.frames_per_second(run) / 1000

    @classmethod
    def runs(
        cls, runs: Union[int, str, Runs, Submissions, Iterable[Union[int, str, Runs, Submissions]]]
    ) -> Sequence[Runs]:
        """
        Fetches an iterable of runs from an iterable of ID(s), tag(s), name(s),
        or submission hash(es).

        Args:
            runs: An iterable consisting of run ID(s), name(s), tag(s), instance(s), or submission hash(es) or instance(s)

        Returns:
            An iterable consisting of runs associated with given run identifiers.
        """
        return Tools.runs(runs)

    @classmethod
    def run(cls, run: Union[int, str, Runs, Submissions]) -> Runs:
        """
        Fetches a run from an ID, tag, name, or submission hash.

        Args:
          run: A run ID, name, tag, instance, or submission hash or instance

        Returns:
          A run associated with the given ID, name, tag, instance, or submission hash or instance
        """
        return Tools.run(run)

    @classmethod
    def simplify_assay_name(cls, assay: Union[Assays, int, str]) -> str:
        """
        See ``ValarTools.assay_name_simplifier``, which is faster for many assay names.
        """
        name = assay if isinstance(assay, str) else Assays.fetch(assay).name
        return ValarTools._assay_name_simplifier()(name)

    @classmethod
    def _assay_name_simplifier(cls) -> Callable[[str], str]:
        """
        Strips out the legacy assay qualifiers like ``(variant:...)`` and the user/experiment info.
        Also removes text like '#legacy' and 'sauronx-', and 'sys :: light ::'.

        Returns:
            A function mapping assay names to new names
        """
        _usernames = {u.username for u in Users.select(Users.username)}
        _qualifier = regex.compile("-\\(variant:.*\\)", flags=regex.V1)
        _end = regex.compile(
            "-(?:" + "|".join(_usernames) + ")" + """-[0-9]{4}-[0-9]{2}-[0-9]{2}-0x[0-9a-h]{4}$""",
            flags=regex.V1,
        )

        def _simplify_name(name: str) -> str:
            prefixes = dict(InternalTools.load_resource("core", "assay_prefixes.json"))
            s = _qualifier.sub("", _end.sub("", name))
            for k, v in prefixes.items():
                s = s.replace(k, v)
            return s

        return _simplify_name

    @classmethod
    def trash_controls(cls) -> FrozenSet[ControlTypes]:
        return _trash_controls

    @classmethod
    def hazardous_controls(cls) -> FrozenSet[ControlTypes]:
        return _problematic_controls


__all__ = ["ValarTools", "StimulusType"]

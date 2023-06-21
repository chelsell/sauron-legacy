import datetime
import getpass
import logging
import os
import platform
import socket
import sys
from typing import Dict, List
from warnings import warn
from pocketutils.core.exceptions import MissingEnvVarError, FileDoesNotExistError, PathError, ConfigError
from pocketutils.tools.path_tools import PathTools
from pocketutils.core.dot_dict import NestedDotDict
from .utils import pexists, pfile, pjoin, warn_user, make_dirs, git_commit_hash

import psutil
import toml

from .utils import (
    datetime_started_raw,
    iso_timestamp_started,
    plain_timestamp_started_with_millis,
    sauronx_version,
    stamp,
)

from .paths import SubmissionPathCollection

if "SAURONX_CONFIG_PATH" not in os.environ:
    raise MissingEnvVarError(
        "Environment variable $SAURONX_CONFIG_PATH is not set; set this to the correct config.toml file"
    )
config_file_path = PathTools.sanitize_path(os.environ["SAURONX_CONFIG_PATH"])
if not pexists(config_file_path):
    raise FileDoesNotExistError("SAURONX_CONFIG_PATH file {} does not exist".format(config_file_path))
if not pfile(config_file_path):
    raise PathError(
        "SAURONX_CONFIG_PATH file {} is not a file".format(config_file_path)
    )
# TODO require this to be inside sauronx/config
sauronx_home = os.environ["SAURONX_HOME"]


class FrameRoi:
    def __init__(self, x0: int, y0: int, x1: int, y1: int) -> None:
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1

    def __str__(self) -> str:
        return "({},{})→({},{})".format(self.x0, self.y0, self.x1, self.y1)


class WellRoi:
    def __init__(self, row: int, column: int, x0: int, y0: int, x1: int, y1: int) -> None:
        self.row_index = row
        self.column_index = column
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1

    def __str__(self) -> str:
        return "{},{}  = ({},{})→({},{})".format(
            self.row_index, self.column_index, self.x0, self.y0, self.x1, self.y1
        )


class Config(NestedDotDict):
    def __init__(self, spec_config_file_path: str = config_file_path) -> None:
        """Reads the TOMLs, sets some extra variables, and fetches OS info and software versions."""

        # as a TomlData subclass, has [], get, and get.as_getter
        logging.info("Loading config file {} ...".format(spec_config_file_path))
        super().__init__(self._get_data(spec_config_file_path))
        self.path = spec_config_file_path

        for r in self.keys():
            if "." in r:
                raise ConfigError("key {} contains a period (.)".format(r))

        # set logging level
        logging.getLogger().setLevel(logging.getLevelName(self["local.feedback.log_level"]))

        # environment properties
        self.toml_name = self["toml_name"]
        # TODO
        self.sauron_id = self["sauron"]["id"]
        self.sauron_number = self["sauron"]["number"]
        self.sauron_name = self["sauron"]["name"]
        self.environment_info = None  # type: Dict[str, str]
        logging.debug("Collecting environment info...")
        self._set_environment_vars()
        logging.debug("Collected environment info.")

        # sub-getters
        self.camera = self.sub("sauron.hardware.camera")
        self.arduino = self.sub("sauron.hardware.arduino.ports")
        self.stimuli = self.sub("sauron.hardware.stimuli")
        self.sensors = self.sub("sauron.hardware.sensors")
        self.webcam = self.sub("sauron.hardware.webcam")
        self.storage = self.sub("local.storage")
        self.executables = self.sub("local.executables")
        self.audio = self.sub("sauron.hardware.stimuli.audio")

        if "%" in self.storage["directory_format"].name:
            raise ConfigError(
                "For technical limitations (regarding ffmpeg), local storage paths cannot contain a percent sign (%)"
            )

        # logging.info("Started on {}".format(self.timestamp_with_offset()))
        logging.info("Loaded config file {}".format(spec_config_file_path))

        assert self["sauron.data.audio.flac_compression_level"] is not None

    @property
    def fps(self):
        return self.camera["frames_per_second"]

    def list_plate_types(self) -> List[str]:
        import valarpy.model as model

        infos = self["sauron.roi"]
        return [
            model.PlateTypes.select().where(model.PlateTypes.id == pt).first().name
            for pt in infos.keys()
        ]

    def get_sauron_config(self):
        import valarpy.model as model

        return (
            model.SauronConfigs.select(model.SauronConfigs, model.Saurons)
            .join(model.Saurons)
            .where(model.Saurons.id == config.sauron_name)
            .order_by(model.SauronConfigs.datetime_changed.desc())
            .first()
        )

    def timestamp_with_offset(self) -> str:
        """What's used in last_modification_timestamp"""
        return datetime_started_raw.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + self.get_str(
            "local.timezone.utc_offset_string"
        )

    def _get_data(self, config_file: str) -> dict:
        with open(config_file) as config_handle:
            try:
                data = toml.loads(config_handle.read())
            except toml.TomlDecodeError as e:
                raise ConfigError("Could not parse SauronX config file.", e)
            data["local"]["storage"]["directory_format"] = PathTools.sanitize_path(
                data["local"]["storage"]["directory_format"]
            )
        return data

    def temp_dir(self) -> str:
        if not pexists(self.storage["root_temp_dir"]):
            warn(
                "Root temp directory {} does not exist; will be created".format(
                    self.storage["root_temp_dir"]
                )
            )
            make_dirs(self.storage["root_temp_dir"])
        return PathTools.sanitize_path(
            pjoin(
                self._parse_dir_format(self.storage["root_temp_dir"]),
                "sauronx.tmp-" + plain_timestamp_started_with_millis,
            )
        )

    def trash_dir(self) -> str:
        if not pexists(self.storage["root_trash_dir"]):
            warn(
                "Root trash directory {} does not exist; will be created".format(
                    self.storage["root_trash_dir"]
                )
            )
        return self._parse_dir_format(self.storage["root_trash_dir"])

    def trash_path(self, path_to_delete: str) -> str:
        trash_path = pjoin(self.trash_dir(), os.path.basename(path_to_delete))
        if pexists(trash_path):
            return trash_path + "-" + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")
        else:
            return trash_path

    def _set_environment_vars(self) -> None:
        # note that datetime_command_entered is NOT the time runs.datetime_run gets set to; that's handled in submission.py
        # TODO: Calling cpuinfo causes a new instance of SauronX to start!!!
        # 'cpu': cpuinfo.get_cpu_info()['brand']
        self.environment_info = {
            "sauronx_version": sauronx_version,
            "datetime_command_entered": iso_timestamp_started,
            "sauron": self.sauron_name,
            "os_release": platform.platform(),
            "hostname": socket.gethostname(),
            "username": getpass.getuser(),
            "python_version": sys.version,
            "shell": os.environ["SHELL"],
            "disk_used": psutil.disk_usage(".").used,
            "disk_free": psutil.disk_usage(".").free,
            "memory_used": psutil.virtual_memory().used,
            "memory_available": psutil.virtual_memory().available,
            "sauronx_hash": git_commit_hash(sauronx_home),
            "environment_info_capture_datetime": datetime.datetime.now().isoformat(),
        }
        self.environment_info = {k: str(v) for k, v in self.environment_info.items()}

    def camera_roi(self, plate_type_id: int) -> FrameRoi:
        roi = self["sauron.hardware.camera.plate.{}.roi".format(plate_type_id)]
        return FrameRoi(roi[0], roi[1], roi[2], roi[3])

    def get_roi_coordinates(self, plate_type_id: int) -> List[WellRoi]:

        info = self["sauron.roi." + str(plate_type_id)]

        # noinspection PyTypeChecker
        n_rows, n_columns = int(info["n_rows"]), int(info["n_columns"])
        # noinspection PyTypeChecker
        x0, y0, x1, y1 = int(info["x0"]), int(info["y0"]), int(info["x1"]), int(info["y1"])
        # noinspection PyTypeChecker
        padx, pady = int(info["padx"]), int(info["pady"])
        width = x1 - x0
        height = y1 - y0

        # make sure the wells don't extend outside the image bounds
        bounds = [float(b) for b in self.camera["plate.{}.roi".format(plate_type_id)]]
        bx0, by0, bx1, by1 = bounds  # ex: "335 119 1175 791"
        if bx0 < 0 or by0 < 0:
            raise ValueError("sauron camera roi has a negative bound {} !".format(bounds))
        # if bx1 < bx0 or by1 < by0: raise ValueError("sauron camera roi is wrong {} !".format(bounds))  # TODO
        wells_x_edge = x0 + n_columns * width + (n_columns - 1) * padx
        if wells_x_edge > bx1:
            warn_user(
                "The rightmost well is out of bounds",
                "The wells extend horizontally to {}".format(round(wells_x_edge, 2)),
                "This is outside the bounds {}".format(bounds),
            )
        wells_y_edge = y0 + n_rows * height + (n_rows - 1) * pady
        if wells_y_edge > by1:
            warn_user(
                "The bottommost well is out of bounds",
                "The wells extend vertically to {}".format(round(wells_y_edge, 2)),
                "This is outside the bounds {}".format(bounds),
            )

        rois = []
        x = info["x0"]
        y = info["y0"]
        for row in range(0, n_rows):
            for column in range(0, n_columns):
                rois.append(WellRoi(row, column, x, y, x + width, y + height))
                x += width + padx
            y += height + pady
            x = info["x0"]

        return rois

    @property
    def raw_frames_disk(self) -> str:
        return self.raw_frames_root.split(os.sep)[0]

    @property
    def output_dir_root(self) -> str:
        return self._parse_dir_format(self.storage["directory_format"])

    @property
    def raw_frames_root(self) -> str:
        return self._parse_dir_format(self.storage["raw_frames_output_dir_format"])

    def get_coll(self, s: str) -> SubmissionPathCollection:
        submission_hash = os.path.basename(s)
        return SubmissionPathCollection(
            self.get_output_dir(submission_hash),
            self.get_raw_frames_dir(submission_hash),
            submission_hash,
        )

    def get_output_dir(self, submission_hash: str) -> str:
        return pjoin(self.output_dir_root, submission_hash)

    def get_raw_frames_dir(self, submission_hash: str) -> str:
        return pjoin(self.raw_frames_root, submission_hash)

    def get_incubation_dir(self) -> str:
        return pjoin(self.output_dir_root, "incubation-" + str(plain_timestamp_started_with_millis))

    def get_prototyping_dir(self) -> str:
        return pjoin(
            self.output_dir_root, "prototyping-" + str(plain_timestamp_started_with_millis)
        )

    def parse_path_format(self, fmt: str, path: str, dt: datetime) -> str:
        return (
            PathTools.sanitize_path(fmt)
            .replace("${path}", path)
            .replace("${number}", str(self.sauron_number))
            .replace("${sauron}", str(self.sauron_name))
            .replace("${date}", dt.strftime("%Y-%m-%d"))
            .replace("${time}", dt.strftime("%H-%M-%S"))
            .replace("${datetime}", dt.strftime("%Y-%m-%d_%H-%M-%S"))
            .replace("${timestamp}", stamp(dt))
        )

    def _parse_dir_format(self, fmt: str) -> str:
        return (
            #str(PathTools.sanitize_path_nodes(fmt)) # this returns /t/m/p/sauronx.... rather than /tmp
            str(fmt)
            .replace("${number}", str(self.sauron_number))
            .replace("${sauron}", str(self.sauron_name))
        )


try:
    config = Config()  # type: Config
except ConfigError:
    warn_user("The config file is malformatted")
    raise
except Exception:
    warn_user("Unexpectedly failed to parse the config file")
    raise
# logging.info("Using log level {}".format(config['local.feedback.log_level']))
# logging.debug('Environment information: ' + str(config.environment_info))


def switch_config(path: str) -> None:
    global config_file_path
    global config
    config_file_path = pjoin(config_file_path, path)
    config = Config(path)
    logging.info("Switching config to {}".format(path))
    logging.info("Using log level {}".format(config["local.feedback.log_level"]))


def reload_config() -> None:
    global config
    config = Config()
    logging.info("Reloading config")
    logging.info("Using log level {}".format(config["local.feedback.log_level"]))


__all__ = ["config", "Config", "switch_config", "reload_config"]

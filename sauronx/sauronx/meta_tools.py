import datetime
import os
from subprocess import Popen
from typing import Iterable

from colorama import Fore, Style
from klgists.common import escape_for_properties
from klgists.misc.colored_notifications import header_to_user
from klgists.misc.commit_hash import git_commit_hash
from valarpy.Valar import Valar

from sauronx import pjoin, sauronx_version

from .alive import SauronxAlive
from .configuration import config, config_file_path
from .locks import *
from .paths import lock_file, sauronx_home


class MetaTools:
    def _bannered(self, *strings: Iterable[str]) -> None:
        print("-" * 120)
        for s in strings:
            print(s)
        print("-" * 120 + "\n")


class VersionTools(MetaTools):
    def update(self) -> None:
        with SauronxAlive(None) as alive:
            p = Popen(pjoin(sauronx_home, "bin", "update-sauronx"))
            p.wait()


class HardwareTools(MetaTools):
    def reset(self) -> None:
        from pymata_aio.pymata3 import PyMata3

        board = PyMata3()
        try:
            board.shutdown()
        except SystemExit:
            pass

    def update(self, text: str, when: datetime.datetime = datetime.datetime.now()) -> None:
        with Valar() as valar:
            import valarpy.model as model

            conf = model.SauronConfigs(
                datetime_changed=when,
                description=text,
                sauron=config.sauron_id,
                created=datetime.datetime.now(),
            )
            conf.save()
        print(Fore.BLUE + "Created new sauron_config {}".format(conf.id))


class InfoTools(MetaTools):
    def print_version(self) -> None:
        print(Style.BRIGHT + "Version: " + sauronx_version)
        print(Style.BRIGHT + "Hash:    " + git_commit_hash(sauronx_home))

    def print_status(self) -> None:
        """Prints information about running SauronX processes."""
        print("")
        print(Fore.MAGENTA + "Using {}".format(config_file_path))
        if SauronxLock().is_engaged():
            submission_hash = SauronxLock().submission_hash
            if submission_hash == "None":
                print(
                    Fore.MAGENTA
                    + "SauronX is locked, but is not running a submission. You cannot run submit, prototype, or preview.".format(
                        submission_hash
                    )
                )
            else:
                print(
                    Fore.MAGENTA
                    + "SauronX is locked with submission {}. You cannot run submit, prototype, or preview.".format(
                        submission_hash
                    )
                )
        else:
            print(Fore.MAGENTA + "SauronX is not locked.")
        print("")
        lst = ProcessingList.now()
        if len(lst) > 0:
            non = [str(s) for s in lst if s not in lst]
            if len(non) > 0:
                print(
                    Fore.MAGENTA
                    + "These submissions are being processed but not run: {}".format(", ".join(non))
                )

    def print_info(self, extended: bool = False) -> None:
        with Valar() as valar:
            print()
            self._bannered(
                Style.BRIGHT + "Version information...",
                "Version ".ljust(20, ".") + " " + sauronx_version,
                "Hash ".ljust(20, ".") + " " + git_commit_hash(sauronx_home),
            )
            obj = config.get_sauron_config()
            self._bannered(
                Style.BRIGHT + "Hardware config information...",
                "Date/time changed ".ljust(20, ".")
                + " "
                + "{}Z".format(
                    config.sauron_number, obj.datetime_changed.strftime("%Y-%m-%d_%H-%M-%S")
                ),
                "Description ".ljust(20, ".") + " " + obj.description,
            )
            self._bannered(
                Style.BRIGHT + "Video information...",
                "QP ".ljust(20, ".") + " " + str(config["sauron.data.video.qp"]),
                "Keyframe interval ".ljust(20, ".")
                + " "
                + str(config["sauron.data.video.keyframe_interval"]),
                "Preset ".ljust(20, ".") + " " + config.get_str("sauron.data.video.preset"),
                "Custom params ".ljust(20, ".")
                + " "
                + "; ".join(
                    [
                        str(k) + "=" + str(v)
                        for k, v in config["sauron.data.video.extra_x265_params"].items()
                    ]
                ),
            )
            self._bannered(
                Style.BRIGHT + "Hardware information...",
                "FPS ".ljust(20, ".")
                + " "
                + str(config["sauron.hardware.camera.frames_per_second"]),
                "Exposure ".ljust(20, ".") + " " + str(config["sauron.hardware.camera.exposure"]),
                "Gain ".ljust(20, ".") + " " + str(config["sauron.hardware.camera.gain"]),
                "Gamma ".ljust(20, ".") + " " + str(config["sauron.hardware.camera.gamma"]),
                "Black level ".ljust(20, ".")
                + " "
                + str(config["sauron.hardware.camera.black_level"]),
                "Pre-padding ".ljust(20, ".")
                + " "
                + str(config["sauron.hardware.camera.padding_before_milliseconds"]),
                "Post-padding ".ljust(20, ".")
                + " "
                + str(config["sauron.hardware.camera.padding_after_milliseconds"]),
                "Arduino chipset ".ljust(20, ".")
                + " "
                + config.get_str("sauron.hardware.arduino.chipset"),
                "Sample rate (ms) ".ljust(20, ".")
                + " "
                + str(config["sauron.hardware.sensors.sampling_interval_milliseconds"]),
                "Audio floor (dB) ".ljust(20, ".")
                + " "
                + str(config["sauron.hardware.stimuli.audio.audio_floor"]),
                "Registered sensors ".ljust(20, ".")
                + " "
                + "; ".join(config["sauron.hardware.sensors.registry"]),
            )
            self._bannered(
                Style.BRIGHT + "Sauronx config information...",
                "Sauron ".ljust(20, ".") + " " + str(config.sauron_name),
                "Raw frames dir ".ljust(20, ".") + " " + config.raw_frames_root,
                "Output dir ".ljust(20, ".") + " " + config.output_dir_root,
                "Trash dir ".ljust(20, ".") + " " + config.trash_dir(),
                "Temp dir ".ljust(20, ".") + " " + config.temp_dir(),
                "Incubation dir ".ljust(20, ".") + " " + config.get_incubation_dir(),
                "Prototyping dir ".ljust(20, ".") + " " + config.get_prototyping_dir(),
                "Plate types ".ljust(20, ".") + " " + "; ".join(config.list_plate_types()),
            )
            if extended:
                self._bannered(
                    Style.BRIGHT + "Environment information...",
                    *[
                        ((key + " ").ljust(40, ".") + " " + escape_for_properties(value))
                        for key, value in config.environment_info.items()
                    ],
                )


class LockTools(MetaTools):
    def lock(self) -> None:
        if not SauronxLock().is_engaged():
            SauronxLock().engage_forced()
            print(
                Style.BRIGHT
                + "Created {} to forcibly lock SauronX. Run 'sauronx unlock' when done.".format(
                    lock_file
                )
            )
        else:
            print(Fore.RED + "Refusing: SauronX is already locked.")

    def unlock(self) -> None:
        if SauronxLock().is_engaged():
            SauronxLock().disengage()
            print(Style.BRIGHT + "Deleted {} to forcibly disengage the lock.".format(lock_file))
        else:
            print(Style.BRIGHT + "The SauronX lock is not engaged.")

    def clear(self, hashes, force) -> None:
        if hashes is None:
            hashes = []
        submissions = ProcessingList.now()
        if len(submissions) == 0:
            print(Style.BRIGHT + "The processing list is empty.")
        else:
            for submission in submissions:
                if len(hashes) == 0 or submission in hashes:
                    os.remove(submission.file)
                    print(Style.BRIGHT + "Removed {} from the processing list.".format(submission))


__all__ = ["VersionTools", "HardwareTools", "InfoTools", "LockTools"]

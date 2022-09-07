#!/usr/bin/env python3

import argparse
import logging
import os
import sys
from typing import Optional
from urllib.request import urlopen

from colorama import Fore, Style
from pint import UnitRegistry
from valarpy.Valar import Valar

from sauronx import looks_like_submission_hash, sauronx_version

from .configuration import config
from .data_manager import DataManager, DisplayOptions, SearchRestrictions
from .locks import SauronxLock
from .lookup import *
from .meta_tools import *
from .run_modes import *


class Main:
    def __init__(self):

        parser = argparse.ArgumentParser(
            description="SauronX interface",
            usage="""sauronx <subcommand> [<args>]
    Submission subcommands:
        submit       Submit a job to SauronX
        continue     Continue an incomplete SauronX run
    Special submission commands:
        incubate     Incubate a plate with SauronX locked (notifies Goldberry when done)
        prototype    Run Arduino commands interactively
    Preview subcommands:
        preview      Show a live feed from the camera with overlaid ROI
        snapshot     Capture a single frame and overlay the ROI
        webcam       Show a snapshot from the webcam
    Test commands:
        test         Run a test battery
        check        Run hardware checks
        calibrate    Calibrate a sensor
    Data/cleanup subcommands:
        data         Show the local output data with history/status info
        clean        Same as 'data', but prompt to delete each directory
        ls           Simply list the local output dirs
        obliterate   Destroy all raw frames
    Lookup/status subcommands:
        lookup       List something from Valar
        identify     Identify a submission and show its history
        log          See SauronX run history for this Sauron
        status       Return info about running SauronX jobs
        version      Just show the SauronX version
        info         Show extended info about SauronX, including config
    Other subcommands:
        modify       Record changes to SauronX hardware or camera settings
        update       Update the SauronX codebase to the latest stable release
        unlock       Forcibly unlocks SauronX
        clear        Forcibly removes items from the list of submissions being processed
        reset        Send a reset command to Arudino and then shutdown
        """,
        )
        args = ["proceed" if s == "continue" else s for s in sys.argv]
        if os.path.exists(config.temp_dir()):
            logging.warning(
                "Temporary directory {} already exists. Either this was left behind, or (far worse) another process is using it.".format(
                    config.temp_dir()
                )
            )
        try:
            ax = ["sauronx", *["'" + a + "'" if " " in a else a for a in args[1:]]]
            logging.info("Running command: {}".format(" ".join(ax)))
            SubcommandHandler(
                parser,
                target=self,
                temp_dir=config.temp_dir(),
                error_handler=lambda e: warn_user(
                    "SauronX failed. Refer to the error messages for more details."
                ),
            ).run(args)
        except:
            logging.fatal("SauronX failed.")
        finally:
            sys.stdout = open(os.devnull, "w")
            logging.info("Exiting SauronX.\n\n")

    def reset(self) -> None:
        parser = argparse.ArgumentParser(
            description="Connect to the Arduino board and shut down. Resets the connection."
        )
        parser.add_argument(
            "--force", action="store_true", help="Reset even if lock is engaged. Also unlocks."
        )
        parser.add_argument("--unlock", action="store_true", help="Unlocks.")
        args = self._parse_args(parser)
        if args.unlock:
            print(Style.BRIGHT + "Forcibly unlocking.")
            LockTools().unlock()
        elif SauronxLock().is_engaged() or args.force:
            warn_user("Refusing to reset: Lock is engaged. Run with --force if needed.")
            return
        print(Style.BRIGHT + "Forcibly resetting Arduino board.")
        HardwareTools().reset()
        success_to_user("Reset Arduino board.")

    def submit(self) -> None:
        parser = argparse.ArgumentParser(description="Submit a job to SauronX")
        parser.add_argument(
            "--halt", action="store_true", help=argparse.SUPPRESS
        )  # , help='Don\'t handle compression and upload: we\'ll run \'sauronx continue\' right after.'
        parser.add_argument(
            "hashes",
            type=self._submission_hash_it,
            nargs="+",
            help="A list of SauronX submission hashes, which are 12-digit lowercase hexadecimal numbers from valinor.ucsf.edu",
        )
        parser.add_argument(
            "--dark",
            type=self._to_sec,
            help="Override the dark acclimation. This change will not be reflected in Valar.",
        )
        parser.add_argument("--local", action="store_true", help="Don’t upload to Valinor.")
        parser.add_argument(
            "--assume-clean",
            action="store_true",
            help="Ignore any existing frames, which is dangerous but can save time. Also skips the sufficient-storage check.",
        )
        parser.add_argument(
            "--store-to",
            type=str,
            help="Instead of compressing, moves the raw frames to a directory under the specified path.",
        )
        parser.add_argument(
            "--keep-frames", action="store_true", help="Keep the massive raw frames (.raw files)."
        )
        parser.add_argument(
            "--overwrite", action="store_true", help="Delete the previous data if it exists."
        )
        parser.add_argument(
            "--plots",
            action="store_true",
            help="Plot the sensor data in the shell at the end of the run. This does not need to be enabled for the sensor data to be collected and stored",
        )
        parser.add_argument(
            "--plot-audio",
            action="store_true",
            help="Also plot the microphone data (as ASCII), which can be time-consuming. Has no effect if --plots is not set.",
        )
        parser.add_argument("--ignore-prior", action="store_true", help=argparse.SUPPRESS)
        parser.add_argument("--keep-lock", action="store_true", help=argparse.SUPPRESS)
        args = self._parse_args(parser)
        # TODO allow --keep-frames without --local, but filter the .raw files with SCP
        # if ValarSauronConfigManager().is_new():  # we should do this everywhere else too
        # 	warnings.warn("The local sauron_config is not in Valar.")
        SubmitMode().run(
            args.hashes,
            args.dark,
            args.local or args.keep_frames,
            args.overwrite,
            args.keep_frames,
            args.store_to,
            args.assume_clean,
            args.plots,
            args.plot_audio,
            args.halt,
            args.ignore_prior,
            args.keep_lock,
        )

    def incubate(self) -> None:
        parser = argparse.ArgumentParser(description="Keep a plate in darkness and lock SauronX")
        parser.add_argument(
            "duration", type=self._to_sec, help="Amount of time to lock SauronX (ex: 15s)"
        )
        parser.add_argument("--sensors", action="store_true", help="Record sensor values to files.")
        args = self._parse_args(parser)
        IncubateMode().run(args.duration, with_sensors=args.sensors)

    def proceed(self) -> None:
        parser = argparse.ArgumentParser(
            description="Restarts a job after post-capture events failed."
        )
        parser.add_argument("path", type=str, help="The path to the failed upload dir")
        parser.add_argument("--local", action="store_true", help="Don’t upload to Valinor.")
        parser.add_argument("--ignore-prior", action="store_true", help=argparse.SUPPRESS)
        args = self._parse_args(parser)
        ProceedMode().run(args.path, args.local, ignore_warnings=args.ignore_prior)

    def version(self) -> None:
        InfoTools().print_version()

    def obliterate(self) -> None:
        """Hidden subcommand: Too specialized for normal use."""
        warn_user("WARNING: This will destroy ALL output data.", "Use with care.")
        DataManager(None).obliterate(config.raw_frames_root)
        DataManager(None).obliterate(config.output_dir_root)

    def lock(self) -> None:
        """Hidden subcommand: Too specialized for normal use."""
        LockTools().lock()

    def unlock(self) -> None:
        parser = argparse.ArgumentParser(
            description="Overrides the lock and unlocks. Necessary if SauronX fails without being able to shut down gracefully."
        )
        self._parse_args(parser)
        LockTools().unlock()

    def clear(self) -> None:
        parser = argparse.ArgumentParser(
            description="Forcibly remove items from the list of submissions being processed. Useful if SauronX mistakenly thinks a submission is being handled."
        )
        parser.add_argument(
            "hashes",
            type=self._submission_hash_it,
            nargs="*",
            help="If not specified, clears every item in the list.",
        )
        parser.add_argument(
            "--force", action="store_true", help="Force removal even if SauronX is running."
        )
        args = self._parse_args(parser)
        LockTools().clear(args.hashes, args.force)

    def parrot(self) -> None:
        """Squawks.
        Public domain (CC0) image from https://pixabay.com/p-1525817
        Converted to ASCII using http://picascii.com/
        """
        parser = argparse.ArgumentParser(description="Squawks.")
        self._parse_args(parser)
        with urlopen("https://valinor.ucsf.edu/assets/parrot") as f:
            print(f.read().decode("utf8"))
        print(
            Fore.RED
            + Style.NORMAL
            + "Did you mean: "
            + Style.BRIGHT
            + "'sauronx repeat'"
            + Style.NORMAL
            + "?\n"
        )

    def squawk(self) -> None:
        parser = argparse.ArgumentParser(description="Squawks.")
        self._parse_args(parser)
        self.parrot()

    def test(self) -> None:
        parser = argparse.ArgumentParser(description="Run a SauronX test battery.")
        parser.add_argument(
            "--keep",
            action="store_true",
            help="Keep the local data and run history after completion",
        )
        parser.add_argument(
            "--plots",
            action="store_true",
            help="Plot the sensor data in the shell at the end of the run. This does not need to be enabled for the sensor data to be collected and stored",
        )
        parser.add_argument(
            "--plot-audio",
            action="store_true",
            help="Also plot the microphone data (as ASCII), which can be time-consuming. Has no effect if --plots is not set.",
        )
        parser.add_argument(
            "--assume-clean",
            action="store_true",
            help="Ignore any existing frames, which can save time. Use only for testing.",
        )
        parser.add_argument("--upload", action="store_true", help="Uploads the data to Valinor")
        args = self._parse_args(parser)
        TestMode().run(args.keep, args.upload, args.assume_clean, args.plots, args.plot_audio)

    def check(self) -> None:
        parser = argparse.ArgumentParser(description="Check hardware.")
        parser.add_argument(
            "--alive-ms",
            type=int,
            default=1000,
            help="The number of milliseconds to record for each change",
        )
        args = self._parse_args(parser)
        CheckMode().run(args.alive_ms)

    def prototype(self) -> None:
        parser = argparse.ArgumentParser(
            description="Capture a single frame and display it with ROI"
        )
        parser.add_argument(
            "--plate-type",
            type=int,
            default=1,
            help="Use this plate type ID for the ROI (currently ignored)",
        )
        args = self._parse_args(parser)
        PrototypeMode().run(args.plate_type)

    def preview(self) -> None:
        parser = argparse.ArgumentParser(
            description="Capture a single frame and display it with ROI"
        )
        parser.add_argument(
            "--plate-type", type=int, default=1, help="Use this plate type ID for the ROI"
        )
        args = self._parse_args(parser)
        LivePreviewMode().run(args.plate_type)

    def snapshot(self) -> None:
        parser = argparse.ArgumentParser(
            description="Capture a single frame and display it with ROI"
        )
        parser.add_argument(
            "--plate-type", type=int, default=1, help="Use this plate type ID for the ROI"
        )
        args = self._parse_args(parser)
        SnapshotMode().run(args.plate_type)

    def webcam(self) -> None:
        parser = argparse.ArgumentParser(description="Capture a single frame and display it")
        args = self._parse_args(parser)
        WebcamSnapshotMode().run()

    def calibrate(self) -> None:
        parser = argparse.ArgumentParser(description="Calibrate a sensor")
        parser.add_argument("sensor", type=str, help="The name of the sensor; ex: photometer")
        parser.add_argument(
            "--sampling-seconds",
            type=float,
            default=1,
            help="Number of seconds to sample SauronX sensor values for",
        )
        args = self._parse_args(parser)
        CalibrateMode().run(args.sensor, args.sampling_seconds)

    def ls(self) -> None:
        parser = argparse.ArgumentParser(description="List paths of SauronX output on this machine")
        parser.add_argument(
            "--dir",
            type=str,
            default=config.output_dir_root,
            help="Look at SauronX data in a different base directory",
        )
        args = self._parse_args(parser)
        DataManager(None).ls(args.dir)

    def data(self) -> None:
        parser = argparse.ArgumentParser(description="List SauronX output on this machine")
        args, restrictions, options, base_dir = self._data_args(parser)
        with Valar() as db:
            DataManager(db).data(restrictions, options, base_dir)

    def clean(self) -> None:
        parser = argparse.ArgumentParser(
            description="List SauronX output on this machine and decide whether to delete it"
        )
        parser.add_argument(
            "--auto", action="store_true", help="Auto-accept each recommendation without prompting"
        )
        parser.add_argument(
            "--skip-ignores",
            action="store_true",
            help="Don’t prompt when the recommendation is to ignore.",
        )
        args, restrictions, options, base_dir = self._data_args(parser)
        with Valar() as db:
            if args.auto:
                DataManager(db).auto_clean(restrictions, options, base_dir)
            else:
                DataManager(db).clean(restrictions, options, base_dir, args.skip_ignores)

    def identify(self) -> None:
        parser = argparse.ArgumentParser(
            description="Show the status of the most recent run of a submission",
            usage="sauronx locate 30ca8f037caf",
        )
        parser.add_argument("hash", help="The submission hash")
        args = self._parse_args(parser)
        IdentificationTools().identify(args.hash)

    def lookup(self) -> None:
        parser = argparse.ArgumentParser(
            description="List something in Valar",
            usage="sauronx lookup [users|experiments|submissions|history|batteries|assays|templates|configs|stimuli|audio_files|sensors|plates|runs|plate_types|saurons|locations]",
        )
        parser.add_argument("what", help="What to list")
        args = self._parse_args(parser)
        with Valar():
            getattr(LookupTools(), args.what)()

    def connect(self) -> None:
        """Hidden connection test."""
        with Valar():
            pass

    def info(self) -> None:
        parser = argparse.ArgumentParser(
            description="Shows information about the current Sauron configuration."
        )
        parser.add_argument("--full", action="store_true", help="Show even more.")
        args = self._parse_args(parser)
        InfoTools().print_info(args.full)

    def log(self) -> None:
        parser = argparse.ArgumentParser(
            description="Show the recent history of submissions on this Sauron."
        )
        self._parse_args(parser)
        lookup = LookupTools()
        with Valar():
            lookup.history()

    def status(self) -> None:
        parser = argparse.ArgumentParser(
            description="Prints the currently running job on SauronX, if any."
        )
        self._parse_args(parser)
        InfoTools().print_status()

    def modify(self) -> None:
        parser = argparse.ArgumentParser(description="Mark a change to Sauron hardware or config")
        parser.add_argument(
            "change",
            help="A text description of the change you made. Please tag with your initials.",
        )
        args = self._parse_args(parser)
        HardwareTools().update(args.change)

    def update(self) -> None:
        parser = argparse.ArgumentParser(
            description="Pulls the latest stable release from Github and installs it."
        )
        self._parse_args(parser)
        VersionTools().update()

    def _data_args(
        self, parser: argparse.ArgumentParser
    ) -> (object, DisplayOptions, SearchRestrictions, str):
        parser.add_argument(
            "--verdict",
            type=str,
            help="""
            Only show output for submissions that ended in this verdict.
            Available options: 'test', 'available', 'not_processed', 'failed_remotely', 'failed_locally', 'unrecoverable', 'invalid'
        """,
        )
        parser.add_argument(
            "--dir",
            type=str,
            default=config.output_dir_root,
            help="Look at SauronX data in a different base directory",
        )
        parser.add_argument(
            "--status",
            type=str,
            help="Only show output for submissions with a history entry that has this status",
        )
        parser.add_argument(
            "--submission", type=str, help="Only show the submission with this hash hex"
        )
        parser.add_argument(
            "--user", type=str, help="Only show output for submissions owned by user (username)"
        )
        parser.add_argument(
            "--experiment", type=str, help="Only show output for submissions under this project"
        )
        parser.add_argument(
            "--superproject",
            type=str,
            help="Only show output for submissions under this superproject",
        )
        parser.add_argument(
            "--before",
            type=str,
            help="Only show output for submissions created before this date (flexible format)",
        )
        parser.add_argument(
            "--after",
            type=str,
            help="Only show output for submissions created after this date (flexible format)",
        )
        parser.add_argument("--no-history", action="store_true", help="Skip the submission history")
        parser.add_argument("--no-local", action="store_true", help="Skip the local data info")
        parser.add_argument("--no-verdict", action="store_true", help="Skip the verdict")
        parser.add_argument("--no-warnings", action="store_true", help="Skip the warnings")
        args = self._parse_args(parser)
        return (
            args,
            SearchRestrictions(
                args.verdict,
                args.status,
                args.submission,
                args.user,
                args.experiment,
                args.superproject,
                args.before,
                args.after,
            ),
            DisplayOptions(
                not args.no_warnings, not args.no_local, not args.no_history, not args.no_verdict
            ),
            args.dir,
        )

    def _parse_args(self, parser: argparse.ArgumentParser):
        # parser.add_argument('--debug', action='store_true', help='Show debugging output in stdout')
        try:
            args = parser.parse_args(sys.argv[2:])
            # if args.debug:
            # 	pass
            return args
        except SystemExit as e:
            raise NaturalExpectedException from e

    def _submission_hash_it(self, submission_hash: str) -> Optional[str]:
        if not looks_like_submission_hash(submission_hash) and not submission_hash == "_" * 12:
            raise argparse.ArgumentTypeError(
                "The submission hash must be a 12-digit lowercase hexidecimal number but was {}".format(
                    submission_hash
                )
            )
        return submission_hash

    def _to_ms(self, string: str) -> int:
        ureg = UnitRegistry()
        return int(round(ureg(string).to(ureg.milliseconds).magnitude, 0))

    def _to_sec(self, string: str) -> int:
        ureg = UnitRegistry()
        try:
            return int(round(ureg(string).to(ureg.seconds).magnitude, 0))
        except AttributeError:
            raise argparse.ArgumentTypeError(
                "Please specify units in argument (e.g. '5 seconds' or '1hr') (got {})".format(
                    string
                )
            )


if __name__ == "__main__":
    Main()

__all__ = ["Main"]

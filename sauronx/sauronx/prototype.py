import cmd
import logging
import os
import shlex
import shutil
from argparse import ArgumentError, ArgumentParser
from typing import Optional
from pocketutils.core.exceptions import BadCommandError, NaturalExpectedError, UserError, LookupFailedError, \
    BadWriteError
from colorama import Fore
from .arduino import Board
from .audio import AudioInfo
from .configuration import config, reload_config
from .global_audio import SauronxAudio
from .lookup import *
from .protocol import AssayBlock, ProtocolBlock
from .schedule import Schedule
from .sensors import SensorParams, SensorRegistry, SensorTrigger
from .utils import prompt_yes_no

class UsageError(Exception):
    message = None  # type: str

    def __init__(self, message: str) -> None:
        self.message = message


class Parser(ArgumentParser):
    def error(self, message):
        raise BadCommandError(message)

    def parse_args(self, args=None, namespace=None):
        args = shlex.split(args)
        # args = [z for z in str(args).split(' ') if len(z.strip()) > 0]
        try:
            return super(Parser, self).parse_args(args, namespace)
        except BaseException as e:  # TODO a little dangerous, but argparse likes to throw system exits
            raise UsageError(self.format_help())


class Prototyper(cmd.Cmd):

    intro = (
        Fore.GREEN
        + "Ready. "
        + Fore.BLUE
        + "Type help or ? to list commands, and command --help to see detailed usage.\n"
    )
    prompt = Fore.BLUE + "> "
    file = None

    def __init__(self, plate_type_id: int) -> None:
        super(Prototyper, self).__init__()
        self.plate_type_id = plate_type_id
        self._registry = None
        self.recording = False
        self.camera = None
        self.audio = None
        self.board = None
        self.lookup = None

    def __enter__(self):
        self.init()
        return self

    def init(self):
        self.audio = SauronxAudio()
        self.audio.start()
        self.lookup = LookupTools()
        self.board = Board()
        self.board.init()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.finish()

    def finish(self) -> None:
        if self.board is not None:
            self.board.finish()
            self.audio.stop()

    def cmdloop(self, intro: Optional[str] = None) -> None:
        while True:
            try:
                super(Prototyper, self).cmdloop(intro=intro)
                self.postloop()
                break
            except KeyboardInterrupt:
                if prompt_yes_no("Exit? [yes/no]"):
                    raise NaturalExpectedError()
            except (
                BadCommandError,
                ArgumentError,
                UserError,
                ValueError,
                LookupFailedError,
                BadWriteError,
            ) as e:
                print(Fore.RED + str(e))
                # self.do_help(None)
            except UsageError as e:
                print(e.message)

    def onecmd(self, line):
        # put replacements here; ex:
        if line in {
            "let there be light",
            "fiat lux",
            "γενηθήτω φῶς",
            "genēthētō phōs",
            "yehi 'or",
            "יְהִי אוֹר‎",
        }:
            line = "light"
        return super(Prototyper, self).onecmd(line)

    def default(self, line):
        print(Fore.RED + "Command not recognized.")

    def do_exit(self, arg):
        """Exits the prototyper."""
        raise NaturalExpectedError()

    def do_quit(self, arg):
        """Exits the prototyper."""
        raise NaturalExpectedError()

    def do_reload(self, arg):
        """Reload the TOML config file."""
        reload_config()

    def do_flash(self, args):
        """Flash an LED status code."""
        parser = Parser(description="Flashes a status code.")
        parser.add_argument(
            "code",
            type=str,
            help="The name of the status code (startup, shutdown, ready, done, error)",
        )
        self.board.flash_error()
        try:
            getattr(self.board, "flash_" + parser.parse_args(args).code)()
        except AttributeError:
            raise BadCommandError("Code {} not recognized.".format(args))

    def do_analog(self, args):
        """Write a value to an analog pin."""
        parser = Parser(description="Write a value to an analog pin.")
        parser.add_argument("pin", type=int, help="The analog pin number")
        parser.add_argument("value", type=_byte, help="Value as a (positive) byte")
        # noinspection PyProtectedMember
        self.board._board.analog_write(args.pin, args.value)

    def do_digital(self, args):
        """Write a value to a digital pin."""
        parser = Parser(description="Write a value to a digital pin.")
        parser.add_argument("pin", type=int, help="The digital pin number")
        parser.add_argument("value", type=_byte, help="0 or 1")
        # noinspection PyProtectedMember
        self.board._board.digital_write(args.pin, args.value)

    def do_record(self, args):
        """Start recording sensor data."""
        if self._registry is not None:
            self._registry.terminate(SensorTrigger.EXPERIMENT_START)
        sensor_dir = os.path.join(config.get_prototyping_dir(), "sensors")
        if os.path.exists(sensor_dir):
            shutil.rmtree(sensor_dir)
        self._registry = SensorRegistry(
            SensorParams(60, config.get_prototyping_dir())
        )  # duration is ignored
        self._registry.ready(SensorTrigger.EXPERIMENT_START)
        self._registry.start(SensorTrigger.EXPERIMENT_START, self.board)
        print(
            Fore.GREEN
            + "Sensors are now recording. Type 'plot' to view or 'terminate' to stop recording."
        )

    def do_terminate(self, args):
        """Save sensor data and end recording."""
        if self._registry is None:
            raise BadCommandError("No sensor data is being recorded.")
        try:
            self._registry.terminate(SensorTrigger.EXPERIMENT_START)
            self._registry = None
            print(
                Fore.GREEN + "Sensors are now off. You can start recording again by typing 'record'"
            )
        except BaseException as e:
            logging.error(e, exc_info=True)

    def do_plot(self, args):
        """Save sensor data and output ASCII plots."""
        if self._registry is None:
            raise BadCommandError("No sensor data is being recorded.")
        self._registry.save(SensorTrigger.EXPERIMENT_START)
        for sensor in self._registry.fetch():
            print("")
            print(sensor.plot())

    def do_stimuli(self, args) -> None:
        """Show a table of stimuli."""
        Parser(description="Show a table of stimuli").parse_args(args)
        self.lookup.stimuli()

    def do_list(self, args) -> None:
        """Alias of lookup."""
        self.do_lookup(args)

    def do_lookup(self, args) -> None:
        """List something from Valar."""
        parser = Parser(description="List something from Valar")
        parser.add_argument("what", type=str, help="What to list")
        try:
            getattr(self.lookup, parser.parse_args(args).what)()
        except AttributeError:
            raise BadCommandError(
                "Table {} is not recognized. See 'sauronx list' for help.".format(args)
            )

    def do_set(self, args) -> None:
        """Set a stimulus to a specific value."""
        parser = Parser(description="Set a stimulus to a specific value.")
        parser.add_argument(
            "stimulus",
            type=str,
            help="The name of the stimulus to set (substitute spaces with underscores)",
        )
        parser.add_argument("value", type=_byte, help="Value as a (positive) byte")
        args = parser.parse_args(args)
        self.board.set_stimulus(args.stimulus, args.value)

    def do_on(self, args) -> None:
        """Synonym of start."""
        self.do_start(args)

    def do_start(self, args) -> None:
        """Set a stimulus to max."""
        stimulus = self._parse_set(args, "Set a stimulus to max")
        self.board.set_stimulus_max(stimulus)

    def do_off(self, args) -> None:
        """Synonym of stop."""
        self.do_stop(args)

    def do_stop(self, args) -> None:
        """Turn a stimulus off."""
        stimulus = self._parse_set(args, "Turn a stimulus off")
        self.board.set_stimulus(stimulus, 0)

    def do_light(self, args) -> None:
        """Turns the IR array on."""
        self.board.ir_on()

    def do_dark(self, args) -> None:
        """Turns the IR array off."""
        self.board.ir_off()

    def do_fiat_lux(self, args):
        """Turns the IR array on."""
        self.board.ir_on()

    def do_pulse(self, args) -> None:
        """Turn a stimulus on, then off."""
        parser = Parser(description="Turn a stimulus on, then off")
        parser.add_argument("stimulus", type=str, help="The name of the stimulus to set")
        parser.add_argument(
            "--ms",
            type=_positive_float,
            default=1000,
            help="Number of milliseconds to keep the stimulus on",
        )
        parser.add_argument(
            "--value", type=_byte, default=255, help="Value for on as a (positive) byte"
        )
        args = parser.parse_args(args)
        self.board.pulse(args.stimulus, args.ms / 1000, args.value)

    def do_bump(self, args) -> None:
        """Turns on a stimulus and gently lets it back down."""
        parser = Parser(
            description="Turns a stimulus to up-pwm for up-ms milliseconds, then turns it to down-pwm for down-ms ms."
        )
        parser.add_argument(
            "--stimulus", type=str, default="solenoid", help="The name of the stimulus to set"
        )
        parser.add_argument("--up-pwm", type=_positive_float, default=255, help="")
        parser.add_argument("--down-pwm", type=_positive_float, default=70, help="")
        parser.add_argument("--up-ms", type=_positive_float, default=20, help="")
        parser.add_argument("--down-ms", type=_positive_float, default=1000, help="")
        args = parser.parse_args(args)
        self.board.bump(args.stimulus, args.up_pwm, args.down_pwm, args.up_ms, args.down_ms)

    def do_strobe(self, args) -> None:
        """Turn a stimulus on and off repeatedly."""
        parser = Parser(description="Turn a stimulus on and off repeatedly")
        parser.add_argument("stimulus", type=str, help="The name of the stimulus to set")
        parser.add_argument(
            "--ms",
            type=_positive_float,
            default=10000,
            help="Number of milliseconds to keep the stimulus on",
        )
        parser.add_argument(
            "--isi",
            type=_positive_float,
            default=500,
            help="The inter-stimulus interval, in milliseconds",
        )
        parser.add_argument(
            "--value", type=_byte, default=255, help="Value for on as a (positive) byte"
        )
        args = parser.parse_args(args)
        self.board.strobe(args.stimulus, args.ms / 1000, args.isi / 1000, args.value)

    def do_play(self, args) -> None:
        """Play an audio file."""
        parser = Parser(description="Play an audio file")
        parser.add_argument("stimulus", type=str, help="The name of the audio stimulus to play")
        parser.add_argument(
            "--ms",
            type=_positive_int,
            help="If set, repeat and truncate the file as needed to play for this number of milliseconds. If not set, play at the native length.",
        )
        parser.add_argument(
            "--volume",
            type=_byte,
            default=255,
            help="Volume as a positive byte, where 255 is the highest and 0 is off",
        )
        args = parser.parse_args(args)
        audio_obj = AudioInfo.build(args.stimulus, args.ms, args.volume)
        self.audio.play(audio_obj)

    def do_run(self, args) -> None:
        """Runs a battery."""
        parser = Parser(description="Run a full battery")
        parser.add_argument("type", type=_pa, help='Either "assay"/"a" or "battery"/"p"')
        parser.add_argument("name", type=str, help="The ID or name of a battery or assay in Valar")
        args = parser.parse_args(args)
        block = (
            ProtocolBlock(_battery_id(args.name))
            if args.type == "battery"
            else AssayBlock(_assay_id(args.name))
        )

        schedule = Schedule(block.stimulus_list, len(block))
        schedule.run_scheduled_and_wait(self.board, self.audio)

    def _parse_set(self, args, description: str) -> str:
        parser = Parser(description=description)
        parser.add_argument(
            "stimulus",
            type=str,
            help="The name of the stimulus to set (substitute spaces with underscores)",
        )
        return parser.parse_args(args).stimulus


def _pa(value: str) -> str:
    if value.lower() in {"assay", "a"}:
        return "assay"
    if value.lower() in {"battery", "p"}:
        return "battery"
    raise UsageError("Must be either 'assay' or 'battery'; was '{}'".format(value))


def _byte(value: str) -> int:
    if value.isdigit() and int(value) in range(0, 256):
        return int(value)
    else:
        raise BadWriteError("Value must be a byte (0–255) but was {}".format(value))


def _positive_int(value: str) -> int:
    if value.isdigit() and int(value) > 0:
        return int(value)
    else:
        raise BadWriteError("Value must positive integer but was {}".format(value))


def _positive_float(value: str) -> float:
    if value.isdecimal() and float(value) > 0:
        return float(value)
    else:
        raise BadWriteError("Value be a positive float but was {}".format(value))


def _assay_id(value: str) -> int:
    import valarpy.model as model

    if value.isdigit():
        p = model.Assays.select().where(model.Assays.id == int(value)).first()
    else:
        p = model.Assays.select().where(model.Assays.name == value).first()
    if p is None:
        raise UsageError(
            'Specify either a name or ID of a valid row in Batteries (type "list Batteries")'
        )
    return p.id


def _battery_id(value: str) -> int:
    import valarpy.model as model

    if value.isdigit():
        p = model.Batteries.select().where(model.Batteries.id == int(value)).first()
    else:
        p = model.Batteries.select().where(model.Batteries.name == value).first()
    if p is None:
        raise UsageError(
            'Specify either a name or ID of a valid row in Batteries (type "list Batteries")'
        )
    return p.id

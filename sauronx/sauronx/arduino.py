import time

from pocketutils.core.exceptions import *
from PyMata.pymata import PyMata

from .configuration import config
from .stimulus import StimulusType


class Board:
    """Handles all aspects of an Arduino board.
    This must be used with the with statement.
            with Board() as board:
                    board.schedule_stimuli(stimuli)
                    board.register_sensor(pin, callback)
    """

    def __init__(self) -> None:
        assert config is not None, "The config in configuration.py was not set!"

        self._board = None

        self._digital_stimuli_pins = config.stimuli["digital_pins"]
        self._analog_stimuli_pins = config.stimuli["analog_pins"]
        self._digital_sensor_pins = config.sensors["digital_pins"]
        self._analog_sensor_pins = config.sensors["analog_pins"]

        # TODO these checks are correct, right?
        if len(set(self._digital_stimuli_pins).intersection(self._analog_stimuli_pins)) != 0:
            raise ConfigError("There is overlap between the digital and analog stimulus pins")
        if len(set(self._digital_sensor_pins).intersection(self._analog_sensor_pins)) != 0:
            raise ConfigError("There is overlap between the digital and analog sensor pins")

        # use sub for safety, then get because the containment check in TomlData is probably more expensive
        digital_ports = config.sub("sauron.hardware.arduino.ports.digital")
        analog_ports = config.sub("sauron.hardware.arduino.ports.digital")

        self._allowed_digital_pins = flatten(
            [[pin for pin in allowed] for port, allowed in digital_ports.items()]
        )
        self._allowed_analog_pins = flatten(
            [[pin for pin in allowed] for port, allowed in analog_ports.items()]
        )

        self._digital_pins_to_ports = None
        self._analog_pins_to_ports = None

        # TODO:
        # 1. verify pins match ports w.r.t. digital and analog
        # 2. set pin directions
        # less urgent:
        # 3. map stimulus names to their ports
        # 4. initialize port value states (_digital_port_values)

        # a dict mapping port names to bytes
        # we'll have to make sure not to write over a sensor pin
        self._digital_port_values = None

    def __enter__(self):
        self.init()
        return self

    def init(self) -> None:
        logging.info("Connecting to board...")
        self._connect()
        logging.debug("Initializing pins.")
        self._init_pins()
        logging.debug("Finished initializing pins.")
        self._set_sampling_interval()
        self.ir_on()
        self.flash_startup()
        logging.debug("Finished initializing board.")

    def _connect(self) -> None:
        def board_load_error(the_error):
            warn_user(
                "Could not connect to the Arduino board.",
                "First, try unplugging the board and plugging it back in.",
                "Make sure that the correct firmware is loaded.",
                "To change the firmware, open the Arduino application,",
                "open the StandardFirmata 'sketch' (file-->open recent), and click upload.",
            )

        try:
            self._board = PyMata(port_id="/dev/ttyACM0", baud_rate=57600)
        except (TypeError, ValueError, Exception) as e:
            board_load_error(e)
            raise MissingDeviceError("Could not connect to the Arduino board") from e
        if self._board is None:
            board_load_error(None)
            raise MissingDeviceError("Could not connect to the Arduino board")
        logging.debug("Connected to board.")

    def _set_sampling_interval(self):
        sampi = config.sensors["sampling_interval_milliseconds"]
        if sampi < 12:
            v = "The sampling interval of {} is too low. Must be at least 12.".format(sampi)
            warn_user(v)
            raise ValueError(v)
        elif sampi < 20:
            logging.warning("The sampling interval {} is probably too low (< 20ms).".format(sampi))
            warn_user(
                "The sampling interval is very low {}.".format(sampi),
                "This may cause connection failures, terminating the run.",
            )
        elif sampi < 50:
            logging.warning(
                "The sampling interval {} is potentially too low (< 50ms).".format(sampi)
            )
        elif sampi > 200:
            logging.warning(
                "The sampling interval {} is very high (>200ms). Sensors may miss some stimuli.".format(
                    sampi
                )
            )
        self._board.set_sampling_interval(sampi)
        logging.info("Set sampling interval to {}ms".format(sampi))

    def _init_pins(self):
        if "sauron.hardware.illumination.pins.status_led" in config:
            self._board.digital_write(config["sauron.hardware.illumination.pins.status_led"], 1)
        for name in self._analog_stimuli_pins:
            self._board.set_pin_mode(self._analog_stimuli_pins[name], PyMata.PWM, PyMata.DIGITAL)
        for name in self._analog_sensor_pins:
            self._board.set_pin_mode(self._analog_sensor_pins[name], PyMata.INPUT, PyMata.ANALOG)

    def __exit__(self, t, value, traceback) -> None:
        self.finish()

    def register_sensor(self, pin_number: int, callback) -> None:
        # TODO test
        try:
            pin_state_q = self._board.pin_state_query(pin_number)
            pin_state = self._board.get_pin_state_query_results()
            logging.debug("Registered sensor on pin {}".format(pin_number))
            self._board.enable_analog_reporting(pin=pin_number)
            # TODO should be able to use pin_state[1] instead of Constants.ANALOG, but for some reason the setting doesn't stick??
            self._board.set_pin_mode(pin_number, PyMata.INPUT, PyMata.ANALOG, cb=callback)
        except Exception as e:
            logging.fatal("Failed while registering sensor on pin {}".format(pin_number))
            warn_user("Failed while registering sensor on pin {}".format(pin_number))
            raise e

    def reset_sensor(self, pin_number: int) -> None:
        try:
            self._board.disable_analog_reporting(pin=pin_number)
        except Exception as e:
            logging.error("Failed while de-registering sensor on pin {}".format(pin_number))
            warn_user("Failed while de-registering sensor on pin {}".format(pin_number))
            logging.debug("Sensor-deregistration failure", exc_info=True)

    def finish(self) -> None:
        # this is in case we already called finish()
        if self._board is None:
            return
        logging.info("Setting pins to off and shutting down Arduino...")
        try:
            self.flash_shutdown()
            # TODO use turn_off_digital_pins for the whole port instead
            # NOTE: we assume here that 0 is always off
            for pin in self._digital_stimuli_pins.values():
                self._board.digital_write(pin, 0)
            for pin in self._analog_stimuli_pins.values():
                self._board.analog_write(pin, 0)
            self._board.digital_write(config["sauron.hardware.illumination.pins.ir_array"], 0)
            if "sauron.hardware.illumination.pins.status_led" in config:
                self._board.digital_write(config["sauron.hardware.illumination.pins.status_led"], 0)
            for pin in self._digital_sensor_pins.values():
                self._board.disable_digital_reporting(pin)
            for pin in self._analog_sensor_pins.values():
                self._board.disable_analog_reporting(pin)
        except BaseException as e:
            logging.exception("Got an error while writing pins to off")
        try:
            self._board._command_handler.stop()
            self._board.transport.stop()
            self._board._command_handler.join()
            self._board.transport.join()
            time.sleep(2)
        except:
            logging.exception("FAILED SHUTDOWN")
            raise
        logging.info("Finished shutting down Arudino.")

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)

    def strobe(
        self, stim_name: str, duration: float = 10, isi_seconds: float = 0.5, pwm_value: int = 200
    ) -> None:
        """Strobes an analog or digital stimulus at an inter-stimulus interval for a duration."""
        if self.is_digital(stim_name):
            pwm_value = 1
        t0 = time.monotonic()
        while time.monotonic() - t0 < duration:
            self.set_stimulus(stim_name, pwm_value)
            time.sleep(isi_seconds)
            self.set_stimulus(stim_name, 0)
            time.sleep(isi_seconds)

    def flash_error(self):
        self.flash_status(2, 25, 125)

    def flash_warning(self):
        self.flash_status(0.5, 50, 175)

    def flash_ready(self):
        self.flash_status(1.2, 300, 300)

    def flash_done(self):
        self.flash_status(0.6, 300, 300)

    def flash_startup(self):
        self.flash_status(1, 400, 100)

    def flash_shutdown(self):
        self.flash_status(1, 100, 400)

    def flash_status(self, seconds: float = 1, on_ms: float = 100, off_ms: float = 100):
        # TODO asynchronous in a safe way
        # asyncio.run_coroutine_threadsafe(self._flash_status(seconds, on_ms, off_ms), asyncio.get_event_loop())
        try:
            self._flash_status(seconds, on_ms, off_ms)
        except:
            logging.error("Failed to flash to status LED.")

    def _flash_status(self, seconds: float = 1, on_ms: float = 100, off_ms: float = 100):
        t0 = time.monotonic()
        """
		if 'sauron.hardware.illumination.pins.status_led' in config:
			while time.monotonic() - t0 < seconds:
				self._board.digital_write(config['sauron.hardware.illumination.pins.status_led'], 1)
				time.sleep(on_ms/1000)
				self._board.digital_write(config['sauron.hardware.illumination.pins.status_led'], 0)
				time.sleep(off_ms/1000)
			self._board.digital_write(config['sauron.hardware.illumination.pins.status_led'], 1)
		"""

    def status_on(self):
        self._board.digital_write(config["sauron.hardware.illumination.pins.status_led"], 1)

    def status_off(self):
        self._board.digital_write(config["sauron.hardware.illumination.pins.status_led"], 0)

    def pulse(self, stim_name: str, sleep_seconds: float = 1, pwm_value: int = 200) -> None:
        """Turns a pin on, then off."""
        if self.is_digital(stim_name):
            pwm_value = 1
        self.set_stimulus(stim_name, pwm_value)
        time.sleep(sleep_seconds)
        self.set_stimulus(stim_name, 0)

    def set_stimulus_max(self, stim_name: str) -> None:
        if self.is_digital(stim_name):
            self.set_stimulus(stim_name, 1)
        else:
            self.set_stimulus(stim_name, 255)

    def ir_on(self):
        self._board.digital_write(config["sauron.hardware.illumination.pins.ir_array"], 1)

    def ir_off(self):
        self._board.digital_write(config["sauron.hardware.illumination.pins.ir_array"], 0)

    def set_stimulus(self, stim_name: str, value: int) -> None:
        """Sets an analog or digital stimulus. For external calls."""
        if self.is_digital(stim_name):
            if value != 0 and value != 1:
                raise ValueError(
                    "Value {} is out of range for digital stimulus {}".format(value, stim_name)
                )
            self._board.digital_write(config.stimuli["digital_pins"][stim_name], value)
        elif self.is_analog(stim_name):
            if value > 255 or value < 0:
                raise ValueError(
                    "Value {} is out of range for analog stimulus {}".format(value, stim_name)
                )
            self._board.analog_write(config.stimuli["analog_pins"][stim_name], value)

    def set_analog_stimulus(self, stim_name: str, value: int) -> None:
        """For external calls; performs a value check."""
        if value > 255 or value < 0:
            raise ValueError("Analog write value must be between 0 and 255; was {}".format(value))
        self._board.analog_write(self._analog_stimuli_pins[stim_name], value)

    def set_digital_stimulus(self, stim_name: str, value: int) -> None:
        """For external calls; performs a value check."""
        if value not in (0, 1):
            raise ValueError("Digital write value must be 0 or 1; was {}".format(value))
        self._board.digital_pin_write(self._digital_stimuli_pins[stim_name], value)

    def is_digital(self, stimulus_name: str) -> bool:
        return self.stimulus_type(stimulus_name) == StimulusType.DIGITAL

    def is_analog(self, stimulus_name: str) -> bool:
        return self.stimulus_type(stimulus_name) == StimulusType.ANALOG

    def stimulus_type(self, stimulus_name: str) -> StimulusType:
        """Returns either 'digital' or 'analog'."""
        if stimulus_name in self._analog_stimuli_pins:
            return StimulusType.ANALOG
        elif stimulus_name in self._digital_stimuli_pins:
            return StimulusType.DIGITAL
        else:
            raise LookupError("No stimulus with name {} exists".format(stimulus_name))

    def read_digital_sensor(self, sensor_name: str):
        self._board.digital_read(self._digital_sensor_pins[sensor_name])

    def read_analog_sensor(self, sensor_name: str):
        self._board.analog_read(self._analog_sensor_pins[sensor_name])


__all__ = ["Board"]

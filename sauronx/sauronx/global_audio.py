import logging
import platform
import typing
from typing import Optional

from pocketutils.core.exceptions import BadCommandError

from .audio import AudioInfo
from .configuration import config


class CouldNotConfigureOsAudioError(IOError):
    def description(self):
        return (
            "Could not set a needed audio device or gain through operating system calls."
            + "The platform appears to be {}.".format(platform.system())
        )


class GlobalAudio:
    """A global lock for audio input and output.
    Calling start() turns it on and calling stop() turns it off.
    Doing so may change the intput and output device if necessary.
    """

    def start(self) -> None:
        """
        Override this to do things like change the output source and volume.
        """
        pass

    def stop(self) -> None:
        """
        Override this to do things like reset the output source and volume to their original values.
        """
        pass

    def __init__(self) -> None:
        self.is_on = False  # type: bool

    def __enter__(self):
        self.start()
        self.is_on = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        self.is_on = False

    def play(self, info: AudioInfo, blocking: bool = False):
        assert self.is_on, "Cannot play sound because the audio service is off"
        if info.intensity > 0:
            aud = info.wave_obj.play()
            if blocking:
                aud.wait_done()


class SmartGlobalAudio(GlobalAudio):
    """
    A GlobalAudio that switches devices and volumes by detecting the OS.
    Looks for a parameterless function _start_{platform.system().lower()} to start, and _stop_{platform.system().lower()} to stop.
    For example, for Mac OS 10.12, this will be _start_darwin() and _stop_darwin()
    """

    def __init__(
        self,
        input_device: Optional[typing.Tuple[str, str]],
        output_device: Optional[typing.Tuple[str, str]],
        input_gain: Optional[typing.Tuple[int, int]],
        output_gain: Optional[typing.Tuple[int, int]],
        timeout_secs: float,
    ):
        super(SmartGlobalAudio, self).__init__()
        self.input_device = input_device
        self.output_device = output_device
        self.input_gain = input_gain
        self.output_gain = output_gain
        self.timeout_secs = timeout_secs

    def __repr__(self):
        return "SmartGlobalAudio:{}(input={}@{},output={}@{})".format(
            self.is_on, self.input_device, self.input_gain, self.output_device, self.output_gain
        )

    def __str__(self):
        return repr(self)

    def start(self) -> None:
        logging.debug("Starting audio handler.")
        self.__wrap("start")
        self.is_on = True
        logging.info("Started audio handler.")

    def stop(self) -> None:
        logging.debug("Stopping audio handler.")
        self.__wrap("stop")
        self.is_on = False
        logging.info("Stopped audio handler.")

    def __wrap(self, prefix: str):
        try:
            getattr(self, "_" + prefix + "_" + platform.system().lower())()
        except ExternalCommandFailed as e:
            raise CouldNotConfigureOsAudioError() from e
        except AttributeError as e:
            raise CouldNotConfigureOsAudioError(
                "OS {} not recognized".format(platform.system())
            ) from e


class DefaultSmartGlobalAudio(SmartGlobalAudio):
    """
    A default implementation of SmartGlobalAudio.
    WARNING: Won't break on Windows, but only changes sources in Mac OS.
    """

    def __repr__(self):
        return "{}:{}(input={}@{},output={}@{})".format(
            self.__class__.__name__,
            self.is_on,
            self.input_device,
            self.input_gain,
            self.output_device,
            self.output_gain,
        )

    def __str__(self):
        return repr(self)

    def _start_mac(self) -> None:
        self.__darwin_switch(0)

    def _stop_mac(self) -> None:
        self.__darwin_switch(1)

    def _start_windows(self) -> None:
        self.__windows_switch(0)

    def _stop_windows(self) -> None:
        self.__windows_switch(1)

    def _start_linux(self) -> None:
        self.__linux_switch(0)

    def _stop_linux(self) -> None:
        self.__linux_switch(1)

    def __windows_switch(self, i: int):
        def percent_to_real(percent: int) -> int:
            audio_max = (
                65535  # This is true of Windows in general, so not necessary to put in config
            )
            # audio min is 0
            return round(audio_max * percent / 100)

        if self.output_device is not None:
            logging.debug("Setting audio output device to %s" % self.output_device[i])
            wrap_cmd_call(
                ["nircmd", "setdefaultsounddevice", "%s" % self.output_device[i]],
                timeout_secs=self.timeout_secs,
            )
        if self.input_device is not None:
            logging.debug("Setting audio input device to %s" % self.input_device[i])
            wrap_cmd_call(
                ["nircmd", "setdefaultsounddevice", "%s" % self.input_device[i], "2"],
                timeout_secs=self.timeout_secs,
            )
        if self.output_gain is not None:
            logging.debug("Setting system volume to configured default %s" % self.output_gain[i])
            wrap_cmd_call(
                [
                    "nircmd",
                    "setsysvolume",
                    "%s" % percent_to_real(self.output_gain[i]),
                    self.output_device[i],
                ],
                timeout_secs=self.timeout_secs,
            )
        if self.input_gain is not None:
            logging.debug("Setting input gain to configured default %s" % self.input_gain[i])
            wrap_cmd_call(
                [
                    "nircmd",
                    "setsysvolume",
                    "%s" % percent_to_real(self.input_gain[i]),
                    self.input_device[i],
                ],
                timeout_secs=self.timeout_secs,
            )

    def __darwin_switch(self, i: int):
        if self.output_device is not None:
            logging.debug("Setting audio output device to %s" % self.output_device[i])
            wrap_cmd_call(["SwitchAudioSource", "-s", "%s" % self.output_device[i]])
        if self.input_device is not None:
            logging.debug("Setting audio input device to %s" % self.input_device[i])
            wrap_cmd_call(["SwitchAudioSource", "-t input", "-s", "%s" % self.input_device[i]])
        if self.output_gain is not None:
            logging.debug("Setting system volume to configured default %s" % self.output_gain[i])
            wrap_cmd_call(["osascript", "-e", "set volume output volume %s" % self.output_gain[i]])
        if self.input_gain is not None:
            logging.debug("Setting input gain to configured default %s" % self.input_gain[i])
            wrap_cmd_call(["osascript", "-e", "set volume input volume %s" % self.input_gain[i]])
        logging.debug("Done configuring audio")

    def __linux_switch(self, i: int):
        if self.output_device is not None:
            logging.debug("Setting audio output device to %s" % self.output_device[i])
            wrap_cmd_call(["pactl", "set-default-sink", "%s" % self.output_device[i]])
        if self.input_device is not None:
            logging.debug("Setting audio input device to %s" % self.input_device[i])
            wrap_cmd_call(["pactl", "set-default-source", "%s" % self.input_device[i]])
        if self.output_gain is not None:
            logging.debug("Setting system volume to configured default %s" % self.output_gain[i])
            wrap_cmd_call(
                [
                    "pactl",
                    "set-sink-volume",
                    "%s" % self.output_device[i],
                    "%s%%" % self.output_gain[i],
                ]
            )
        if self.input_gain is not None:
            logging.debug("Setting input gain to configured default %s" % self.input_gain[i])
            wrap_cmd_call(
                [
                    "pactl",
                    "set-source-volume",
                    "%s" % self.input_device[i],
                    "%s%%" % self.input_gain[i],
                ]
            )
        logging.debug("Done configuring audio")


class SauronxAudio(DefaultSmartGlobalAudio):
    def __init__(self):
        super(SauronxAudio, self).__init__(
            input_device=(
                config.audio["sauronx_input_audio_device"],
                config.audio["default_input_audio_device"],
            ),
            output_device=(
                config.audio["sauronx_output_audio_device"],
                config.audio["default_output_audio_device"],
            ),
            output_gain=(
                config.audio["sauronx_system_volume"],
                config.audio["default_system_volume"],
            ),
            input_gain=(config.audio["sauronx_input_volume"], config.audio["default_input_volume"]),
            timeout_secs=config.audio["init_timeout_secs"],
        )


__all__ = [
    "GlobalAudio",
    "SmartGlobalAudio",
    "DefaultSmartGlobalAudio",
    "CouldNotConfigureOsAudioError",
    "SauronxAudio",
]

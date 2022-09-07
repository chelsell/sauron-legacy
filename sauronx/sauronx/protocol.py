import itertools
import logging
import re
import typing
from datetime import timedelta
from typing import Any, List, Optional, Set, Sized

import numpy as np
import peewee

from sauronx import show_table

from .audio import AudioInfo
from .stimulus import Stimulus


class BaseBlock(Sized):
    def __init__(self, valar_obj: Any) -> None:
        """Fetches the battery, assays, and stimulus frames.
        Prepares Protocol.stimulus_list, which is a tuple of times (in milliseconds), stimulus names, and values.
        """
        self.valar_obj = valar_obj
        self.dangerous_writes = set([])  # type: Set[typing.Tuple[int, Stimulus]]
        self.stimulus_list = None  # type: List[typing.Tuple[int, Stimulus]]
        self._set_stimulus_list()

    @staticmethod
    def _assay_name_simplifier():
        import valarpy.model as model

        _usernames = {u.username for u in model.Users.select(model.Users.username)}
        _qualifier = re.compile("-\\(variant:.*\\)")
        _end = re.compile(
            "-(?:" + "|".join(_usernames) + ")" + """-\d{4}-\d{2}-\d{2}-0x[0-9a-h]{4}$"""
        )

        def _simplify_name(name: str) -> str:
            return (
                _qualifier.sub("", _end.sub("", name))
                .replace("legacy-", "#")
                .replace("sauronx-", "#")
                .replace("#legacy: ", "#")
                .replace("background:$length=", "background=")
            )

        return _simplify_name

    def __len__(self) -> int:
        """Returns the number of frames, or number of milliseconds."""
        return self.n_ms()

    ###
    # implement these
    ###

    def stimuli(self) -> set:
        raise NotImplementedError()

    def n_ms(self) -> int:
        raise NotImplementedError()

    def _stim_query(self, stimulus_id: int) -> peewee.Expression:
        raise NotImplementedError()

    def _start_of_frames(self, stimframes_obj) -> int:
        raise NotImplementedError()

    def _set_stimulus_list(self) -> None:
        # an edge case here is having no stimulus_frames
        # any change to the code must make sure that the empty battery still runs for the full duration
        stimuli = self.stimuli()
        self.stimulus_list = list(
            itertools.chain.from_iterable(
                [self._list_for_stimulus(stimulus) for stimulus in stimuli]
            )
        )
        self.stimulus_list = sorted(self.stimulus_list, key=lambda t: t[0])
        self._pretty_print_list(self.stimulus_list)

    def _pretty_print_list(self, stimulus_list):
        def tabify(index, stimulus) -> str:
            return (
                str(index).ljust(8)
                + str(stimulus.name).ljust(20)
                + str(round(stimulus.intensity, 2)).ljust(8)
                + str("-" if stimulus.audio_obj is None else stimulus.audio_obj.duration_ms).ljust(
                    8
                )
            )

        header = "ms".ljust(8) + "stimulus".ljust(20) + "value".ljust(8) + "duration(ms)".ljust(8)
        logging.info(
            "\n"
            + header
            + "\n"
            + "-" * (8 + 20 + 8 + 8)
            + "\n"
            + "\n".join([tabify(e[0], e[1]) for e in stimulus_list if not isinstance(e[1], str)])
        )

    def _list_for_stimulus(self, stimulus) -> List[tuple]:

        is_audio = stimulus.audio_file is not None
        stimulus_list = []  # type: List[(int, Stimulus)]

        stim_query = self._stim_query(stimulus.id)

        prev_value = 0
        prev_index = 0
        index = None

        simplifier = BaseBlock._assay_name_simplifier()

        def append(ms: int, val: int, time_since: Optional[int], chirp: bool) -> None:
            """
            :param ms: The current ms
            :param val: The value to change to
            :param time_since: The ms since the last change
            :param chirp: Treat all audio as native-length regardless of how long the stimulus_frames are applied; for legacy assays
            """
            if time_since is not None and time_since < 10 and not is_audio:  # TODO
                logging.error(
                    "Attempted to set {} {} {} {} {}".format(stimulus, ms, val, time_since, chirp)
                )
                return
            # set length to None (native length) for legacy assays because they don't use the definition audio length==1 <==> play exact length
            duration_ms = None if chirp else time_since
            if duration_ms == 1:
                duration_ms = None
            audio_obj = AudioInfo.build(stimulus, duration_ms, val) if is_audio else None
            if not is_audio or val > 0:  # don't write 0-volume audio files
                built_stim = Stimulus(stimulus, val, audio_obj)
                stimulus_list.append((ms, built_stim))

        for stimulus_index, stimframes_obj in enumerate(stim_query):

            # so that we can track the length, write the previous change when the next change is encountered
            # also, write the final change at the end
            stim_blob = blob_to_byte_array(stimframes_obj.frames)
            assay_name = stimframes_obj.assay.name.strip()
            chirp = assay_name.startswith("#legacy:") or assay_name.endswith("#chirp#")
            logging.debug(
                "Appending assay {} of length {} (chirp={})".format(
                    assay_name, len(stim_blob), chirp
                )
            )
            assay_start = self._start_of_frames(stimframes_obj)
            stimulus_list.append((assay_start, simplifier(assay_name)))  # TODO

            if index is not None and assay_start != index + 1 and stimulus.audio_file is None:
                append(index, 0, None, chirp)
                # logging.info("For gap on {} set {} at {}".format(stimulus.name, 0, index))
                prev_value = 0

            for mini_index, value in enumerate(stim_blob):
                index = assay_start + mini_index
                if value != prev_value:
                    if prev_index > 0:
                        append(prev_index, prev_value, index - prev_index, chirp)
                    # logging.debug("For stimulus {} set {} (now {}) at index {} (now {})".format(stimulus.name, prev_value, value, prev_index, index))
                    prev_index = index
                    prev_value = value

            if index is not None:
                append(prev_index, prev_value, index - prev_index, chirp)
                # logging.debug("Finally set {} at {} for stimulus {}".f ormat(prev_value, prev_index, stimulus.name))

        # write to 0 after the last time the stimulus is ever used, but only if it wasn't already 0
        if index is not None and not is_audio and prev_value > 0:
            # if index is not None and not is_audio:
            append(index, 0, None, False)  # chirp=True or chirp=False should be fine

        seen = {}
        for ms, stim in sorted(stimulus_list):
            if isinstance(stim, str) or stim.name == "none":
                continue
            if (
                ms in seen and stim.intensity == seen[ms].intensity
            ):  # currently there's a small bug causing this
                logging.debug("{} and {} were set at time {}ms".format(stim, seen[ms], ms))
            elif ms in seen:  # but these are really bad and should be fixed in the assay
                logging.error("{} and {} were set at time {}ms".format(stim, seen[ms], ms))
            seen[ms] = stim
        stimulus_list = [(t, s) for t, s in stimulus_list if isinstance(s, str) or s.name != "none"]
        return stimulus_list
        # return list(sorted(stimulus_list, key=lambda t: 0, reverse=True))
        # return list(sorted(new_list, key=lambda x: x[0], reverse=True))


class ProtocolBlock(BaseBlock):
    def __init__(self, battery_object: int) -> None:
        """Fetches the battery, assays, and stimulus frames.
        Prepares Protocol.stimulus_list, which is a tuple of times (in milliseconds), stimulus names, and values.
        """
        import valarpy.model as model

        battery_object = model.Batteries.fetch(battery_object)
        super().__init__(battery_object)
        logging.debug("Setting battery to {} with length {}ms".format(battery_object.id, len(self)))
        self._pretty_print_assays()

    def _pretty_print_assays(self):
        import valarpy.model as model

        assay_positions = list(
            model.AssayPositions.select(model.AssayPositions, model.Assays)
            .join(model.Assays)
            .where(model.AssayPositions.battery_id == self.valar_obj.id)
            .order_by(model.AssayPositions.start)
        )

        def simpu(i):
            i = int(np.round(i / 1000))
            return str(timedelta(seconds=i))

        simplifier = BaseBlock._assay_name_simplifier()
        string = show_table(
            ["assay", "start", "length"],
            [
                [simplifier(p.assay.name), simpu(p.start), simpu(p.assay.length)]
                for p in assay_positions
            ],
        )
        logging.debug(string)
        print(string)

    def __str__(self) -> str:
        return "ProtocolBlock({})".format(self.valar_obj.name)

    def n_ms(self) -> int:
        return self.valar_obj.length

    def stimuli(self):
        import valarpy.model as model

        return set(
            model.Stimuli.select(
                model.Stimuli,
                model.StimulusFrames,
                model.Assays,
                model.AssayPositions,
                model.Batteries,
            )
            .join(model.StimulusFrames)
            .join(model.Assays)
            .join(model.AssayPositions)
            .join(model.Batteries)
            .where(model.Batteries.id == self.valar_obj.id)
        )

    def _stim_query(self, stimulus_id: int):
        import valarpy.model as model

        return (
            model.StimulusFrames.select(
                model.StimulusFrames,
                model.Assays,
                model.AssayPositions,
                model.Batteries,
                model.Stimuli,
            )
            .join(model.Assays)
            .join(model.AssayPositions)
            .join(model.Batteries)
            .switch(model.StimulusFrames)
            .join(model.Stimuli)
            .join(model.AudioFiles, model.JOIN.LEFT_OUTER)
            .where(model.Batteries.id == self.valar_obj.id)
            .where(model.Stimuli.id == stimulus_id)
            .order_by(model.AssayPositions.start)
        )

    def _start_of_frames(self, stimframes_obj) -> int:
        return stimframes_obj.assay.assaypositions.start


class AssayBlock(BaseBlock):
    def __init__(self, assay_id: int) -> None:
        """Fetches the battery, assays, and stimulus frames.
        Prepares Protocol.stimulus_list, which is a tuple of times (in milliseconds), stimulus names, and values.
        """
        import valarpy.model as model

        assay_obj = model.Assays.select().where(model.Assays.id == assay_id).first()
        if assay_obj is None:
            raise ValueError("No battery with ID {} exists in the database".format(assay_id))
        super().__init__(assay_obj)
        logging.info("Setting assay to {} with length {}ms".format(assay_id, len(self)))

    def __str__(self) -> str:
        return "AssayBlock({})".format(self.valar_obj.name)

    def n_ms(self) -> int:
        return self.valar_obj.length

    def stimuli(self):
        import valarpy.model as model

        return set(
            model.Stimuli.select(model.Stimuli, model.StimulusFrames, model.Assays)
            .join(model.StimulusFrames)
            .join(model.Assays)
            .where(model.Assays.id == self.valar_obj.id)
        )

    def _stim_query(self, stimulus_id: int):
        import valarpy.model as model

        return (
            model.StimulusFrames.select(model.StimulusFrames, model.Assays, model.Stimuli)
            .join(model.Assays)
            .switch(model.StimulusFrames)
            .join(model.Stimuli)
            .join(model.AudioFiles, model.JOIN.LEFT_OUTER)
            .where(model.Assays.id == self.valar_obj.id)
            .where(model.Stimuli.id == stimulus_id)
        )

    def _start_of_frames(self, stimframes_obj) -> int:
        return 0

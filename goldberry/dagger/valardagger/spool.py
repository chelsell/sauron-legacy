from __future__ import annotations
import abc
import logging
from typing import Sequence, List
from pathlib import Path

from prefect.tasks.shell import ShellTask

from valardagger.context import CONTEXT


logger = logging.getLogger(__package__)


class SpoolState:
    def __init__(self, on: bool):
        self._on = on

    def is_active(self) -> bool:
        return self._on

    def turn_on(self) -> None:
        self._on = True

    def turn_off(self) -> None:
        self._on = False


class Hash:
    def __init__(self, sub_hash: str):
        self._hash = sub_hash

    @property
    def hash(self) -> str:
        return self._hash

    def queue(self) -> None:
        pass

    def dequeue(self) -> None:
        pass

    def prioritize(self) -> None:
        pass

    def de_prioritize(self) -> None:
        pass

    def calculate(self, feature: str) -> None:
        pass


class Spool:
    def __init__(self):
        self._state = SpoolState(False)
        self._waiting: List[Hash] = []
        self._active: List[Hash] = []
        self._finished: List[Hash] = []

    def state(self) -> SpoolState:
        return self._state

    def hash(self, sub_hash: str) -> Hash:
        return Hash(sub_hash)

    @property
    def waiting(self) -> Sequence[Hash]:
        return self._waiting

    @property
    def active(self) -> Sequence[Hash]:
        return self._active

    @property
    def finished(self) -> Sequence[Hash]:
        return self._finished


__all__ = ["Spool"]

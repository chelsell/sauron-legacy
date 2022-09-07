from __future__ import annotations

import enum
from typing import Set, Union

from pocketutils.core.enums import CleverEnum


@enum.unique
class DataGeneration(CleverEnum):
    """
    A broad type of Sauron data, including hardware and software.
    Note that this does not capture framerate.
    Generally each Sauron only has a one or two generations.
    Types:
        - PIKE_MGH:          Saurons at MGH using Allied Vision Pike cameras. Sauron 0 (id=5).
        - PIKE_LEGACY:       Saurons running Pike cameras at UCSF using old MATLAB drivers. Saurons 1, 2, and 3.
        - PIKE_SAURONX:      Saurons running Pike cameras using SauronX. Saurons 1, 2, 3, and 4.
        - POINTGREY_ALPHA:   Saurons running PointGrey cameras without the new stimuli and sensors. Saurons 2 and 4.
        - POINTGREY:         Saurons running PointGrey cameras after integrating sensors and the white and UV LEDs. Saurons 10, 11, 12, and 13.

    """

    PIKE_MGH = enum.auto()
    PIKE_LEGACY = enum.auto()
    PIKE_SAURONX = enum.auto()
    POINTGREY_ALPHA = enum.auto()
    POINTGREY = enum.auto()

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def is_pike(self) -> bool:
        """ """
        return self in DataGeneration.pike_generations()

    def is_pointgrey(self) -> bool:
        """ """
        return self in DataGeneration.pointgrey_generations()

    def is_sauronx(self) -> bool:
        """ """
        return self in DataGeneration.sauronx_generations()

    def is_mgh(self) -> bool:
        """ """
        return self == DataGeneration.PIKE_MGH

    def is_ucsf(self) -> bool:
        """ """
        return self != DataGeneration.PIKE_MGH

    @classmethod
    def pike_generations(cls) -> Set[DataGeneration]:
        """ """
        return {
            DataGeneration.PIKE_MGH,
            DataGeneration.PIKE_LEGACY,
            DataGeneration.PIKE_SAURONX,
        }

    @classmethod
    def pointgrey_generations(cls) -> Set[DataGeneration]:
        """ """
        return {DataGeneration.POINTGREY_ALPHA, DataGeneration.POINTGREY}

    @classmethod
    def sauronx_generations(cls) -> Set[DataGeneration]:
        """ """
        return {
            DataGeneration.PIKE_SAURONX,
            DataGeneration.POINTGREY_ALPHA,
            DataGeneration.POINTGREY,
        }

    @classmethod
    def all_generations(cls) -> Set[DataGeneration]:
        """ """
        return set(DataGeneration.__members__.values())


__all__ = ["DataGeneration"]

"""
Visualization code.
Can depend on core, calc, and model.
"""
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from sauronlab.core.core_imports import *


class CakeComponent(metaclass=abc.ABCMeta):
    """ """

    pass


class CakeLayer(metaclass=abc.ABCMeta):
    """ """

    @abcd.abstractmethod
    def plot(self, **kwargs) -> Axes:
        """


        Args:
            **kwargs:

        Returns:

        """
        raise NotImplementedError()


__all__ = ["CakeComponent", "CakeLayer", "plt"]

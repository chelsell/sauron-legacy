"""

"""
import logging
import sys

import IPython
import matplotlib.pyplot as plt
from IPython.display import HTML, Markdown, display
from matplotlib.figure import Figure
from pandas.plotting import register_matplotlib_converters
from pocketutils.misc.j import J, JFonts
from pocketutils.misc.magic_template import MagicTemplate

from sauronlab.core.core_imports import *
from sauronlab.startup import *

(
    MagicTemplate.from_path(sauronlab_env.jupyter_template, prefix="${", suffix="}")
    .add_version(sauronlab_version)
    .add_datetime()
    .add("username", sauronlab_env.username)
    .add("author", sauronlab_env.username.title())
    .add("config", sauronlab_env.config_file)
).register_magic("sauronlab")


def plot_all(it: Iterable[Tup[str, Figure]]) -> None:
    for name, figure in it:
        print(f"Plotting {name}")
        plt.show(figure)


def save_all(it: Iterable[Tup[str, Figure]], path: PathLike) -> None:
    # noinspection PyTypeChecker
    FigureTools.save(it, path=path)


register_matplotlib_converters()

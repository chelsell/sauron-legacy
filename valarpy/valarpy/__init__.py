"""
Project metadata and convenience functions.
"""

import logging
from contextlib import contextmanager
from importlib.metadata import PackageNotFoundError
from importlib.metadata import metadata as __load
from pathlib import Path
from typing import Generator, List, Mapping, Union

import peewee

from valarpy.connection import Valar
from valarpy.micromodels import (
    ValarLookupError,
    ValarTableTypeError,
    UnsupportedOperationError,
    WriteNotEnabledError,
)

pkg = Path(__file__).absolute().parent.name
logger = logging.getLogger(pkg)
_metadata = None
try:
    _metadata = __load(Path(__file__).absolute().parent.name)
    __status__ = "Development"
    __copyright__ = "Copyright 2016–2021"
    __date__ = "2020-12-29"
    __uri__ = _metadata["home-page"]
    __title__ = _metadata["name"]
    __summary__ = _metadata["summary"]
    __license__ = _metadata["license"]
    __version__ = _metadata["version"]
    __author__ = _metadata["author"]
    __maintainer__ = _metadata["maintainer"]
    __contact__ = _metadata["maintainer"]
except PackageNotFoundError:  # pragma: no cover
    logger.error(f"Could not load package metadata for {pkg}. Is it installed?")


def new_model():
    """
    Shorthand for importing model.
    You should have a connection open.

    Returns:
        The ``model`` module
    """
    from valarpy import model

    return model


@contextmanager
def opened(
    config: Union[
        None, str, Path, List[Union[str, Path, None]], Mapping[str, Union[str, int]]
    ] = None
):
    """
    Context manager. Opens a connection and returns the model.
    Closes the connection when the generator exits.

    Args:
        config: Passed to ``Valar.__init__``

    Yields:
        The ``model`` module, with an attached ``.conn`` of type ``Valar``
    """
    with Valar(config) as valar:
        from valarpy import model

        model.conn = valar
        yield model


def valarpy_info() -> Generator[str, None, None]:
    """
    Gets lines describing valarpy metadata and database row counts.
    Useful for verifying that the schema matches the valarpy model,
    and for printing info.

    Yields:
        Lines of free text

    Raises:
        InterfaceError: On some connection and schema mismatch errors
    """
    if _metadata is not None:
        yield "{} (v{})".format(_metadata["name"], _metadata["version"])
    else:
        yield "Unknown project info"
    yield "Connecting..."
    with opened(Valar.get_preferred_paths()) as m:
        yield "Connected."
        yield ""
        yield "Table                       N Rows"
        yield "----------------------------------"
        for sub in m.BaseModel.__subclasses__():
            count = sub.select(peewee.fn.COUNT(sub.id).alias("count")).first()
            yield f"{sub.__name__:<25} = {count.count}"
        yield "----------------------------------"
        yield ""
    yield "All valarpy queries succeeded."


if __name__ == "__main__":  # pragma: no cover
    for line in valarpy_info():
        print(line)


__all__ = ["Valar", "new_model", "opened", "opened", "valarpy_info"]

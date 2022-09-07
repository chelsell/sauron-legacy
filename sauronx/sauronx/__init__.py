"""
Metadata for this project.
"""

import logging
from importlib.metadata import PackageNotFoundError
from importlib.metadata import metadata as __load
from pathlib import Path

pkg = Path(__file__).absolute().parent.name
logger = logging.getLogger(pkg)
__metadata = None
try:
    __metadata = __load(Path(__file__).absolute().parent.name)
    __status__ = "Development"
    __copyright__ = "Copyright 2016–2020"
    __date__ = "2020-09-10"
    __uri__ = __metadata["home-page"]
    __title__ = __metadata["name"]
    __summary__ = __metadata["summary"]
    __license__ = __metadata["license"]
    __version__ = __metadata["version"]
    __author__ = __metadata["author"]
    __maintainer__ = __metadata["maintainer"]
    __contact__ = __metadata["maintainer"]
except PackageNotFoundError:  # pragma: no cover
    logger.error(f"Could not load package metadata for {pkg}. Is it installed?")


if __name__ == "__main__":  # pragma: no cover
    if __metadata is not None:
        print(f"{pkg} (v{__metadata['version']})")
    else:
        print("Unknown project info")

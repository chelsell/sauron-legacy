import tempfile
import shutil
from pathlib import Path
from typing import Union
from contextlib import contextmanager
from datetime import datetime


def resource(*nodes: Union[Path, str]) -> Path:
    """Gets a path of a test resource file under resources/."""
    return Path(Path(__file__).parent, "resources", *nodes)


@contextmanager
def new_tmp_dir() -> Path:
    path = Path("tmptestdata") / datetime.now().strftime("%Y%m%d.%H%M%S")
    if path.exists():
        shutil.rmtree(str(path))
    path.mkdir(parents=True)
    yield path
    if path.exists():
        shutil.rmtree(str(path))

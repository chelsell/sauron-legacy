# this could depend on internal_core_imports, but let's keep it light
import os
from pathlib import Path

import decorateme as abcd
from valarpy import Valar as __Valar


@abcd.auto_singleton
class Valar(__Valar):
    """
    A singleton database connection for sauronlab.
    """

    def __init__(self):
        config_path = os.environ.get(
            "VALARPY_CONFIG", Path.home() / ".sauronlab" / "connection.json"
        )
        super().__init__(config_path)
        super().open()


VALAR = Valar()
# noinspection PyUnresolvedReferences
from valarpy.model import *

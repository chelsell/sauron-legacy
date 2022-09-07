import os
from pathlib import Path

import valarpy
from pocketutils.core.dot_dict import NestedDotDict


class Context:
    def __init__(self):
        path = os.environ.get("VALARDAGGER_CONFIG", Path("/etc", "valardagger.toml"))
        self.config = NestedDotDict.read_toml(path)
        self.valar = valarpy.Valar()
        self.model = None

    def __enter__(self):
        self.valar.open()
        self.model = valarpy.new_model()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.valar.close()

    def archive_path(self, submission_hash: str) -> Path:
        pass

CONTEXT = Context()

__all__ = ["CONTEXT"]

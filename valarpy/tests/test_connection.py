import json
import os
from pathlib import Path

import pytest

from valarpy import *

CONFIG_PATH = Path(__file__).parent / "resources" / "connection.json"
CONFIG_DATA = json.loads(CONFIG_PATH.read_text(encoding="utf8"))


class TestModel:
    def test_reconnect(self):
        with Valar(CONFIG_PATH) as valar:
            from valarpy.model import Refs

            assert list(Refs) is not None
            valar.reconnect()
            assert list(Refs) is not None

    def test_config_dict(self):
        with Valar(CONFIG_DATA):
            from valarpy.model import Refs

            list(Refs.select())

    def test_config_path_env(self):
        popped = None
        try:
            # just in case it's needed elsewhere, let's save the current VALARPY_CONFIG
            if "VALARPY_CONFIG" in os.environ:
                popped = os.environ.pop("VALARPY_CONFIG")
            # test using environment variable
            with pytest.raises(FileNotFoundError):
                with Valar():
                    from valarpy.model import Refs

                    list(Refs.select())
            os.environ["VALARPY_CONFIG"] = str("asd346erfdgawq046j54e4y")
            with pytest.raises(FileNotFoundError):
                with Valar():
                    from valarpy.model import Refs

                    list(Refs.select())
            os.environ["VALARPY_CONFIG"] = str(CONFIG_PATH)
            with Valar():
                from valarpy.model import Refs

                assert list(Refs) is not None
            # test with passing directly
            os.environ.pop("VALARPY_CONFIG")
            with Valar(CONFIG_PATH):
                from valarpy.model import Refs

                assert list(Refs) is not None
            with Valar([Path("asd346erfdgawq046j54e4y"), CONFIG_PATH]):
                from valarpy.model import Refs

                assert list(Refs) is not None
        finally:
            if popped is not None:
                os.environ["VALARPY_CONFIG"] = popped


if __name__ == ["__main__"]:
    pytest.main()

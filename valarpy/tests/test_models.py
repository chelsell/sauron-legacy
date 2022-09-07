from pathlib import Path

import pytest

from valarpy import Valar


@pytest.fixture(scope="module")
def setup():
    with Valar(Path(__file__).parent / "resources" / "connection.json"):
        yield


class TestModel:
    def test_all_models(self, setup):
        import valarpy.model as m

        for sub in m.BaseModel.__subclasses__():
            assert list(sub.select()) is not None


if __name__ == ["__main__"]:
    pytest.main()

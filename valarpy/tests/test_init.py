from pathlib import Path

import pytest

import valarpy

PATH = Path(__file__).parent / "resources" / "connection.json"


class TestModel:
    def test_fancy_import(self):
        with valarpy.Valar(PATH):
            model = valarpy.new_model()
            assert len(list(model.Refs.select())) == 1

    def test_fancy_open_read(self):
        import valarpy

        with valarpy.opened(PATH) as model:
            assert len(list(model.Refs.select())) == 1

    def test_fancy_open_write(self):
        import valarpy

        with valarpy.opened(PATH) as model:
            assert len(list(model.Refs.select())) == 1


if __name__ == ["__main__"]:
    pytest.main()

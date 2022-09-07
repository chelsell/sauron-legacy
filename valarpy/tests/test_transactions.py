import json
from pathlib import Path

import pytest

from valarpy import opened, opened

CONFIG_PATH = Path(__file__).parent / "resources" / "connection.json"
CONFIG_DATA = json.loads(CONFIG_PATH.read_text(encoding="utf8"))


class TestModel:

    """

    def test_atomic_trans(self):
        with opened(CONFIG_DATA) as model:
            valar = model.conn
            valar.backend.enable_write()
            from valarpy.model import Refs
            Refs.delete().where(Refs.name << {"myfakeref", "fixedrefname"}).execute()
            assert "myfakeref" not in {r.name for r in Refs.select()}
            with valar.atomic():
                Refs.create(name="myfakeref")
            # transaction should commit
            assert "myfakeref" in {r.name for r in Refs.select()}

    def test_rollback_trans(self):
        with opened(CONFIG_DATA) as model:
            valar = model.conn
            valar.backend.enable_write()
            from valarpy.model import Refs
            Refs.delete().where(Refs.name << {"myfakeref", "fixedrefname"}).execute()
            assert "myfakeref" not in {r.name for r in Refs.select()}
            with valar.rolling_back():
                Refs.create(name="myfakeref")
            # transaction should commit
            assert "myfakeref" not in {r.name for r in Refs.select()}

    def test_atomic_trans_fail(self):
        with opened(CONFIG_DATA) as model:
            valar = model.conn
            valar.backend.enable_write()
            from valarpy.model import Refs
            Refs.delete().where(Refs.name << {"test_atomic_trans_fail"}).execute()
            assert "test_atomic_trans_fail" not in {r.name for r in Refs.select()}
            try:
                with valar.atomic() as t:
                    Refs.create(name="test_atomic_trans_fail")
                    assert "test_atomic_trans_fail" in {r.name for r in Refs.select()}
                    raise ValueError("nope")
            except ValueError:
                pass
            # it should have rolled back
            assert "test_atomic_trans_fail" not in {r.name for r in Refs.select()}

    def test_atomic_nested(self):
        with opened(CONFIG_DATA) as model:
            valar = model.conn
            valar.backend.enable_write()
            from valarpy.model import Refs
            Refs.delete().where(Refs.name << {"myfakeref", "fixedrefname"}).execute()
            with valar.atomic():
                Refs.create(name="myfakeref")
                with valar.atomic():
                    Refs.update(dict(name="fixedrefname")).where(Refs.name == "myfakeref").execute()
            # transaction should commit
            assert "myfakeref" not in {r.name for r in Refs.select()}
            assert "fixedrefname" in {r.name for r in Refs.select()}

    def test_atomic_nested_fail_on_checkpoint(self):
        with opened(CONFIG_DATA) as model:
            valar = model.conn
            from valarpy.model import Refs
            Refs.delete().where(Refs.name << {"myfakeref", "fixedrefname"}).execute()
            with valar.atomic():
                try:
                    Refs.create(name="myfakeref")
                    with valar.atomic():
                        Refs.update(dict(name="fixedrefname")).where(Refs.name == "myfakeref").execute()
                        raise ValueError("nope")
                except ValueError:
                    pass  # catching outside of savepoint but inside transaction
            # it should have rolled back the savepoint BUT NOT transaction
        with opened(CONFIG_DATA):
            assert "myfakeref" in {r.name for r in Refs.select()}
            assert "fixedrefname" not in {r.name for r in Refs.select()}

    """


if __name__ == ["__main__"]:
    pytest.main()

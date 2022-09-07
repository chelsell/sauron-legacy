import json
from pathlib import Path

import pytest

from valarpy import opened, WriteNotEnabledError, UnsupportedOperationError

CONFIG_PATH = Path(__file__).parent / "resources" / "connection.json"
CONFIG_DATA = json.loads(CONFIG_PATH.read_text(encoding="utf8"))


class TestModel:
    def test_cannot_truncate(self):
        with opened(CONFIG_DATA) as model:
            model.conn.backend.enable_write()
            from valarpy.model import Refs

            try:
                with pytest.raises(UnsupportedOperationError):
                    Refs.truncate_table()
                with pytest.raises(UnsupportedOperationError):
                    Refs.drop_table()
            finally:
                try:
                    model.conn.backend.disable_write()
                except Exception:  # nosec
                    pass

    def test_write_enable_disable(self):
        key = "test_write_enable_disable"
        with opened(CONFIG_DATA) as model:
            backend = model.conn.backend
            from valarpy.model import Refs

            try:
                # first, write is disabled
                ref = Refs(name=key)
                with pytest.raises(WriteNotEnabledError):
                    ref.save()
                assert key not in {r.name for r in Refs.select()}
                # now enable write
                backend.enable_write()
                # saving should work
                ref.save()
                assert key in {r.name for r in Refs.select()}
                # now that we have a row, let's delete it
                # but first fail: disable write
                backend.disable_write()
                with pytest.raises(WriteNotEnabledError):
                    ref.delete_instance()
                assert key in {r.name for r in Refs.select()}
                # we didn't delete the row because it errored
                # now re-enable write and delete the row
                backend.enable_write()
                ref.delete_instance()
                assert key not in {r.name for r in Refs.select()}
            finally:
                try:
                    backend.enable_write()
                    Refs.delete().where(Refs.name == key).execute()
                except Exception:  # nosec
                    pass
                finally:
                    try:
                        backend.disable_write()
                    except Exception:  # nosec
                        pass


if __name__ == ["__main__"]:
    pytest.main()

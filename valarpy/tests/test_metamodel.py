from pathlib import Path

import pytest

from valarpy import Valar


@pytest.fixture(scope="module")
def setup():
    with Valar(Path(__file__).parent / "resources" / "connection.json"):
        yield


class TestMetamodel:
    def test_create(self, setup):
        from valarpy.model import Users

        user = Users(username="hi", first_name="Hello", last_name="Hi")
        assert user.id is None

    def test_get_data(self, setup):
        from valarpy.model import Refs

        assert Refs(id=1, name="hi").get_data() == dict(id=1, name="hi")

    def test_query(self, setup):
        from valarpy.model import Refs

        refs = list(Refs.select())
        assert [ref.name for ref in refs] == ["ref_four"]

    def test_fetch(self, setup):
        from valarpy.model import Refs, Users, ValarLookupError, ValarTableTypeError

        ref = Refs.fetch("ref_four")
        assert ref is not None
        assert ref.name == "ref_four"
        with pytest.raises(ValarLookupError):
            Refs.fetch("ref_three")
        with pytest.raises(ValarTableTypeError):
            Refs.fetch(Users(id=1))

    def test_fetch_or_none(self, setup):
        from valarpy.model import Refs, Users, ValarTableTypeError

        assert Refs.fetch_or_none(Refs(id=1)).id == 1
        with pytest.raises(ValarTableTypeError):
            Refs.fetch_or_none(Users(id=1))
        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            Refs.fetch_or_none(lambda x: x)
        ref = Refs.fetch_or_none("ref_four")
        assert ref is not None
        assert ref.name == "ref_four"
        assert Refs.fetch_or_none("non") is None

    def test_fetch_all(self, setup):
        from valarpy.model import Refs, ValarLookupError

        dat = Refs.fetch_all(["ref_four"])
        assert [ref.name for ref in dat] == ["ref_four"]
        with pytest.raises(ValarLookupError):
            Refs.fetch_all(["ref_four", "ref_three"])

    def test_fetch_all_or_none(self, setup):
        from valarpy.model import Refs, Users, ValarTableTypeError

        assert Refs.fetch_all_or_none([]) == []
        assert Refs.fetch_all_or_none(["nope"]) == [None]
        dat = Refs.fetch_all_or_none([4, 20])
        assert [getattr(ref, "name", None) for ref in dat] == ["ref_four", None]
        dat = Refs.fetch_all_or_none(["ref_four", "non"])
        assert [getattr(ref, "id", None) for ref in dat] == [4, None]
        # combined, with duplicates
        dat = Refs.fetch_all_or_none(["ref_four", "non", 4, "nope"])
        assert [getattr(ref, "id", None) for ref in dat] == [4, None, 4, None]
        # ID, string, and instance, with duplicates
        dat = Refs.fetch_all_or_none(["ref_four", "non", 4, Refs.fetch(4)])
        assert [getattr(ref, "id", None) for ref in dat] == [4, None, 4, 4]
        with pytest.raises(ValarTableTypeError):
            Refs.fetch_all_or_none([Users(id=1)])
        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            Refs.fetch_all_or_none([lambda x: x])
        # with a join fn
        dat = Refs.fetch_all_or_none(["ref_four"], join_fn=lambda s: s)
        assert [getattr(ref, "id", None) for ref in dat] == [4]
        dat = Refs.fetch_all_or_none([Refs.fetch(4)], join_fn=lambda s: s)
        assert [getattr(ref, "id", None) for ref in dat] == [4]
        # TODO
        # dat = Refs.fetch_all_or_none(["ref_four", "non", 4, Refs.fetch(4)], join_fn=lambda s: s.join(Refs))
        # assert [getattr(ref, "id", None) for ref in dat] == [4, None, 4, 4]

    def test_fetch_like(self, setup):
        from valarpy.model import Refs

        assert Refs.fetch_or_none("four") is None
        ref = Refs.fetch_or_none("ref_four", like=True)
        assert ref is not None and ref.id == 4
        ref = Refs.fetch_or_none("four", like=True)
        assert ref is not None and ref.id == 4

    def test_fetch_regex(self, setup):
        from valarpy.model import Refs

        assert Refs.fetch_or_none(".*") is None
        assert Refs.fetch_or_none(".*", like=True) is None
        ref = Refs.fetch_or_none(".*", regex=True)
        assert ref is not None and ref.id == 4

    def test_fetch_to_query(self, setup):
        from valarpy.model import Refs

        query = Refs.select().where(Refs.fetch_to_query(4)[0])
        assert [getattr(ref, "id", None) for ref in query] == [4]
        query = Refs.select().where(Refs.fetch_to_query([4, 4])[0])
        assert [getattr(ref, "id", None) for ref in query] == [4]
        query = Refs.select().where(Refs.fetch_to_query(Refs.id > 0)[0])
        assert [getattr(ref, "id", None) for ref in query] == [4]
        query = Refs.select().where(Refs.fetch_to_query([Refs.id > 0])[0])
        assert [getattr(ref, "id", None) for ref in query] == [4]
        query = Refs.select().where(Refs.fetch_to_query([Refs.id > 0, Refs.id > 1])[0])
        assert [getattr(ref, "id", None) for ref in query] == [4]
        query = Refs.select().where(Refs.fetch_to_query([Refs.id > 10])[0])
        assert [getattr(ref, "id", None) for ref in query] == []
        query = Refs.select().where(Refs.fetch_to_query(Refs.fetch(4)))
        assert [getattr(ref, "id", None) for ref in query] == [4]
        query = Refs.select().where(Refs.fetch_to_query(4))
        assert [getattr(ref, "id", None) for ref in query] == [4]
        # test AND
        wheres = Refs.fetch_to_query([Refs.id > 0, Refs.id > 10])
        query = Refs.select()
        for where in wheres:
            query = query.where(where)
        assert [getattr(ref, "id", None) for ref in query] == []
        # test bad queries
        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            Refs.fetch_to_query([lambda x: x])
        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            Refs.fetch_to_query(lambda x: x)

    def test_list_where(self, setup):
        from valarpy.model import Refs

        refs = Refs.list_where(Refs.id > 0)
        assert [getattr(ref, "id", None) for ref in refs] == [4]
        # noinspection PyTypeChecker
        refs = Refs.list_where(name="ref_four")
        assert [getattr(ref, "id", None) for ref in refs] == [4]

    def test_description(self, setup):
        from valarpy.model import Features

        df = Features.get_desc()
        assert list(df.columns.values) == [
            "name",
            "type",
            "nullable",
            "choices",
            "primary",
            "unique",
            "constraints",
        ]
        assert len(df) == 6
        assert list(df["name"].values) == [
            "id",
            "created",
            "data_type",
            "description",
            "dimensions",
            "name",
        ]
        s = Features.get_desc_list()
        assert len(s) == 6
        assert s[0] == {
            "choices": None,
            "constraints": 0,
            "name": "id",
            "nullable": False,
            "primary": True,
            "type": "AUTO",
            "unique": False,
        }

    def test_schema_lines(self, setup):
        from valarpy.model import Features

        lines = Features.get_schema().split("\n")
        assert len(lines) == 6

    def test_sstring(self, setup):

        from valarpy.model import ControlTypes

        control = ControlTypes(id=1)
        assert control.sstring == "ct1"


if __name__ == ["__main__"]:
    pytest.main()

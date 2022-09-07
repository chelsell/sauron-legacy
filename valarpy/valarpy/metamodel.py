from __future__ import annotations
from collections import defaultdict
from numbers import Integral
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Union

import pandas as pd
import peewee
from peewee import *

from valarpy import (
    ValarLookupError,
    ValarTableTypeError,
    UnsupportedOperationError,
    WriteNotEnabledError,
)
from valarpy.connection import GlobalConnection

database = GlobalConnection._peewee_database


# noinspection PyProtectedMember
class EnumField(peewee._StringField):  # pragma: no cover
    """
    A MySQL ``ENUM`` field type.
    """

    field_type = "ENUM"

    def __init__(self, max_length=255, *args, **kwargs):
        self.max_length = max_length
        super().__init__(*args, **kwargs)

    def get_modifiers(self):
        return self.max_length and [self.max_length] or None


class BinaryField(BlobField):  # pragma: no cover
    """
    A MySQL constant-width ``BINARY`` field type.
    """

    field_type = "BINARY"

    def __init__(self, max_length=255, *args, **kwargs):
        super(BinaryField, self).__init__(args, kwargs)
        self.max_length = max_length


class UnknownField(object):  # pragma: no cover
    """
    A field type that was not recognized.
    """

    def __init__(self, *_, **__):
        pass


class TableDescriptionFrame(pd.DataFrame):
    """
    A Pandas DataFrame subclass that contains the columns::

        - keys name (str)
        - type (str)
        - length (int or None)
        - nullable (bool)
        - choices (set or list)
        - primary (bool)
        - unique (bool)
        - constraints (list of constraint objects)
    """

    pass


class BaseModel(Model):
    """
    A table model in Valar through Valarpy and peewee.
    Provides functions in additional to the normal peewee functions.
    """

    class Meta:
        database = database

    def save(self, force_insert=False, only=None) -> Union[bool, int]:
        self._ensure_write()
        return super().save(force_insert, only)

    def delete_instance(self, recursive=False, delete_nullable=False) -> Any:
        self._ensure_write()
        return super().delete_instance(recursive, delete_nullable)

    @classmethod
    def update(cls, __data=None, **update) -> peewee.ModelUpdate:
        cls._ensure_write()
        return super().update(__data, **update)

    @classmethod
    def insert(cls, __data=None, **insert) -> peewee.ModelInsert:
        cls._ensure_write()
        return super().insert(__data, **insert)

    @classmethod
    def insert_many(cls, rows, fields=None) -> peewee.ModelInsert:
        cls._ensure_write()
        return super().insert_many(rows, fields)

    @classmethod
    def insert_from(cls, query, fields) -> peewee.ModelInsert:
        cls._ensure_write()
        return super().insert_from(query, fields)

    @classmethod
    def replace(cls, __data=None, **insert) -> Optional[Any]:
        cls._ensure_write()
        return super().replace(__data, **insert)

    @classmethod
    def replace_many(cls, rows, fields=None) -> Optional[Any]:
        cls._ensure_write()
        return super().replace_many(rows, fields)

    @classmethod
    def raw(cls, rows, fields=None) -> Optional[Any]:
        raise UnsupportedOperationError(f"Cannot get raw {cls}: not supported")

    @classmethod
    def delete(cls) -> peewee.ModelDelete:
        cls._ensure_write()
        return super().delete()

    @classmethod
    def create(cls, **query) -> BaseModel:
        cls._ensure_write()
        return super().create(**query)

    @classmethod
    def bulk_create(cls, model_list, batch_size=None) -> Optional[Any]:
        cls._ensure_write()
        return super().bulk_create(model_list, batch_size)

    @classmethod
    def bulk_update(cls, model_list, fields, batch_size=None) -> int:
        cls._ensure_write()
        return super().bulk_update(model_list, fields, batch_size)

    @classmethod
    def set_by_id(cls, key, value) -> Any:
        cls._ensure_write()
        return super().set_by_id(key, value)

    @classmethod
    def delete_by_id(cls, pk) -> Any:
        cls._ensure_write()
        return super().delete_by_id(pk)

    @classmethod
    def get_or_create(cls, **kwargs) -> BaseModel:
        cls._ensure_write()
        return super().get_or_create(**kwargs)

    @classmethod
    def drop_table(cls, safe=True, drop_sequences=True, **options) -> None:
        raise UnsupportedOperationError(f"Cannot drop {cls}: not supported")

    @classmethod
    def truncate_table(cls, **options) -> None:
        raise UnsupportedOperationError(f"Cannot truncate {cls}: not supported")

    @classmethod
    def _ensure_write(cls):
        if not GlobalConnection._write_enabled:
            raise WriteNotEnabledError()

    def get_data(self) -> Dict[str, Any]:
        """
        Gets a dict of all the fields.

        Examples:
            Users.get(Users.id == 1).get_data()  # {'id': 2, 'username': 'john', ...}

        Returns:
            The value of every field (column value)
        """
        return self.__data__

    @property
    def sstring(self) -> str:
        """
        Gets a short string of the ID. This can be overridden.

        Returns:
            A string like ``s12``
        """
        return "".join([c for c in self.__class__.__name__ if c.isupper()]).lower() + str(self.id)

    @property
    def _data(self) -> Dict[str, Any]:  # pragma: no cover
        """
        See ``get_data``.
        """
        # for compatibility with peewee version 2 code
        return self.__data__

    @classmethod
    def get_desc_list(cls) -> List[Dict[str, str]]:
        """
        Gets info about the columns as a list of dicts.

        Returns:
            list of dicts:
                A list the columns in this table, where each is a dictionary of::

                  - keys name (str)
                  - type (str)
                  - nullable (bool)
                  - choices (set or list)
                  - primary (bool)
                  - unique (bool)
                  - constraints (list of constraint objects)
        """
        return cls.__description()

    @classmethod
    def get_desc(cls) -> TableDescriptionFrame:
        """
        Gets a description of this table as a Pandas DataFrame.

        Examples:
            Users.get_desc()

        Returns:
            A DataFrame:
                A TableDescriptionFrame (Pandas DataFrame subclass) of the columns::

                    - keys name (str)
                    - type (str)
                    - length (int or None)
                    - nullable (bool)
                    - choices (set or list)
                    - primary (bool)
                    - unique (bool)
                    - constraints (list of constraint objects)
        """

        def _cfirst(dataframe: pd.DataFrame, col_seq) -> pd.DataFrame:
            if len(dataframe) == 0:  # will break otherwise
                return dataframe
            else:
                return dataframe[col_seq + [c for c in dataframe.columns if c not in col_seq]]

        # noinspection PyTypeChecker
        df = pd.DataFrame.from_dict(cls.__description())
        return TableDescriptionFrame(
            _cfirst(df, ["name", "type", "nullable", "choices", "primary", "unique"])
        )

    @classmethod
    def get_schema(cls) -> str:
        """
        Gets the approximate schema string.

        Returns:
            A string that is **approximately** the text returned by the SQL ``SHOW CREATE TABLE tablename``
        """
        return ",\n".join(
            [
                " ".join(
                    [
                        d["name"],
                        d["type"] + (str(d["choices"]) if d["choices"] is not None else ""),
                        ("NULL" if d["nullable"] else "NOT NULL"),
                        ("PRIMARY KEY" if d["primary"] else ("UNIQUE" if d["unique"] else "")),
                    ]
                ).rstrip()
                for d in cls.__description()
            ]
        )

    @classmethod
    def __description(cls) -> List[Dict[str, str]]:  # pragma: no cover
        return [
            {
                "name": v.name,
                "type": v.field_type,
                "nullable": v.null,
                "choices": v.choices if hasattr(v, "choices") else None,
                "primary": v.primary_key,
                "unique": v.unique,
                "constraints": 0 if v.constraints is None else len(v.constraints),
            }
            for k, v in cls._meta.fields.items()
        ]

    @classmethod
    def list_where(cls, *wheres: Sequence[peewee.Expression], **values: Mapping[str, Any]):
        """
        Runs a simple query and returns a list.

        Args:
            wheres: List of Peewee WHERE expressions (like ``Users.id==1``) to be joined by AND
            values: Explicit values (like ``id=1``), also joined by AND

        Returns:
            The table rows in a list
        """
        query = cls.select()
        for where in wheres:
            query = query.where(where)
        for name, value in values.items():
            query = query.where(getattr(cls, name) == value)
        return list(query)

    @classmethod
    def fetch_or_none(
        cls, thing: Union[Integral, str, peewee.Model], like: bool = False, regex: bool = False
    ) -> Optional[peewee.Model]:
        """
        Gets the first (which is unique) match of the row by:
            - instance of this class (just returns it)
            - ``id`` columns (if ``thing`` is an integer-like type)
            - any of this class's unique string columns;
               more specifically, a column that is marked in SQL as both (``VARCHAR``, ``CHAR``, or ``ENUM``)
               and ``UNIQUE``

        Also see ``fetch``, which raises an error if then row was not found.

        Examples:
            # assuming John has ID 2
            user = Users.fetch('john')
            print(user)  # Users(2)

        Args:
            thing: A string, int that
            like: Use a LIKE expression and wrap in % %
            regex: Treat ``thing`` as a regex pattern

        Returns:
            The Peewee row instance that was found OR None if it does not exist

        Raises:
            ValarTableTypeError: If ``thing`` is an instance of BaseModel of the wrong type (not this class)
            TypeError: If ``thing`` was not a str, int-like, or a ``BaseModel``
        """
        if isinstance(thing, cls):
            return thing
        elif isinstance(thing, peewee.Model):
            raise ValarTableTypeError(
                f"Fetching a {thing.__class__.__name__} on class {cls.__name__}"
            )
        elif isinstance(thing, Integral) or isinstance(thing, float):
            # noinspection PyUnresolvedReferences
            return cls.get_or_none(cls.id == int(thing))
        elif isinstance(thing, str) and len(cls.__indexing_cols()) > 0:
            return cls.get_or_none(cls._build_or_query([thing], like=like, regex=regex))
        else:
            raise TypeError(
                f"Fetching with unknown type {thing.__class__.__name__} on class {cls.__name__}"
            )

    @classmethod
    def fetch(
        cls, thing: Union[Integral, str, peewee.Model], like: bool = False, regex: bool = False
    ) -> peewee.Model:
        """
        Gets the first (which is unique) match of the row by:
            - instance of this class (just returns it)
            - ``id`` columns (if ``thing`` is an integer-like type
            - any of this class's unique string columns;
              more specifically, a column that is marked in SQL as both (``VARCHAR``, ``CHAR``, or ``ENUM``)
              and ``UNIQUE``

        Also see ``fetch_or_none``, which returns None if the row was not found.

        Examples:
            # assuming John has ID 2
            user = Users.fetch('john')
            print(user)  # Users(2)

        Args:
            thing: A string, int that
            like: Use a LIKE expression and wrap in % %
            regex: Treat ``thing`` as a regex pattern

        Returns:
            The matching Peewee row instance

        Raises:
            ValarLookupError: If the row was not found
            ValarTableTypeError: If ``thing`` is an instance of BaseModel of the wrong type (not this class)
            TypeError: If ``thing`` was not a str, int-like, or a BaseModel
        """
        found = cls.fetch_or_none(thing, like=like, regex=regex)
        if found is None:
            raise ValarLookupError(f"Could not find {thing} in {cls}")
        return found

    @classmethod
    def fetch_all(
        cls, things: Iterable[Union[Integral, str, peewee.Model]]
    ) -> Sequence[peewee.Model]:
        """
        Fetches rows corresponding to ``things`` from their instances, IDs, or values from unique columns.
        See ``fetch`` for full information.
        Also see ``fetch_all_or_none`` for a similar function.
        This method is preferrable to calling ``fetch`` repeatedly because it minimizes the number of queries.
        Specifically, it will perform 0, 1, or 2 queries depending on the passed types::

            - If only instances are passed, it just returns them (0 queries)
            - If only IDs or only string values are passed, it performs 1 query
            - If both IDs and string values are passed, it performs 2 queries

        Examples:
            # assuming John has ID 2 and Alex has user ID 14
            users = Users.fetch_all(['john', 14, 'john', Users.get(Users.id == 2)])
            print(users)  # [Users(2), Users(14), Users(2), Users(2)]

        Returns:
            A sequence of the rows found, in the same order as they were passed

        Raises:
            ValarLookupError: If any of the elements of ``things`` was not found
            ValarTableTypeError: If an instance of a BaseModel of the wrong type (not this class) was passed
            TypeError: If the type of an element was otherwise invalid (not str, BaseModel, or int-like)
        """

        def _x(thing):  # pragma: no cover
            if thing is None:
                raise ValarLookupError(f"Could not find {thing} in {cls}")
            return thing

        return [_x(thing) for thing in cls.fetch_all_or_none(things)]

    @classmethod
    def fetch_all_or_none(
        cls,
        things: Iterable[Union[Integral, str, peewee.Model]],
        join_fn: Optional[Callable[[peewee.Expression], peewee.Expression]] = None,
    ) -> Iterable[peewee.Model]:
        """
        Fetches rows corresponding to ``things`` from their instances, IDs, or values from unique columns.
        See ``fetch`` for full information.
        Also see ``fetch_all`` for a similar function.
        This method is preferrable to calling ``fetch`` repeatedly because it minimizes the number of queries.
        Specifically, it will perform 0, 1, or 2 queries depending on the passed types::

            - If only instances are passed, it just returns them (0 queries)
            - If only IDs or only string values are passed, it performs 1 query
            - If both IDs and string values are passed, it performs 2 queries

        Examples:
            # assuming John has ID 2 and Alex has user ID 14
            users = Users.fetch_all_or_none(['john', 14, 'john', Users.get(Users.id == 2)])
            print(users)  # [Users(2), Users(14), Users(2), Users(2)]

        Returns:
            A sequence of the rows found, or None if they were not found; in the same order as they were passed

        Raises:
            ValarTableTypeError: If an instance of a BaseModel of the wrong type (not this class) was passed
            TypeError: If the type of an element was otherwise invalid (not str, BaseModel, or int-like)
        """
        # modify arguments
        things = list(things)
        has_join_fn = join_fn is not None
        if join_fn is None:

            def join_fn(s):
                return s

        # handle errors
        bad_models = [
            isinstance(thing, peewee.Model) and not isinstance(thing, cls) for thing in things
        ]
        if any(bad_models):
            raise ValarTableTypeError(
                f"Fetching a {cls.__name__} on invalid classes {set(bad_models)}"
            )
        bad_types = [not isinstance(thing, (cls, Integral, str)) for thing in things]
        if any(bad_types):
            raise TypeError(f"Fetching a {cls.__name__} on unknown types {set(bad_types)}")
        # utility functions
        def do_q():
            return join_fn(cls.select())

        def make_dct(the_type):
            dct = defaultdict(list)
            for i, thing in enumerate(things):
                if isinstance(thing, the_type):
                    dct[thing].append(i)
            return dct

        # now we fetch
        # this will become a dict mapping every index in things to its instance
        index_to_match = {}
        # first, we can add all of the actual instances
        # if we need to join on other tables, we'll to do queries anyway
        model_things = make_dct(cls)
        if has_join_fn and len(model_things) > 0:
            for match in do_q().where(cls.id << [z.id for z in model_things.keys()]):
                for ind in model_things[match]:
                    index_to_match[ind] = match
        elif len(model_things) > 0:
            for thing in model_things:
                for ind in model_things[thing]:
                    index_to_match[ind] = thing
        # now let's collect those that are ints and those that are strs
        # unfortunately right now we have to do 2 queries (ID and names), or we'll get type a mismatch error
        int_things = make_dct(Integral)
        str_things = make_dct(str)
        if len(int_things) > 0:
            for match in do_q().where(cls.id << {int(t) for t, ilist in int_things.items()}):
                for ind in int_things[match.id]:
                    index_to_match[ind] = match
        if len(str_things) > 0:
            for match in do_q().where(cls._build_or_query(list(set(str_things.keys())))):
                for col in cls.__indexing_cols():
                    my_attr = getattr(match, col)
                    if my_attr in str_things:
                        for ind in str_things[my_attr]:
                            index_to_match[ind] = match
        return [index_to_match.get(i, None) for i in range(0, len(things))]

    @classmethod
    def fetch_to_query(
        cls,
        thing: Union[
            Integral,
            str,
            peewee.Model,
            peewee.Expression,
            Sequence[peewee.Expression],
            Sequence[Union[Integral, str, peewee.Model]],
        ],
    ) -> Sequence[peewee.Expression]:
        """
        This method has limited but important reasons for being called.
        See ``fetch``, ``fetch_or_none``, ``fetch_all``, or ``fetch_all_or_none`` for more commonly used functions.
        Returns a sequence of Peewee expressions corresponding to WHERE statements::

            - If the instance is one of (int, str, or model), that the row is the one passed,
              matched by ID or unique column value as needed
            - If the instance is a Peewee expression itself, that the expression matches

        Args:
            thing: An int-type to be looked up by the ``id`` column, a ``str``.
                Looked up by::

                    - a unique column value
                    - a model instance
                    - an expression
                    - a list of expressions

        Returns:
            A sequence of Peewee expressions to be joined with AND

        Raises:
            ValarTableTypeError: If ``thing`` is an instance of BaseModel of the wrong type (not this class)
            TypeError: If ``thing`` was not a str, int-like, or a ``BaseModel`` instance
        """
        if isinstance(thing, (Integral, str, Model, peewee.Expression)):
            thing = [thing]
        if all(isinstance(t, peewee.Expression) for t in thing):
            return thing
        elif all(isinstance(t, (Integral, str, Model)) for t in thing):
            # noinspection PyTypeChecker,PyUnresolvedReferences
            return [cls.id << {x.id for x in cls.fetch_all_or_none(thing) if x is not None}]
        raise TypeError(f"Invalid type for {thing} in {cls}")

    @classmethod
    def _build_or_query(
        cls, values: Sequence[Union[Model, int, str]], like: bool = False, regex: bool = False
    ) -> Optional[peewee.Expression]:  # pragma: no cover
        if like and regex:
            raise ValueError(f"Cannot call with both like and regex")
        cols = list(cls.__indexing_cols())
        if len(values) == 0:
            return None
        ids = [i for i in values if isinstance(i, int)]
        ids.extend([i.id for i in values if isinstance(i, cls)])
        strs = [i for i in values if isinstance(i, str)]
        ors = [cls.id << ids]
        if like:
            ors.extend((cls.__gen_ors(strs, cols, lambda attr, t: attr % ("%" + t + "%"))))
        elif regex:
            ors.extend(cls.__gen_ors(strs, cols, lambda attr, t: attr.regexp(t)))
        else:
            ors.extend([getattr(cls, col) << strs for col in cols])
        return cls.__ors_to_query(ors)

    @classmethod
    def __gen_ors(cls, things, cols, function):  # pragma: no cover
        for thing in things:
            for col in cols:
                yield function(getattr(cls, col), thing)

    @classmethod
    def __ors_to_query(cls, ors):  # pragma: no cover
        if len(ors) == 0:
            raise AssertionError("Building WHERE on 0 assertions")
        query = ors[0]
        for e in ors[1:]:
            query = query | e
        return query

    @classmethod
    def __indexing_cols(cls):  # pragma: no cover
        return {
            k
            for k, v in cls._meta.fields.items()
            if v.unique and v.field_type in {"VARCHAR", "CHAR", "ENUM"}
        }

    @classmethod
    def get_indexing_cols(cls):  # pragma: no cover
        """
        Gets the list of unique columns

        Returns:
            The columns, of course
        """
        return cls.__indexing_cols()

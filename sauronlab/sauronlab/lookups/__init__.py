"""
Code only to be used by users, outside Sauronlab, for returning Pandas DataFrames of queries from Valar.
Can depend on all other packages, except for extra.
"""
from __future__ import annotations

from datetime import date

from sauronlab.core.core_imports import *


class Lookup(UntypedDf, metaclass=abc.ABCMeta):
    """
    A Pandas DataFrame from a simple Valar lookup.
    """


class LookupTool(metaclass=abc.ABCMeta):
    """
    A class that provides static functions to look up data from Valar into Lookup DataFrames.
    These functions resemble SQL views.

    """

    @classmethod
    def _expressions_use(cls, expressions, any_of):
        """


        Args:
            expressions:
            any_of:

        Returns:

        """
        return len(LookupTool._expressions_using(expressions, any_of)) > 0

    @classmethod
    def _expressions_using(cls, expressions, any_of):
        """

        Args:
            expressions:
             any_of:

        Returns:

        """
        expressions = InternalTools.flatten_smart(expressions)
        return [
            expression
            for expression in expressions
            if (
                hasattr(expression, "lhs")
                and isinstance(expression.lhs, peewee.Field)
                and expression.lhs.model in any_of
                or hasattr(expression, "rhs")
                and isinstance(expression.rhs, peewee.Field)
                and expression.rhs.model in any_of
            )
        ]

    @classmethod
    def _expressions_not_using(cls, expressions, any_of):
        """
        X.

        Args:
          expressions:
          any_of:

        Returns:

        """
        expressions = InternalTools.flatten_smart(expressions)
        return [
            expression
            for expression in expressions
            if (
                hasattr(expression, "lhs")
                and isinstance(expression.lhs, peewee.Field)
                and expression.lhs.model in any_of
                or hasattr(expression, "rhs")
                and isinstance(expression.rhs, peewee.Field)
                and expression.rhs.model in any_of
            )
        ]

    @classmethod
    def _simple(cls, table, query, like, regex, wheres, *data):
        """
        For backwards compatibility

        Args:
            table:
            query:
            like:
            regex:
            wheres:
            *data:

        Returns:

        """
        return (
            LookupBuilder(table)
            .set_query(query)
            .like_regex(like, regex)
            .add_all(*data)
            .query(wheres)
        )


class Column:
    """"""

    def __init__(
        self,
        name: str,
        attribute: Optional[str] = None,
        function: Optional[Callable[[Any], Any]] = None,
    ):
        """

        Args:
            name:
            attribute:
            function:
        """
        self.name = name
        self.attribute = attribute
        self.function = (lambda x: x) if function is None else function

    def get(self, data: Any) -> Any:
        """


        Args:
            data: Any:

        Returns:

        """
        if self.attribute:
            return self.function(Tools.look(data, self.attribute))
        else:
            return self.function(data)


T = TypeVar("T")
V = TypeVar("V")


class LookupBuilder:
    """"""

    def __init__(self, table: Type[T]):
        """

        Args:
            table:
        """
        self._table = table
        self._query = table.select()
        self._columns = []  # type: List[Column]
        self._like = False
        self._regex = False
        self._sort = "id"
        self._index_cols = "id"
        self._base_attr = None
        self._single_handlers = {}
        self._where_handlers = {}

    def set_query(self, query: peewee.Query) -> LookupBuilder:
        """


        Args:
            query: peewee.Query:

        Returns:

        """
        self._query = query
        return self

    def set_base_attribute(self, attr: str) -> LookupBuilder:
        """


        Args:
            attr: str:

        Returns:

        """
        assert len(self._columns) == 0
        self._base_attr = attr
        return self

    def handle_single(self, type_val: Type[V], function: Callable[[V], ExpressionLike]) -> None:
        """


        Args:
            type_val:
            function:

        """
        self._single_handlers[type_val] = function

    def handle_where(self, type_val: Type[V], function: Callable[[V], ExpressionLike]) -> None:
        """


        Args:
            type_val:
            function:

        """
        self._where_handlers[type_val] = function

    def add_all(
        self, *data: Sequence[Union[str, Tup[str, str], Tup[str, str, Callable[[Any], Any]]]]
    ) -> LookupBuilder:
        """


        Args:
            *data:

        Returns:

        """
        for x in data:
            if isinstance(x, tuple) and len(x) == 3:
                self.add(x[0], x[1], x[2])
            elif isinstance(x, tuple) and len(x) == 2:
                self.add(x[0], x[1])
            else:
                self.add(x)
        return self

    def add(
        self,
        name: str,
        attribute: Optional[str] = None,
        function: Optional[Callable[[Any], Any]] = None,
    ) -> LookupBuilder:
        """


        Args:
            name: str:
            attribute:
            function:

        Returns:

        """
        if attribute is None:
            attribute = name
        elif attribute == "":
            attribute = None
        if self._base_attr is not None and attribute is not None:
            attribute = self._base_attr + "." + attribute
        elif self._base_attr is not None:
            attribute = self._base_attr
        if function is None:
            function = lambda s: s
        self._columns.append(Column(name, attribute, function))
        return self

    def like_regex(self, like: bool, regex: bool) -> LookupBuilder:
        """


        Args:
            like: bool:
            regex: bool:

        Returns:

        """
        if like and regex:
            raise XValueError("Can't pass both ``like`` and ``regex``")
        self._like = like
        self._regex = regex
        return self

    def sort(self, column: str) -> LookupBuilder:
        """


        Args:
            column: str:

        Returns:

        """
        self._sort = column
        return self

    def index(self, column: str) -> LookupBuilder:
        """


        Args:
            column: str:

        Returns:

        """
        self._index_cols = column
        return self

    def query(self, wheres: Iterable[Union[T, str, int, BaseModel, ExpressionLike]]) -> Lookup:
        """


        Args:
            wheres:

        Returns:

        """
        # TODO handle extra singles
        wheres = InternalTools.flatten_smart(wheres)
        expressions = [where for where in wheres if isinstance(where, ExpressionLike)]
        singles = [where for where in wheres if isinstance(where, (int, str, BaseModel))]
        knowns = [
            self._where_handlers[type(where)](where)
            for where in wheres
            if type(where) in self._where_handlers
        ]
        expressions.extend(knowns)
        datetimes = [self._table.created > dt for dt in wheres if isinstance(dt, datetime)]
        expressions.extend(datetimes)
        if any((isinstance(dt, datetime)) for dt in wheres) and not hasattr(self._table, "created"):
            raise XTypeError(
                f"Datetime fields ({datetimes}) not accepted for table {self._table}, which has no 'created' field"
            )
        bads = [
            where
            for where in wheres
            if not isinstance(where, (int, str, BaseModel, datetime, peewee.ColumnBase))
        ]
        if len(bads) > 0:
            raise XTypeError(
                f"Types {[type(b) for b in bads]} not recognized for lookup values {bads}"
            )
        # noinspection PyTypeChecker
        if len(expressions) > 0 and len(singles) > 0:
            raise ContradictoryRequestError(
                "Can't query with both arbitrary expressions and single items"
            )
        elif len(expressions) > 0:
            for where in expressions:
                self._query = self._query.where(where)
        elif len(singles) > 0:
            # noinspection PyProtectedMember
            single_where = self._table._build_or_query(singles, self._like, self._regex)
            self._query = self._query.where(single_where)
        column_names = [column.name for column in self._columns]
        df = Lookup(
            [
                pd.Series({column.name: column.get(row) for column in self._columns})
                for row in self._query
            ],
            columns=column_names,
        )
        df = Lookup.convert(df.cfirst(column_names))
        df = df.sort_values(self._sort).drop_duplicates()
        if self._index_cols is not None:
            df = df.set_index(self._index_cols)
        return Lookup(df)


__all__ = ["Lookup", "LookupTool", "LookupBuilder"]

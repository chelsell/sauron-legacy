from sauronlab.core._imports import *
from sauronlab.core.tools import *
from sauronlab.core.valar_singleton import *

T = TypeVar("T")


@abcd.internal
class InternalTools:
    """
    A collection of utility functions for internal use in Sauronlab.
    Equivalents of some of these functions are in the external-use Tools class, which delegates to this class.
    """

    @classmethod
    def load_resource(
        cls, *parts: Sequence[PathLike]
    ) -> Union[
        str,
        bytes,
        Sequence[str],
        pd.DataFrame,
        Sequence[int],
        Sequence[float],
        Sequence[str],
        Mapping[str, str],
    ]:
        """Loads a resource file of any known type under ``resources/``."""
        path = SauronlabResources.path(*parts)
        return Tools.read_any(path)

    @classmethod
    def fetch_all_ids_unchecked(cls, thing_class: Type[BaseModel], things, keep_none: bool = False):
        """
        Fetches a single row from a table, returning the row IDs.
        If just IDs are passed, just returns them.
        This means that the return value is NOT GUARANTEED to be a valid row ID.

        Args:
            thing_class: The table (peewee model)
            things: A list of lookup values -- each is an ID or unique varchar/char/enum field value
            keep_none: Include None values

        Returns:
            The ID of the row

        Raises:
            ValarLookupError: If a row was not found
        """
        things = InternalTools.listify(things)
        # noinspection PyTypeChecker
        return [
            thing
            if isinstance(thing, int) or thing is None and keep_none
            else thing_class.fetch(thing).id
            for thing in things
        ]

    @classmethod
    def flatten(cls, seq: Iterable[Iterable[T]]) -> Sequence[T]:
        """Flattens an iterable by one level, returning the result."""
        y = []
        for z in seq:
            y.extend(z)
        return y

    @classmethod
    def flatten_smart(cls, seq: Iterable[Any]) -> Sequence[Any]:
        """
        Flattens an iterable any number of nested levels.
        Continues until :meth:`InternalTools.is_true_iterable` is false.
        """
        if not Tools.is_true_iterable(seq):
            return [seq]
        y = []
        for z in seq:
            if Tools.is_true_iterable(z):
                y.extend(z)
            else:
                y.append(z)
        return y

    @classmethod
    def listify(cls, sequence_or_element: Any) -> Sequence[Any]:
        """
        Makes a singleton list of a single element or returns the iterable.
        Will return (a list from) the sequence as-is if it is Iterable, not a string, and not a bytes object.
        The order of iteration from the sequence is preserved.

        Args:
            sequence_or_element: A single element of any type, or an untyped Iterable of elements.
        """
        return list(InternalTools.iterify(sequence_or_element))

    @classmethod
    def iterify(cls, sequence_or_element) -> Iterator[Any]:
        """
        Makes a singleton Iterator of a single element or returns the iterable.
        Will return (an iterator from) the sequence as-is if it is Iterable, not a string, and not a bytes object.

        Args:
            sequence_or_element: A single element of any type, or an untyped Iterable of elements.
        """
        if Tools.is_true_iterable(sequence_or_element):
            return iter(sequence_or_element)
        else:
            return iter([sequence_or_element])


__all__ = ["InternalTools"]

import json
import logging
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Mapping, Union, Generator, Type

import peewee
from peewee import _transaction as PeeweeTransaction

logger = logging.getLogger("valarpy")


class GlobalConnection:  # pragma: no cover
    _peewee_database: peewee.Database = None
    _write_enabled: bool = False

    @classmethod
    def enable_write(cls) -> None:
        """
        Enables running UPDATEs, INSERTs, and DELETEs.
        Otherwise, attempting will raise a ``WriteNotEnabledError``.
        The database user must additionally have the appropriate privileges.
        Note that this function is **not thread-safe.**
        """
        # even though it's a classmethod, refer to the superclass member
        GlobalConnection._write_enabled = True

    @classmethod
    def disable_write(cls) -> None:
        """
        Disables running UPDATEs, INSERTs, and DELETEs.
        See ``enable_write``.
        Note that this function is **not thread-safe.**
        """
        # even though it's a classmethod, refer to the superclass member
        GlobalConnection._write_enabled = False


class Valar:
    """
    Global valarpy connection.
    """

    def __init__(
        self,
        config: Union[
            None, str, Path, List[Union[str, Path, None]], Mapping[str, Union[str, int]]
        ] = None,
    ):
        """
        Constructor.

        Args:
            config: The connection info, which must contain "database" and optionally parameters passed to peewee
                If a dict, used as-is. If a path or str, attempts to read JSON from that path.
                If a list of paths, strs, and Nones, reads from the first extant file found in the list.
                If None, attempts to read JSON from the ``VALARPY_CONFIG`` environment variable, if set.

        Raises:
            FileNotFoundError: If a path was supplied but does not point to a file
            TypeError: If the type was not recognized
            InterfaceError: On some connection issues
        """
        if config is None:
            config = self._read_json(
                self.__class__.find_extant_path(os.environ.get("VALARPY_CONFIG"))
            )
        elif isinstance(config, (str, Path)):
            config = self._read_json(config)
        elif isinstance(config, list) and all(
            (isinstance(p, (str, Path)) for p in config if p is not None)
        ):
            config = self._read_json(self.__class__.find_extant_path(*config))
        elif (
            hasattr(config, "items")
            and hasattr(config, "values")
            and hasattr(config, "keys")
            and hasattr(config, "__getitem__")
            and hasattr(config, "get")
        ):
            pass
        else:
            raise TypeError(f"Invalid type {type(config)} of {config}")
        # make a copy! Otherwise we'll pop the passed argument, which could cause problems
        self._config: Dict[str, Union[str, int]] = {k: v for k, v in config.items()}
        self._db_name = self._config.pop("database")

    @property
    def backend(self) -> Type[GlobalConnection]:
        return GlobalConnection

    @classmethod
    def find_extant_path(cls, *paths: Union[Path, str, None]) -> Path:
        """
        Finds the first extant path in the list.
        It is rare to need to call this directly.

        Args:
            *paths: A list of file paths; values of None are skipped

        Returns:
            The first Path that exists

        Raises:
            FileNotFoundError: If the path found is not a file
        """
        paths = [None if p is None else Path(p) for p in paths]
        path = None
        for path in paths:
            if path is not None and path.exists():
                return path
        if path is None:
            raise FileNotFoundError(f"File {path} not found")
        return path

    @classmethod
    def get_preferred_paths(cls) -> List[Path]:
        """
        Gets a list of preferred paths to look for config files, in order from highest-priority to least-priority.
        Starts with the ``VALARPY_CONFIG`` environment variable, if it is set.

        Returns: A list of ``Path`` instances
        """
        return [
            os.environ.get("VALARPY_CONFIG"),
            Path.home() / ".sauronlab" / "connection.json",
            Path.home() / ".valarpy" / "connection.json",
            Path.home() / ".valarpy" / "config.json",
            Path.home() / ".valarpy" / "read_only.json",
        ]

    @contextmanager
    def rolling_back(self) -> Generator[PeeweeTransaction, None, None]:
        """
        Starts a transaction or savepoint that will be rolled back whether it fails or succeeds.
        Useful for testing.

        Yields:
            A peewee Transaction type; this should generally not be used
        """
        # noinspection PyBroadException
        try:
            with self._db.atomic() as t:
                yield t
        except BaseException:
            logger.debug("Failed on transaction. Rolling back.")
            raise
        finally:
            logger.debug("Succeeded on transaction. Rolling back.")
            t.rollback()

    @contextmanager
    def atomic(self) -> Generator[PeeweeTransaction, None, None]:
        """
        Starts a transaction or savepoint that will be rolled back only on failure.

        Yields:
            A peewee Transaction type; this should generally not be used

        Examples:
            Here, both ``testing1`` and ``testing2`` are created atomically in a single transaction,
            or neither are created on failure because the transaction is automatically rolled back.

                @valar.atomic
                def create_stuff():
                    Refs(name="testing1").save()
                    Refs(name="testing2").save()
        """
        # noinspection PyBroadException
        with self._db.atomic() as t:
            try:
                yield t
            except BaseException:
                logger.debug("Failed on atomic transaction. Rolling back.")
                # t.rollback()
                raise

    @property
    def _db(self) -> peewee.Database:
        """
        The underlying database.
        You should generally not access this directly.

        Returns:
            A peewee ``Database`` instance
        """
        return GlobalConnection._peewee_database

    def reconnect(self, hard: bool = False) -> None:
        """
        Closes and then opens the connection.
        This may be useful for fixing connection issues.

        Args:
            hard: Forcibly close and re-open connection
        """
        if hard:
            self.close()
            self.open()
        else:
            GlobalConnection._peewee_database.connect(reuse_if_open=True)

    def open(self) -> None:
        """
        Opens the database connection.
        This is already called by ``__enter__``.
        """
        logging.info(f"Opening connection to {self._db_name}")
        GlobalConnection._peewee_database = peewee.MySQLDatabase(
            self._db_name, autorollback=True, **self._config
        )
        GlobalConnection._peewee_database.connect()
        if self._db.in_transaction():
            raise AssertionError("In transaction on open() but should not be")

    def close(self) -> None:
        """
        Closes the connection.
        This is already called by ``__exit__``.
        """
        logging.info(f"Closing connection to {self._db_name}")
        GlobalConnection._peewee_database.close()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, t, value, traceback):
        self.close()

    def __del__(self):  # pragma: no cover
        try:
            self.close()
        except AttributeError:
            # Because del gets called at weird times, we might not have a _db_name, etc.
            logger.debug(f"Error when closing on delete", exc_info=True)

    @classmethod
    def _read_json(cls, path: Union[str, Path]) -> Dict[str, Any]:
        if not Path(path).exists():
            raise FileNotFoundError(f"JSON config file {path} does not exist")
        if not Path(path).is_file():
            raise FileNotFoundError(f"JSON config file {path} is not a file")
        return json.loads(Path(path).read_text(encoding="utf8"))


__all__ = ["GlobalConnection", "Valar"]

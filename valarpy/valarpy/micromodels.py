class ValarLookupError(KeyError):
    """
    A value wasn't found in Valar.
    """


class ValarTableTypeError(TypeError):
    """
    A function was passed a row of a table, but from the wrong table.
    """


class UnsupportedOperationError(Exception):
    """
    This database operation is not supported.
    """


class WriteNotEnabledError(Exception):
    """
    Write access has not been enabled.
    """

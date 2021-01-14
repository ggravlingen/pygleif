"""Errors for PyGLEIF."""


class PyGLEIFError(Exception):
    """Base Error"""

    pass


class NoMatchError(PyGLEIFError):
    """An error happened sending or receiving a command."""

    pass

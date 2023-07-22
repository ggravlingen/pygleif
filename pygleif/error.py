"""Errors for PyGLEIF."""


class PyGLEIFError(Exception):
    """Base Error."""


class NoMatchError(PyGLEIFError):
    """An error happened sending or receiving a command."""

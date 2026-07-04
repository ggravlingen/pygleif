"""Errors for the pygleif v2 client."""

from __future__ import annotations


class PyGLEIFError(Exception):
    """Base error for v2."""


class PyGLEIFApiError(PyGLEIFError):
    """Raised for HTTP / transport failures against the GLEIF API."""


class PyGLEIFNotFoundError(PyGLEIFApiError):
    """Raised when a requested resource does not exist (HTTP 404)."""


class PyGLEIFRateLimitError(PyGLEIFApiError):
    """Raised when the GLEIF rate limit is exceeded (HTTP 429)."""

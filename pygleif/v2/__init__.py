"""New v2 namespace.

Implements the full GLEIF API v1.0. New features should land here, not in
``pygleif.v1``.
"""

from .api import GLEIFResponse, LeiRecord, SearchResponse
from .base import Transport
from .client import ExportFormat, GleifClient, SearchType
from .error import (
    PyGLEIFApiError,
    PyGLEIFError,
    PyGLEIFNotFoundError,
    PyGLEIFRateLimitError,
)

__all__ = [
    "ExportFormat",
    "GLEIFResponse",
    "GleifClient",
    "LeiRecord",
    "PyGLEIFApiError",
    "PyGLEIFError",
    "PyGLEIFNotFoundError",
    "PyGLEIFRateLimitError",
    "SearchResponse",
    "SearchType",
    "Transport",
]

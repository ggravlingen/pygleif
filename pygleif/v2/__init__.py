"""New v2 namespace.

Implements the full GLEIF API v1.0. New features should land here, not in
``pygleif.v1``.
"""

from .client import GleifClient, SearchType

__all__ = ["GleifClient", "SearchType"]

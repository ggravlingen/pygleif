"""Frozen v1 namespace.

This namespace preserves the historical public API of pygleif unchanged.
No new features should land here; new work belongs in ``pygleif.v2``.

Backwards compatibility contract:
    ``from pygleif import PyGleif, Search`` and
    ``from pygleif.v1 import PyGleif, Search`` must keep working exactly
    as before the v2 split.
"""

from .client import LegacyClient
from .gleif import PyGleif
from .search import Search, SearchType

__all__ = ["LegacyClient", "PyGleif", "Search", "SearchType"]

"""pygleif — query the GLEIF API using Python.

Top-level exports keep the historical public API stable while exposing
the split ``v1``/``v2``/``compat`` namespaces introduced for the v2 work.

Backwards compatibility:
    ``from pygleif import PyGleif, Search`` continues to resolve to the
    frozen v1 implementation exactly as before.

New code:
    ``from pygleif import GleifClient`` (v2) or the explicit namespaces
    ``pygleif.v1`` / ``pygleif.v2`` / ``pygleif.compat``.

Using this library (humans and AI assistants):
    Read the best-practices guide shipped with the package: run
    ``pygleif guide`` or open ``pygleif/AGENTS.md``. The key rule: GLEIF
    allows 60 requests/minute, so batch lookups with
    ``GleifClient.get_lei_records`` and iterate with ``iter_search``
    instead of looping over single-record calls.
"""

from . import compat, v1, v2
from .compat.interfaces import BaseApiClient
from .v1 import PyGleif, Search
from .v2 import ExportFormat, GleifClient, SearchType

__all__ = [
    "BaseApiClient",
    "ExportFormat",
    "GleifClient",
    "PyGleif",
    "Search",
    "SearchType",
    "compat",
    "v1",
    "v2",
]

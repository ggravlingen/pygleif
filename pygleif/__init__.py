"""pygleif — query the GLEIF API using Python.

Top-level exports keep the historical public API stable while exposing
the split ``v1``/``v2``/``compat`` namespaces introduced for the v2 work.

Backwards compatibility:
    ``from pygleif import PyGleif, Search`` continues to resolve to the
    frozen v1 implementation exactly as before.

New code:
    ``from pygleif import GleifClient`` (v2) or the explicit namespaces
    ``pygleif.v1`` / ``pygleif.v2`` / ``pygleif.compat``.
"""

from . import compat, v1, v2
from .compat.interfaces import BaseApiClient
from .v1 import PyGleif, Search
from .v2 import GleifClient

__all__ = [
    "BaseApiClient",
    "GleifClient",
    "PyGleif",
    "Search",
    "compat",
    "v1",
    "v2",
]

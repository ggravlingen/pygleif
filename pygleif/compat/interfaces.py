"""Shared interfaces for both API generations.

These types form the stable contract that both ``pygleif.v1`` and
``pygleif.v2`` normalize toward. They intentionally avoid importing
pydantic so the compatibility surface stays valid under either pydantic
namespace during the migration.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class RecordLike:
    """Compatibility DTO used by tests and adapters.

    A minimal, generation-agnostic view of an LEI record. Both the frozen
    v1 client and the new v2 client can produce this shape so callers can
    depend on it regardless of the underlying implementation.
    """

    lei: str
    legal_name: str | None
    country: str | None


@runtime_checkable
class BaseApiClient(Protocol):
    """Stable client contract shared across v1 and v2 implementations."""

    def get_lei(self, lei: str) -> RecordLike:
        """Return a normalized record for a single LEI."""

    def healthcheck(self) -> bool:
        """Return whether the client is operational."""

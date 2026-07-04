"""Adapters that normalize v1 and v2 model outputs to the shared DTO."""

from __future__ import annotations

from pygleif.compat.interfaces import RecordLike


def normalize_record(
    *,
    lei: str,
    legal_name: str | None,
    country: str | None,
) -> RecordLike:
    """Build a normalized compatibility DTO from loose fields."""
    return RecordLike(lei=lei, legal_name=legal_name, country=country)

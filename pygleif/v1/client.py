"""Frozen v1 client adapter.

Wraps the historical :class:`~pygleif.v1.gleif.PyGleif` request object in
the shared :class:`~pygleif.compat.interfaces.BaseApiClient` contract so
callers can treat v1 and v2 uniformly. The legacy ``PyGleif``/``Search``
public API remains available and unchanged.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pygleif.compat.adapters import normalize_record

from .gleif import PyGleif

if TYPE_CHECKING:
    from pygleif.compat.interfaces import RecordLike


class LegacyClient:
    """Compatibility adapter over the frozen v1 ``PyGleif`` implementation.

    Keep this namespace stable during migration. New behavior belongs in
    ``pygleif.v2.GleifClient``.
    """

    def get_lei(self, lei: str) -> RecordLike:
        """Fetch a single LEI record and normalize it to the shared DTO."""
        response = PyGleif(lei).response
        attributes = response.data.attributes
        return normalize_record(
            lei=attributes.lei,
            legal_name=attributes.entity.legal_name.name,
            country=attributes.entity.legal_address.country,
        )

    def healthcheck(self) -> bool:
        """Return client health.

        The v1 client is stateless and always considered operational; a
        real connectivity probe would issue a lightweight request.
        """
        return True

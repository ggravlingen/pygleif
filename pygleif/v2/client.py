"""v2 GLEIF client implementing the full API v1.0 surface.

``GleifClient`` covers the documented endpoints:

- ``get_lei``            -> ``GET /lei-records/{lei}``
- ``search``             -> ``GET /lei-records`` (filters, sort, pagination)
- ``owners`` / ``children`` -> relationship lookups via ``owns`` / ``ownedBy``
- ``isins``              -> ``GET /lei-records/{lei}/isins``
- ``fuzzy_completions``  -> ``GET /fuzzycompletions``
- ``fields``             -> ``GET /fields``

It also satisfies the shared :class:`~pygleif.compat.interfaces.BaseApiClient`
contract (``get_lei`` returning a normalized DTO is exposed as
``get_lei_record`` for the rich model; ``get_lei`` returns ``RecordLike``).
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Any

from pygleif.compat.adapters import normalize_record
from pygleif.v2.api import (
    FieldsResponse,
    FuzzyCompletionResponse,
    GLEIFResponse,
    IsinResponse,
    SearchResponse,
)
from pygleif.v2.base import Transport

if TYPE_CHECKING:
    from pygleif.compat.interfaces import RecordLike


class SearchType(StrEnum):
    """Fields supported for full-text and single-field searches."""

    FULL_TEXT = "fulltext"
    LEGAL_NAME = "entity.legalName"


class GleifClient:
    """High-level client for the GLEIF API v1.0.

    New features land here; the frozen v1 API lives in ``pygleif.v1``.
    """

    def __init__(self, transport: Transport | None = None) -> None:
        """Init the client, optionally with a custom transport."""
        self._transport = transport or Transport()

    # -- single record --------------------------------------------------
    def get_lei_record(self, lei: str) -> GLEIFResponse:
        """Return the full LEI record for a single LEI code."""
        payload = self._transport.get(f"lei-records/{lei}")
        return GLEIFResponse(**payload)

    def get_lei(self, lei: str) -> RecordLike:
        """Return a normalized :class:`RecordLike` for a single LEI.

        Implements the shared :class:`BaseApiClient` contract.
        """
        attributes = self.get_lei_record(lei).data.attributes
        return normalize_record(
            lei=attributes.lei,
            legal_name=attributes.entity.legal_name.name,
            country=attributes.entity.legal_address.country,
        )

    # -- search ---------------------------------------------------------
    def search(
        self,
        *,
        filters: dict[str, str] | None = None,
        sort: str | None = None,
        page_number: int = 1,
        page_size: int = 15,
    ) -> SearchResponse:
        """Search LEI records with JSON:API filters, sorting and pagination.

        Filter keys are the bare field names (e.g. ``"fulltext"``,
        ``"lei"``, ``"bic"``, ``"isin"``, ``"entity.legalAddress.country"``)
        and are wrapped as ``filter[<key>]`` in the request.
        """
        params: dict[str, Any] = {
            "page[number]": page_number,
            "page[size]": page_size,
        }
        if sort:
            params["sort"] = sort
        for key, value in (filters or {}).items():
            params[f"filter[{key}]"] = value
        payload = self._transport.get("lei-records", params)
        return SearchResponse(**payload)

    def search_fulltext(
        self,
        query: str,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> SearchResponse:
        """Run a full-text search over LEI records."""
        return self.search(
            filters={"fulltext": query},
            page_number=page_number,
            page_size=page_size,
        )

    def by_bic(
        self,
        bic: str,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> SearchResponse:
        """Look up LEI records by BIC code."""
        return self.search(
            filters={"bic": bic},
            page_number=page_number,
            page_size=page_size,
        )

    def by_isin(
        self,
        isin: str,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> SearchResponse:
        """Look up LEI records by ISIN code."""
        return self.search(
            filters={"isin": isin},
            page_number=page_number,
            page_size=page_size,
        )

    # -- relationships (Level 2) ---------------------------------------
    def owners(
        self,
        lei: str,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> SearchResponse:
        """Return the parent entities that own the given LEI (``owns``)."""
        return self.search(
            filters={"owns": lei},
            page_number=page_number,
            page_size=page_size,
        )

    def children(
        self,
        lei: str,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> SearchResponse:
        """Return the child entities owned by the given LEI (``ownedBy``)."""
        return self.search(
            filters={"ownedBy": lei},
            page_number=page_number,
            page_size=page_size,
        )

    # -- ISIN mappings --------------------------------------------------
    def isins(
        self,
        lei: str,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> IsinResponse:
        """Return all ISINs mapped to the given LEI record."""
        params = {"page[number]": page_number, "page[size]": page_size}
        payload = self._transport.get(f"lei-records/{lei}/isins", params)
        return IsinResponse(**payload)

    # -- fuzzy completions ---------------------------------------------
    def fuzzy_completions(
        self,
        query: str,
        *,
        field: str = "fulltext",
    ) -> FuzzyCompletionResponse:
        """Find legal entities with names similar to ``query`` (fuzzy match)."""
        params = {"field": field, "q": query}
        payload = self._transport.get("fuzzycompletions", params)
        return FuzzyCompletionResponse(**payload)

    # -- field metadata -------------------------------------------------
    def fields(self) -> FieldsResponse:
        """Return technical metadata describing the API's LEI data fields."""
        payload = self._transport.get("fields")
        return FieldsResponse(**payload)

    # -- health ---------------------------------------------------------
    def healthcheck(self) -> bool:
        """Return whether the API is reachable.

        Issues a minimal ``/fields`` request; any transport error surfaces
        as a ``False`` result rather than raising.
        """
        try:
            self._transport.get("fields", {"page[size]": 1})
        except Exception:  # noqa: BLE001 - healthcheck must not raise
            return False
        return True

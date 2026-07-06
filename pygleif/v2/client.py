"""v2 GLEIF client implementing the full documented API v1.0 surface.

``GleifClient`` covers every endpoint in the official GLEIF API docs
(https://documenter.getpostman.com/view/7679680/SVYrrxuU):

- LEI records: ``get_lei_record``, ``search`` (filters, sort, pagination)
  plus the ``search_fulltext`` / ``by_bic`` / ``by_isin`` conveniences and
  the auto-paginating ``iter_search``.
- Level 2 relationships: ``direct_parent``, ``ultimate_parent``,
  ``direct_children``, ``ultimate_children``, the ``*_relationship(s)``
  record lookups and the ``*_reporting_exception`` lookups.
- Related records: ``lei_issuer``, ``managing_lou``, ``associated_entity``,
  ``successor_entity``.
- ``isins``, ``field_modifications``.
- Completions: ``fuzzy_completions``, ``autocompletions``.
- Field metadata: ``fields``, ``get_field``.
- Issuers: ``lei_issuers``, ``get_lei_issuer``, ``lei_issuer_jurisdictions``,
  ``vlei_issuers``, ``get_vlei_issuer``.
- Reference data: ``countries``, ``entity_legal_forms``,
  ``official_organizational_roles``, ``jurisdictions``, ``regions``,
  ``registration_authorities``, ``registration_agents`` (each with a
  ``get_*`` detail lookup).
- ``export_lei_records`` (``/export/v1``, file download).

It also satisfies the shared :class:`~pygleif.compat.interfaces.BaseApiClient`
contract (``get_lei`` returns a normalized ``RecordLike`` DTO;
``get_lei_record`` returns the rich model).

Every method has an async counterpart prefixed with ``a`` (e.g. ``search``
and ``asearch``) backed by the same :class:`~pygleif.v2.base.Transport`.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Any, Self

from pygleif.compat.adapters import normalize_record
from pygleif.v2.api import (
    AutocompletionResponse,
    CountriesResponse,
    CountryResponse,
    EntityLegalFormResponse,
    EntityLegalFormsResponse,
    FieldModificationResponse,
    FieldResponse,
    FieldsResponse,
    FuzzyCompletionResponse,
    GLEIFResponse,
    IsinResponse,
    JurisdictionResponse,
    JurisdictionsResponse,
    LeiIssuerJurisdictionsResponse,
    LeiIssuerResponse,
    LeiIssuersResponse,
    OfficialOrganizationalRoleResponse,
    OfficialOrganizationalRolesResponse,
    RegionResponse,
    RegionsResponse,
    RegistrationAgentResponse,
    RegistrationAgentsResponse,
    RegistrationAuthoritiesResponse,
    RegistrationAuthorityResponse,
    RelationshipListResponse,
    RelationshipResponse,
    ReportingExceptionResponse,
    SearchResponse,
    VLeiIssuerResponse,
    VLeiIssuersResponse,
)
from pygleif.v2.base import DEFAULT_TIMEOUT_SECONDS, EXPORT_BASE_URL, Transport

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

    from pygleif.compat.interfaces import RecordLike
    from pygleif.v2.api import LeiRecord
    from pygleif.v2.base import TransportLike
    from pygleif.v2.pydantic_shim import BaseModel


class SearchType(StrEnum):
    """Fields supported by the completion and search endpoints."""

    FULL_TEXT = "fulltext"
    LEGAL_NAME = "entity.legalName"
    OWNS = "owns"
    OWNED_BY = "ownedBy"


class ExportFormat(StrEnum):
    """File formats supported by the LEI record export endpoint."""

    CSV = "csv"
    XLSX = "xlsx"
    JSON = "json"


class GleifClient:
    """High-level client for the GLEIF API v1.0.

    New features land here; the frozen v1 API lives in ``pygleif.v1``.
    """

    def __init__(
        self,
        transport: TransportLike | None = None,
        *,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        retries: int = 0,
    ) -> None:
        """Init the client, optionally with a custom transport.

        ``timeout`` (seconds) and ``retries`` (extra attempts for
        transient failures such as HTTP 429/5xx) configure the default
        :class:`~pygleif.v2.base.Transport`; they are ignored when a
        ``transport`` is injected.
        """
        self._transport = transport or Transport(timeout=timeout, retries=retries)

    # -- request/validation helpers ---------------------------------------
    def _fetch[ModelT: BaseModel](
        self,
        model: type[ModelT],
        path: str,
        params: dict[str, Any] | None = None,
    ) -> ModelT:
        """Fetch ``path`` and validate the payload into ``model``."""
        return model.model_validate(self._transport.get(path, params))

    async def _afetch[ModelT: BaseModel](
        self,
        model: type[ModelT],
        path: str,
        params: dict[str, Any] | None = None,
    ) -> ModelT:
        """Async counterpart of :meth:`_fetch`."""
        return model.model_validate(await self._transport.aget(path, params))

    # -- shared param builders -------------------------------------------
    @staticmethod
    def _page_params(page_number: int, page_size: int) -> dict[str, Any]:
        """Build the JSON:API pagination params."""
        return {"page[number]": page_number, "page[size]": page_size}

    @staticmethod
    def _filter_params(
        filters: dict[str, str] | None,
        sort: str | None,
    ) -> dict[str, Any]:
        """Build ``filter[...]`` and ``sort`` params."""
        params: dict[str, Any] = {}
        if sort:
            params["sort"] = sort
        for key, value in (filters or {}).items():
            params[f"filter[{key}]"] = value
        return params

    @classmethod
    def _search_params(
        cls,
        *,
        filters: dict[str, str] | None,
        sort: str | None,
        page_number: int,
        page_size: int,
    ) -> dict[str, Any]:
        """Build the JSON:API query params shared by ``search``/``asearch``."""
        return {
            **cls._page_params(page_number, page_size),
            **cls._filter_params(filters, sort),
        }

    @classmethod
    def _field_modification_params(  # noqa: PLR0913 - one arg per API filter
        cls,
        *,
        modification_type: str | None,
        record_type: str | None,
        field: str | None,
        date: str | None,
        page_number: int,
        page_size: int,
    ) -> dict[str, Any]:
        """Build the params for the field-modifications endpoint."""
        filters = {
            key: value
            for key, value in (
                ("modificationType", modification_type),
                ("recordType", record_type),
                ("field", field),
                ("date", date),
            )
            if value is not None
        }
        return cls._search_params(
            filters=filters,
            sort=None,
            page_number=page_number,
            page_size=page_size,
        )

    @staticmethod
    def _to_record(response: GLEIFResponse) -> RecordLike:
        """Normalize a parsed LEI record response to ``RecordLike``."""
        attributes = response.data.attributes
        return normalize_record(
            lei=attributes.lei,
            legal_name=attributes.entity.legal_name.name,
            country=attributes.entity.legal_address.country,
        )

    # -- single record --------------------------------------------------
    def get_lei_record(self, lei: str) -> GLEIFResponse:
        """Return the full LEI record for a single LEI code."""
        return self._fetch(GLEIFResponse, f"lei-records/{lei}")

    async def aget_lei_record(self, lei: str) -> GLEIFResponse:
        """Return the full LEI record for a single LEI code (async)."""
        return await self._afetch(GLEIFResponse, f"lei-records/{lei}")

    def get_lei(self, lei: str) -> RecordLike:
        """Return a normalized :class:`RecordLike` for a single LEI.

        Implements the shared :class:`BaseApiClient` contract.
        """
        return self._to_record(self.get_lei_record(lei))

    async def aget_lei(self, lei: str) -> RecordLike:
        """Return a normalized :class:`RecordLike` for a single LEI (async)."""
        return self._to_record(await self.aget_lei_record(lei))

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
        ``"lei"``, ``"bic"``, ``"isin"``, ``"entity.legalAddress.country"``,
        ``"owns"``, ``"ownedBy"``) and are wrapped as ``filter[<key>]`` in
        the request.

        Filter values support the documented search operators, passed
        through verbatim:

        - ``!abc`` - must not match
        - ``abc,def`` - must match any (``!abc,def`` for none)
        - ``123..456`` - range (dates as ``YYYYMMDD``)
        - ``>123`` / ``>=123`` / ``<123`` / ``<=123`` - comparisons

        Prefix ``sort`` with ``-`` for descending order.
        """
        params = self._search_params(
            filters=filters,
            sort=sort,
            page_number=page_number,
            page_size=page_size,
        )
        return self._fetch(SearchResponse, "lei-records", params)

    async def asearch(
        self,
        *,
        filters: dict[str, str] | None = None,
        sort: str | None = None,
        page_number: int = 1,
        page_size: int = 15,
    ) -> SearchResponse:
        """Search LEI records with JSON:API filters, sorting and pagination.

        Async counterpart of :meth:`search`.
        """
        params = self._search_params(
            filters=filters,
            sort=sort,
            page_number=page_number,
            page_size=page_size,
        )
        return await self._afetch(SearchResponse, "lei-records", params)

    def iter_search(
        self,
        *,
        filters: dict[str, str] | None = None,
        sort: str | None = None,
        page_size: int = 100,
        start_page: int = 1,
        max_records: int | None = None,
    ) -> Iterator[LeiRecord]:
        """Yield LEI records across all result pages of a search.

        Follows the response pagination until the last page (or
        ``max_records``) is reached, so a single call iterates the full
        result set. The API caps ``page_size`` at 200 and the service is
        rate limited to 60 requests/minute; prefer large page sizes for
        big result sets.
        """
        page = start_page
        yielded = 0
        while True:
            response = self.search(
                filters=filters,
                sort=sort,
                page_number=page,
                page_size=page_size,
            )
            for record in response.data:
                yield record
                yielded += 1
                if max_records is not None and yielded >= max_records:
                    return
            pagination = response.meta.pagination
            if not response.data or pagination is None or page >= pagination.last_page:
                return
            page += 1

    async def aiter_search(
        self,
        *,
        filters: dict[str, str] | None = None,
        sort: str | None = None,
        page_size: int = 100,
        start_page: int = 1,
        max_records: int | None = None,
    ) -> AsyncIterator[LeiRecord]:
        """Yield LEI records across all result pages of a search (async).

        Async counterpart of :meth:`iter_search`.
        """
        page = start_page
        yielded = 0
        while True:
            response = await self.asearch(
                filters=filters,
                sort=sort,
                page_number=page,
                page_size=page_size,
            )
            for record in response.data:
                yield record
                yielded += 1
                if max_records is not None and yielded >= max_records:
                    return
            pagination = response.meta.pagination
            if not response.data or pagination is None or page >= pagination.last_page:
                return
            page += 1

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

    async def asearch_fulltext(
        self,
        query: str,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> SearchResponse:
        """Run a full-text search over LEI records (async)."""
        return await self.asearch(
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

    async def aby_bic(
        self,
        bic: str,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> SearchResponse:
        """Look up LEI records by BIC code (async)."""
        return await self.asearch(
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

    async def aby_isin(
        self,
        isin: str,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> SearchResponse:
        """Look up LEI records by ISIN code (async)."""
        return await self.asearch(
            filters={"isin": isin},
            page_number=page_number,
            page_size=page_size,
        )

    # -- relationships (Level 2): parent / child LEI records -------------
    def direct_parent(self, lei: str) -> GLEIFResponse:
        """Return the LEI record of the direct parent.

        Raises :class:`PyGLEIFNotFoundError` when no direct parent is
        reported (see :meth:`direct_parent_reporting_exception`).
        """
        return self._fetch(GLEIFResponse, f"lei-records/{lei}/direct-parent")

    async def adirect_parent(self, lei: str) -> GLEIFResponse:
        """Return the LEI record of the direct parent (async)."""
        return await self._afetch(GLEIFResponse, f"lei-records/{lei}/direct-parent")

    def ultimate_parent(self, lei: str) -> GLEIFResponse:
        """Return the LEI record of the ultimate parent.

        Raises :class:`PyGLEIFNotFoundError` when no ultimate parent is
        reported (see :meth:`ultimate_parent_reporting_exception`).
        """
        return self._fetch(GLEIFResponse, f"lei-records/{lei}/ultimate-parent")

    async def aultimate_parent(self, lei: str) -> GLEIFResponse:
        """Return the LEI record of the ultimate parent (async)."""
        return await self._afetch(GLEIFResponse, f"lei-records/{lei}/ultimate-parent")

    def direct_children(
        self,
        lei: str,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> SearchResponse:
        """Return the LEI records of the direct children."""
        params = self._page_params(page_number, page_size)
        return self._fetch(
            SearchResponse,
            f"lei-records/{lei}/direct-children",
            params,
        )

    async def adirect_children(
        self,
        lei: str,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> SearchResponse:
        """Return the LEI records of the direct children (async)."""
        params = self._page_params(page_number, page_size)
        return await self._afetch(
            SearchResponse,
            f"lei-records/{lei}/direct-children",
            params,
        )

    def ultimate_children(
        self,
        lei: str,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> SearchResponse:
        """Return the LEI records of the ultimate children."""
        params = self._page_params(page_number, page_size)
        return self._fetch(
            SearchResponse,
            f"lei-records/{lei}/ultimate-children",
            params,
        )

    async def aultimate_children(
        self,
        lei: str,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> SearchResponse:
        """Return the LEI records of the ultimate children (async)."""
        params = self._page_params(page_number, page_size)
        return await self._afetch(
            SearchResponse,
            f"lei-records/{lei}/ultimate-children",
            params,
        )

    # -- relationships (Level 2): relationship records --------------------
    def direct_parent_relationship(self, lei: str) -> RelationshipResponse:
        """Return the direct parent relationship record."""
        return self._fetch(
            RelationshipResponse,
            f"lei-records/{lei}/direct-parent-relationship",
        )

    async def adirect_parent_relationship(self, lei: str) -> RelationshipResponse:
        """Return the direct parent relationship record (async)."""
        return await self._afetch(
            RelationshipResponse,
            f"lei-records/{lei}/direct-parent-relationship",
        )

    def ultimate_parent_relationship(self, lei: str) -> RelationshipResponse:
        """Return the ultimate parent relationship record."""
        return self._fetch(
            RelationshipResponse,
            f"lei-records/{lei}/ultimate-parent-relationship",
        )

    async def aultimate_parent_relationship(self, lei: str) -> RelationshipResponse:
        """Return the ultimate parent relationship record (async)."""
        return await self._afetch(
            RelationshipResponse,
            f"lei-records/{lei}/ultimate-parent-relationship",
        )

    def direct_child_relationships(
        self,
        lei: str,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> RelationshipListResponse:
        """Return the direct child relationship records."""
        params = self._page_params(page_number, page_size)
        return self._fetch(
            RelationshipListResponse,
            f"lei-records/{lei}/direct-child-relationships",
            params,
        )

    async def adirect_child_relationships(
        self,
        lei: str,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> RelationshipListResponse:
        """Return the direct child relationship records (async)."""
        params = self._page_params(page_number, page_size)
        return await self._afetch(
            RelationshipListResponse,
            f"lei-records/{lei}/direct-child-relationships",
            params,
        )

    def ultimate_child_relationships(
        self,
        lei: str,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> RelationshipListResponse:
        """Return the ultimate child relationship records."""
        params = self._page_params(page_number, page_size)
        return self._fetch(
            RelationshipListResponse,
            f"lei-records/{lei}/ultimate-child-relationships",
            params,
        )

    async def aultimate_child_relationships(
        self,
        lei: str,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> RelationshipListResponse:
        """Return the ultimate child relationship records (async)."""
        params = self._page_params(page_number, page_size)
        return await self._afetch(
            RelationshipListResponse,
            f"lei-records/{lei}/ultimate-child-relationships",
            params,
        )

    # -- relationships (Level 2): reporting exceptions --------------------
    def direct_parent_reporting_exception(
        self,
        lei: str,
    ) -> ReportingExceptionResponse:
        """Return the reporting exception for the missing direct parent."""
        return self._fetch(
            ReportingExceptionResponse,
            f"lei-records/{lei}/direct-parent-reporting-exception",
        )

    async def adirect_parent_reporting_exception(
        self,
        lei: str,
    ) -> ReportingExceptionResponse:
        """Return the direct parent reporting exception (async)."""
        return await self._afetch(
            ReportingExceptionResponse,
            f"lei-records/{lei}/direct-parent-reporting-exception",
        )

    def ultimate_parent_reporting_exception(
        self,
        lei: str,
    ) -> ReportingExceptionResponse:
        """Return the reporting exception for the missing ultimate parent."""
        return self._fetch(
            ReportingExceptionResponse,
            f"lei-records/{lei}/ultimate-parent-reporting-exception",
        )

    async def aultimate_parent_reporting_exception(
        self,
        lei: str,
    ) -> ReportingExceptionResponse:
        """Return the ultimate parent reporting exception (async)."""
        return await self._afetch(
            ReportingExceptionResponse,
            f"lei-records/{lei}/ultimate-parent-reporting-exception",
        )

    # -- related records --------------------------------------------------
    def lei_issuer(self, lei: str) -> LeiIssuerResponse:
        """Return the LEI issuer (LOU) record that manages the given LEI.

        For the issuer's own LEI record, use :meth:`managing_lou`.
        """
        return self._fetch(LeiIssuerResponse, f"lei-records/{lei}/lei-issuer")

    async def alei_issuer(self, lei: str) -> LeiIssuerResponse:
        """Return the LEI issuer record for the given LEI (async)."""
        return await self._afetch(LeiIssuerResponse, f"lei-records/{lei}/lei-issuer")

    def managing_lou(self, lei: str) -> GLEIFResponse:
        """Return the LEI record of the managing LOU (LEI issuer)."""
        return self._fetch(GLEIFResponse, f"lei-records/{lei}/managing-lou")

    async def amanaging_lou(self, lei: str) -> GLEIFResponse:
        """Return the LEI record of the managing LOU (async)."""
        return await self._afetch(GLEIFResponse, f"lei-records/{lei}/managing-lou")

    def associated_entity(self, lei: str) -> GLEIFResponse:
        """Return the associated entity (fund manager) LEI record."""
        return self._fetch(GLEIFResponse, f"lei-records/{lei}/associated-entity")

    async def aassociated_entity(self, lei: str) -> GLEIFResponse:
        """Return the associated entity LEI record (async)."""
        return await self._afetch(
            GLEIFResponse,
            f"lei-records/{lei}/associated-entity",
        )

    def successor_entity(self, lei: str) -> GLEIFResponse:
        """Return the successor entity LEI record."""
        return self._fetch(GLEIFResponse, f"lei-records/{lei}/successor-entity")

    async def asuccessor_entity(self, lei: str) -> GLEIFResponse:
        """Return the successor entity LEI record (async)."""
        return await self._afetch(
            GLEIFResponse,
            f"lei-records/{lei}/successor-entity",
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
        params = self._page_params(page_number, page_size)
        return self._fetch(IsinResponse, f"lei-records/{lei}/isins", params)

    async def aisins(
        self,
        lei: str,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> IsinResponse:
        """Return all ISINs mapped to the given LEI record (async)."""
        params = self._page_params(page_number, page_size)
        return await self._afetch(IsinResponse, f"lei-records/{lei}/isins", params)

    # -- field modifications ----------------------------------------------
    def field_modifications(  # noqa: PLR0913 - one arg per API filter
        self,
        lei: str,
        *,
        modification_type: str | None = None,
        record_type: str | None = None,
        field: str | None = None,
        date: str | None = None,
        page_number: int = 1,
        page_size: int = 15,
    ) -> FieldModificationResponse:
        """Return the historical changes of the given LEI record.

        Optional filters map to ``filter[modificationType]``,
        ``filter[recordType]``, ``filter[field]`` and ``filter[date]``.
        """
        params = self._field_modification_params(
            modification_type=modification_type,
            record_type=record_type,
            field=field,
            date=date,
            page_number=page_number,
            page_size=page_size,
        )
        return self._fetch(
            FieldModificationResponse,
            f"lei-records/{lei}/field-modifications",
            params,
        )

    async def afield_modifications(  # noqa: PLR0913 - one arg per API filter
        self,
        lei: str,
        *,
        modification_type: str | None = None,
        record_type: str | None = None,
        field: str | None = None,
        date: str | None = None,
        page_number: int = 1,
        page_size: int = 15,
    ) -> FieldModificationResponse:
        """Return the historical changes of the given LEI record (async)."""
        params = self._field_modification_params(
            modification_type=modification_type,
            record_type=record_type,
            field=field,
            date=date,
            page_number=page_number,
            page_size=page_size,
        )
        return await self._afetch(
            FieldModificationResponse,
            f"lei-records/{lei}/field-modifications",
            params,
        )

    # -- completions ------------------------------------------------------
    def fuzzy_completions(
        self,
        query: str,
        *,
        field: SearchType | str = SearchType.FULL_TEXT,
    ) -> FuzzyCompletionResponse:
        """Find legal entities with data similar to ``query`` (fuzzy match).

        ``field`` accepts the :class:`SearchType` values.
        """
        params = {"field": str(field), "q": query}
        return self._fetch(FuzzyCompletionResponse, "fuzzycompletions", params)

    async def afuzzy_completions(
        self,
        query: str,
        *,
        field: SearchType | str = SearchType.FULL_TEXT,
    ) -> FuzzyCompletionResponse:
        """Find legal entities with data similar to ``query`` (async)."""
        params = {"field": str(field), "q": query}
        return await self._afetch(FuzzyCompletionResponse, "fuzzycompletions", params)

    def autocompletions(
        self,
        query: str,
        *,
        field: SearchType | str = SearchType.FULL_TEXT,
    ) -> AutocompletionResponse:
        """Return suggested search terms similar to ``query``.

        ``field`` accepts the :class:`SearchType` values.
        """
        params = {"field": str(field), "q": query}
        return self._fetch(AutocompletionResponse, "autocompletions", params)

    async def aautocompletions(
        self,
        query: str,
        *,
        field: SearchType | str = SearchType.FULL_TEXT,
    ) -> AutocompletionResponse:
        """Return suggested search terms similar to ``query`` (async)."""
        params = {"field": str(field), "q": query}
        return await self._afetch(AutocompletionResponse, "autocompletions", params)

    # -- field metadata -------------------------------------------------
    def fields(self) -> FieldsResponse:
        """Return technical metadata describing the API's LEI data fields."""
        return self._fetch(FieldsResponse, "fields")

    async def afields(self) -> FieldsResponse:
        """Return technical metadata describing the API's LEI data fields.

        Async counterpart of :meth:`fields`.
        """
        return await self._afetch(FieldsResponse, "fields")

    def get_field(self, field_id: str) -> FieldResponse:
        """Return the metadata of a single LEI data field."""
        return self._fetch(FieldResponse, f"fields/{field_id}")

    async def aget_field(self, field_id: str) -> FieldResponse:
        """Return the metadata of a single LEI data field (async)."""
        return await self._afetch(FieldResponse, f"fields/{field_id}")

    # -- LEI and vLEI issuers ----------------------------------------------
    def lei_issuers(
        self,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> LeiIssuersResponse:
        """Return the accredited LEI issuers (LOUs)."""
        params = self._page_params(page_number, page_size)
        return self._fetch(LeiIssuersResponse, "lei-issuers", params)

    async def alei_issuers(
        self,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> LeiIssuersResponse:
        """Return the accredited LEI issuers (async)."""
        params = self._page_params(page_number, page_size)
        return await self._afetch(LeiIssuersResponse, "lei-issuers", params)

    def get_lei_issuer(self, issuer_id: str) -> LeiIssuerResponse:
        """Return a single LEI issuer by its LEI.

        ``issuer_id`` is the issuer's own LEI code; for the issuer of a
        given LEI record use :meth:`lei_issuer`.
        """
        return self._fetch(LeiIssuerResponse, f"lei-issuers/{issuer_id}")

    async def aget_lei_issuer(self, issuer_id: str) -> LeiIssuerResponse:
        """Return a single LEI issuer by its LEI (async)."""
        return await self._afetch(LeiIssuerResponse, f"lei-issuers/{issuer_id}")

    def lei_issuer_jurisdictions(
        self,
        issuer_id: str,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> LeiIssuerJurisdictionsResponse:
        """Return the jurisdictions an LEI issuer is accredited for."""
        params = self._page_params(page_number, page_size)
        return self._fetch(
            LeiIssuerJurisdictionsResponse,
            f"lei-issuers/{issuer_id}/jurisdictions",
            params,
        )

    async def alei_issuer_jurisdictions(
        self,
        issuer_id: str,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> LeiIssuerJurisdictionsResponse:
        """Return the jurisdictions an LEI issuer is accredited for (async)."""
        params = self._page_params(page_number, page_size)
        return await self._afetch(
            LeiIssuerJurisdictionsResponse,
            f"lei-issuers/{issuer_id}/jurisdictions",
            params,
        )

    def vlei_issuers(
        self,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> VLeiIssuersResponse:
        """Return the qualified vLEI issuing organizations."""
        params = self._page_params(page_number, page_size)
        return self._fetch(VLeiIssuersResponse, "vlei-issuers", params)

    async def avlei_issuers(
        self,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> VLeiIssuersResponse:
        """Return the qualified vLEI issuing organizations (async)."""
        params = self._page_params(page_number, page_size)
        return await self._afetch(VLeiIssuersResponse, "vlei-issuers", params)

    def get_vlei_issuer(self, issuer_id: str) -> VLeiIssuerResponse:
        """Return a single vLEI issuer by its LEI."""
        return self._fetch(VLeiIssuerResponse, f"vlei-issuers/{issuer_id}")

    async def aget_vlei_issuer(self, issuer_id: str) -> VLeiIssuerResponse:
        """Return a single vLEI issuer by its LEI (async)."""
        return await self._afetch(VLeiIssuerResponse, f"vlei-issuers/{issuer_id}")

    # -- reference data ----------------------------------------------------
    def countries(
        self,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> CountriesResponse:
        """Return the ISO 3166 country codes."""
        params = self._page_params(page_number, page_size)
        return self._fetch(CountriesResponse, "countries", params)

    async def acountries(
        self,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> CountriesResponse:
        """Return the ISO 3166 country codes (async)."""
        params = self._page_params(page_number, page_size)
        return await self._afetch(CountriesResponse, "countries", params)

    def get_country(self, code: str) -> CountryResponse:
        """Return a single country by its ISO 3166 code."""
        return self._fetch(CountryResponse, f"countries/{code}")

    async def aget_country(self, code: str) -> CountryResponse:
        """Return a single country by its ISO 3166 code (async)."""
        return await self._afetch(CountryResponse, f"countries/{code}")

    def entity_legal_forms(
        self,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> EntityLegalFormsResponse:
        """Return the ISO 20275 entity legal form (ELF) codes."""
        params = self._page_params(page_number, page_size)
        return self._fetch(EntityLegalFormsResponse, "entity-legal-forms", params)

    async def aentity_legal_forms(
        self,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> EntityLegalFormsResponse:
        """Return the ISO 20275 entity legal form codes (async)."""
        params = self._page_params(page_number, page_size)
        return await self._afetch(
            EntityLegalFormsResponse,
            "entity-legal-forms",
            params,
        )

    def get_entity_legal_form(self, elf_code: str) -> EntityLegalFormResponse:
        """Return a single entity legal form by its ELF code."""
        return self._fetch(EntityLegalFormResponse, f"entity-legal-forms/{elf_code}")

    async def aget_entity_legal_form(self, elf_code: str) -> EntityLegalFormResponse:
        """Return a single entity legal form by its ELF code (async)."""
        return await self._afetch(
            EntityLegalFormResponse,
            f"entity-legal-forms/{elf_code}",
        )

    def official_organizational_roles(
        self,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> OfficialOrganizationalRolesResponse:
        """Return the ISO 5009 official organizational role (OOR) codes."""
        params = self._page_params(page_number, page_size)
        return self._fetch(
            OfficialOrganizationalRolesResponse,
            "official-organizational-roles",
            params,
        )

    async def aofficial_organizational_roles(
        self,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> OfficialOrganizationalRolesResponse:
        """Return the ISO 5009 OOR codes (async)."""
        params = self._page_params(page_number, page_size)
        return await self._afetch(
            OfficialOrganizationalRolesResponse,
            "official-organizational-roles",
            params,
        )

    def get_official_organizational_role(
        self,
        role_id: str,
    ) -> OfficialOrganizationalRoleResponse:
        """Return a single official organizational role by its OOR code."""
        return self._fetch(
            OfficialOrganizationalRoleResponse,
            f"official-organizational-roles/{role_id}",
        )

    async def aget_official_organizational_role(
        self,
        role_id: str,
    ) -> OfficialOrganizationalRoleResponse:
        """Return a single official organizational role (async)."""
        return await self._afetch(
            OfficialOrganizationalRoleResponse,
            f"official-organizational-roles/{role_id}",
        )

    def jurisdictions(
        self,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> JurisdictionsResponse:
        """Return the legal jurisdictions."""
        params = self._page_params(page_number, page_size)
        return self._fetch(JurisdictionsResponse, "jurisdictions", params)

    async def ajurisdictions(
        self,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> JurisdictionsResponse:
        """Return the legal jurisdictions (async)."""
        params = self._page_params(page_number, page_size)
        return await self._afetch(JurisdictionsResponse, "jurisdictions", params)

    def get_jurisdiction(self, jurisdiction_id: str) -> JurisdictionResponse:
        """Return a single legal jurisdiction by its code."""
        return self._fetch(JurisdictionResponse, f"jurisdictions/{jurisdiction_id}")

    async def aget_jurisdiction(self, jurisdiction_id: str) -> JurisdictionResponse:
        """Return a single legal jurisdiction by its code (async)."""
        return await self._afetch(
            JurisdictionResponse,
            f"jurisdictions/{jurisdiction_id}",
        )

    def regions(
        self,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> RegionsResponse:
        """Return the ISO 3166 sub-region codes."""
        params = self._page_params(page_number, page_size)
        return self._fetch(RegionsResponse, "regions", params)

    async def aregions(
        self,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> RegionsResponse:
        """Return the ISO 3166 sub-region codes (async)."""
        params = self._page_params(page_number, page_size)
        return await self._afetch(RegionsResponse, "regions", params)

    def get_region(self, region_id: str) -> RegionResponse:
        """Return a single region by its ISO 3166 sub-region code."""
        return self._fetch(RegionResponse, f"regions/{region_id}")

    async def aget_region(self, region_id: str) -> RegionResponse:
        """Return a single region by its sub-region code (async)."""
        return await self._afetch(RegionResponse, f"regions/{region_id}")

    def registration_authorities(
        self,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> RegistrationAuthoritiesResponse:
        """Return the GLEIF registration authority (RA) codes."""
        params = self._page_params(page_number, page_size)
        return self._fetch(
            RegistrationAuthoritiesResponse,
            "registration-authorities",
            params,
        )

    async def aregistration_authorities(
        self,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> RegistrationAuthoritiesResponse:
        """Return the GLEIF registration authority codes (async)."""
        params = self._page_params(page_number, page_size)
        return await self._afetch(
            RegistrationAuthoritiesResponse,
            "registration-authorities",
            params,
        )

    def get_registration_authority(
        self,
        authority_id: str,
    ) -> RegistrationAuthorityResponse:
        """Return a single registration authority by its RA code."""
        return self._fetch(
            RegistrationAuthorityResponse,
            f"registration-authorities/{authority_id}",
        )

    async def aget_registration_authority(
        self,
        authority_id: str,
    ) -> RegistrationAuthorityResponse:
        """Return a single registration authority by its RA code (async)."""
        return await self._afetch(
            RegistrationAuthorityResponse,
            f"registration-authorities/{authority_id}",
        )

    def registration_agents(
        self,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> RegistrationAgentsResponse:
        """Return the registration agents."""
        params = self._page_params(page_number, page_size)
        return self._fetch(RegistrationAgentsResponse, "registration-agents", params)

    async def aregistration_agents(
        self,
        *,
        page_number: int = 1,
        page_size: int = 15,
    ) -> RegistrationAgentsResponse:
        """Return the registration agents (async)."""
        params = self._page_params(page_number, page_size)
        return await self._afetch(
            RegistrationAgentsResponse,
            "registration-agents",
            params,
        )

    def get_registration_agent(self, agent_id: str) -> RegistrationAgentResponse:
        """Return a single registration agent by its ID."""
        return self._fetch(
            RegistrationAgentResponse,
            f"registration-agents/{agent_id}",
        )

    async def aget_registration_agent(
        self,
        agent_id: str,
    ) -> RegistrationAgentResponse:
        """Return a single registration agent by its ID (async)."""
        return await self._afetch(
            RegistrationAgentResponse,
            f"registration-agents/{agent_id}",
        )

    # -- export -------------------------------------------------------------
    def export_lei_records(
        self,
        *,
        export_format: ExportFormat | str = ExportFormat.CSV,
        filters: dict[str, str] | None = None,
        sort: str | None = None,
    ) -> bytes:
        """Export LEI records as a file and return its raw bytes.

        Hits ``https://api.gleif.org/export/v1/lei-records.{format}``. The
        server caps exports at 5000 records; narrow the result with the
        same ``filters`` accepted by :meth:`search`.
        """
        fmt = ExportFormat(export_format)
        params = self._filter_params(filters, sort)
        return self._transport.get_raw(
            f"lei-records.{fmt.value}",
            params or None,
            base_url=EXPORT_BASE_URL,
        )

    async def aexport_lei_records(
        self,
        *,
        export_format: ExportFormat | str = ExportFormat.CSV,
        filters: dict[str, str] | None = None,
        sort: str | None = None,
    ) -> bytes:
        """Export LEI records as a file and return its raw bytes (async)."""
        fmt = ExportFormat(export_format)
        params = self._filter_params(filters, sort)
        return await self._transport.aget_raw(
            f"lei-records.{fmt.value}",
            params or None,
            base_url=EXPORT_BASE_URL,
        )

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

    async def ahealthcheck(self) -> bool:
        """Return whether the API is reachable (async).

        Issues a minimal ``/fields`` request; any transport error surfaces
        as a ``False`` result rather than raising.
        """
        try:
            await self._transport.aget("fields", {"page[size]": 1})
        except Exception:  # noqa: BLE001 - healthcheck must not raise
            return False
        return True

    # -- lifecycle --------------------------------------------------------
    def close(self) -> None:
        """Close the underlying sync transport connection pool."""
        self._transport.close()

    async def aclose(self) -> None:
        """Close the underlying async transport connection pool."""
        await self._transport.aclose()

    def __enter__(self) -> Self:
        """Enter the sync context manager."""
        return self

    def __exit__(self, *exc_info: object) -> None:
        """Close the client on context exit."""
        self.close()

    async def __aenter__(self) -> Self:
        """Enter the async context manager."""
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        """Close the client on context exit."""
        await self.aclose()

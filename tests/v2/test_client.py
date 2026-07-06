"""v2 namespace tests (offline via a fake transport)."""

from __future__ import annotations

import asyncio
from typing import Any

from pygleif.compat.interfaces import BaseApiClient
from pygleif.v2 import GleifClient

from .conftest import FakeTransport, PagedFakeTransport, load_fixture


def _client_for_single_record() -> tuple[GleifClient, FakeTransport]:
    """Build a client backed by the issued LEI fixture."""
    lei = "9845001B2AD43E664E58"
    payload = load_fixture(f"{lei}_issued")
    transport = FakeTransport({f"lei-records/{lei}": payload})
    return GleifClient(transport=transport), transport


def test_v2_client_implements_protocol() -> None:
    """v2 client should satisfy the shared interface."""
    client = GleifClient()
    assert isinstance(client, BaseApiClient)


def test_v2_get_lei_record_parses_fixture() -> None:
    """The full LEI record should parse into the v2 models."""
    client, _ = _client_for_single_record()
    response = client.get_lei_record("9845001B2AD43E664E58")
    assert response.data.attributes.lei == "9845001B2AD43E664E58"


def test_v2_get_lei_returns_normalized_dto() -> None:
    """get_lei should return a normalized compatibility DTO."""
    client, _ = _client_for_single_record()
    record = client.get_lei("9845001B2AD43E664E58")
    assert record.lei == "9845001B2AD43E664E58"
    assert record.country is not None


def test_v2_get_lei_record_parses_lapsed_fixture() -> None:
    """A second real record (lapsed) should parse into the v2 models."""
    lei = "549300LBI3LRIZ2V8V66"
    transport = FakeTransport({f"lei-records/{lei}": load_fixture(f"{lei}_lapsed")})
    client = GleifClient(transport=transport)
    response = client.get_lei_record(lei)
    assert response.data.attributes.lei == lei


def test_v2_get_lei_record_parses_sparse_record() -> None:
    """A record with only CDF-mandatory fields should parse tolerantly."""
    lei = "SPARSE00000000000001"
    transport = FakeTransport({f"lei-records/{lei}": load_fixture("sparse_record")})
    client = GleifClient(transport=transport)
    response = client.get_lei_record(lei)
    entity = response.data.attributes.entity
    assert entity.legal_name.name == "Sparse Example AB"
    assert entity.legal_address.country == "SE"
    assert entity.headquarters_address is None
    assert entity.other_names == []
    assert response.data.attributes.registration.validated_at is None
    assert response.data.relationships is None


def test_v2_pagination_parses_from_key() -> None:
    """The reserved ``from`` key should map to ``from_``."""
    payload = {
        "meta": {
            "pagination": {
                "currentPage": 1,
                "perPage": 15,
                "from": 1,
                "to": 15,
                "total": 100,
                "lastPage": 7,
            },
        },
        "data": [],
    }
    transport = FakeTransport({"lei-records": payload})
    client = GleifClient(transport=transport)
    pagination = client.search().meta.pagination
    assert pagination is not None
    assert pagination.from_ == 1
    assert pagination.model_dump(by_alias=True)["from"] == 1


def test_v2_search_builds_filter_params() -> None:
    """Search should wrap filter keys as filter[...] and paginate."""
    transport = FakeTransport({"lei-records": {"meta": {}, "data": []}})
    client = GleifClient(transport=transport)
    client.search(filters={"fulltext": "bank"}, sort="entity.legalName", page_size=5)
    path, params = transport.calls[0]
    assert path == "lei-records"
    assert params["filter[fulltext]"] == "bank"
    assert params["sort"] == "entity.legalName"
    assert params["page[size]"] == 5


def test_v2_search_supports_owns_and_ownedby_filters() -> None:
    """The documented owns/ownedBy filters should pass through search."""
    transport = FakeTransport({"lei-records": {"meta": {}, "data": []}})
    client = GleifClient(transport=transport)
    client.search(filters={"owns": "315700WQBDF1ZVVE0T64"})
    client.search(filters={"ownedBy": "529900IYQRX2JSSIZA36"})
    assert transport.calls[0][1]["filter[owns]"] == "315700WQBDF1ZVVE0T64"
    assert transport.calls[1][1]["filter[ownedBy]"] == "529900IYQRX2JSSIZA36"


def test_v2_isins_parses_payload() -> None:
    """Isins should parse the ISIN mapping envelope."""
    lei = "5493001KJTIIGC8Y1R12"
    payload = {
        "meta": {},
        "data": [
            {
                "type": "isins",
                "id": "1",
                "attributes": {"lei": lei, "isin": "DE000ST8MPP0"},
            },
        ],
    }
    transport = FakeTransport({f"lei-records/{lei}/isins": payload})
    client = GleifClient(transport=transport)
    result = client.isins(lei)
    assert result.data[0].attributes.isin == "DE000ST8MPP0"


def test_v2_fuzzy_completions_parses_payload() -> None:
    """fuzzy_completions should parse matched values."""
    payload = {
        "data": [
            {"type": "fuzzycompletions", "attributes": {"value": "Factbook"}},
        ],
    }
    transport = FakeTransport({"fuzzycompletions": payload})
    client = GleifClient(transport=transport)
    result = client.fuzzy_completions("factbook")
    assert result.data[0].attributes.value == "Factbook"
    assert transport.calls[0][1] == {"field": "fulltext", "q": "factbook"}


def test_v2_fields_parses_payload() -> None:
    """Fields should parse the field metadata envelope."""
    payload = {
        "data": [
            {
                "type": "fields",
                "id": "lei",
                "attributes": {"key": "lei", "dataType": "STRING", "sortable": True},
            },
        ],
    }
    transport = FakeTransport({"fields": payload})
    client = GleifClient(transport=transport)
    result = client.fields()
    assert result.data[0].attributes.data_type == "STRING"


def test_v2_convenience_searches_build_filter_params() -> None:
    """search_fulltext/by_bic/by_isin should map to the right filters."""
    transport = FakeTransport({"lei-records": {"meta": {}, "data": []}})
    client = GleifClient(transport=transport)
    client.search_fulltext("bank")
    client.by_bic("HELADEF1RRS")
    client.by_isin("DE000ST8MPP0")
    assert transport.calls[0][1]["filter[fulltext]"] == "bank"
    assert transport.calls[1][1]["filter[bic]"] == "HELADEF1RRS"
    assert transport.calls[2][1]["filter[isin]"] == "DE000ST8MPP0"


def test_v2_healthcheck_returns_true_on_success() -> None:
    """Healthcheck should return True when the transport succeeds."""
    transport = FakeTransport({"fields": {"meta": {}, "data": []}})
    client = GleifClient(transport=transport)
    assert client.healthcheck() is True


def test_v2_healthcheck_returns_false_on_error() -> None:
    """Healthcheck should swallow transport errors and return False."""

    class FailingTransport:
        def get(
            self,
            path: str,
            params: dict[str, Any] | None = None,
        ) -> dict[str, Any]:
            raise RuntimeError("boom")

    client = GleifClient(transport=FailingTransport())  # type: ignore[arg-type]
    assert client.healthcheck() is False


# -- pagination iterators ---------------------------------------------------


def _record_payload(lei: str) -> dict[str, Any]:
    """Build a minimal LEI record data object."""
    return {
        "id": lei,
        "type": "lei-records",
        "attributes": {
            "lei": lei,
            "entity": {
                "legalName": {"name": f"Entity {lei}"},
                "legalAddress": {"country": "SE"},
                "status": "ACTIVE",
            },
            "registration": {"status": "ISSUED"},
        },
    }


def _page_payload(
    records: list[dict[str, Any]],
    *,
    current_page: int,
    last_page: int,
    total: int,
) -> dict[str, Any]:
    """Build a search response page with pagination meta."""
    return {
        "meta": {
            "pagination": {
                "currentPage": current_page,
                "perPage": len(records),
                "from": 1,
                "to": len(records),
                "total": total,
                "lastPage": last_page,
            },
        },
        "data": records,
    }


def test_v2_iter_search_follows_pagination() -> None:
    """iter_search should yield records across all pages."""
    pages = [
        _page_payload(
            [_record_payload("LEI0000000000000001"), _record_payload("LEI0000000000000002")],
            current_page=1,
            last_page=2,
            total=3,
        ),
        _page_payload(
            [_record_payload("LEI0000000000000003")],
            current_page=2,
            last_page=2,
            total=3,
        ),
    ]
    transport = PagedFakeTransport({"lei-records": pages})
    client = GleifClient(transport=transport)
    records = list(client.iter_search(filters={"fulltext": "bank"}, page_size=2))
    assert [record.id for record in records] == [
        "LEI0000000000000001",
        "LEI0000000000000002",
        "LEI0000000000000003",
    ]
    assert [params["page[number]"] for _, params in transport.calls] == [1, 2]
    assert all(params["filter[fulltext]"] == "bank" for _, params in transport.calls)


def test_v2_iter_search_respects_max_records() -> None:
    """iter_search should stop once max_records have been yielded."""
    pages = [
        _page_payload(
            [_record_payload("LEI0000000000000001"), _record_payload("LEI0000000000000002")],
            current_page=1,
            last_page=5,
            total=10,
        ),
    ]
    transport = PagedFakeTransport({"lei-records": pages})
    client = GleifClient(transport=transport)
    records = list(client.iter_search(max_records=2))
    assert len(records) == 2
    assert len(transport.calls) == 1


def test_v2_iter_search_stops_on_empty_page() -> None:
    """iter_search should stop without a second request on empty data."""
    pages = [_page_payload([], current_page=1, last_page=3, total=0)]
    transport = PagedFakeTransport({"lei-records": pages})
    client = GleifClient(transport=transport)
    assert list(client.iter_search()) == []
    assert len(transport.calls) == 1


def test_v2_iter_search_stops_without_pagination_meta() -> None:
    """iter_search should stop after one page when meta lacks pagination."""
    payload = {"meta": {}, "data": [_record_payload("LEI0000000000000001")]}
    transport = PagedFakeTransport({"lei-records": [payload]})
    client = GleifClient(transport=transport)
    records = list(client.iter_search())
    assert len(records) == 1
    assert len(transport.calls) == 1


def test_v2_aiter_search_follows_pagination() -> None:
    """aiter_search should mirror iter_search for the async path."""
    pages = [
        _page_payload(
            [_record_payload("LEI0000000000000001")],
            current_page=1,
            last_page=2,
            total=2,
        ),
        _page_payload(
            [_record_payload("LEI0000000000000002")],
            current_page=2,
            last_page=2,
            total=2,
        ),
    ]
    transport = PagedFakeTransport({"lei-records": pages})
    client = GleifClient(transport=transport)

    async def _collect() -> list[str]:
        return [record.id async for record in client.aiter_search()]

    assert asyncio.run(_collect()) == [
        "LEI0000000000000001",
        "LEI0000000000000002",
    ]


# -- async counterparts --------------------------------------------------


def test_v2_aget_lei_record_parses_fixture() -> None:
    """aget_lei_record should mirror get_lei_record for the async path."""
    client, _ = _client_for_single_record()
    response = asyncio.run(client.aget_lei_record("9845001B2AD43E664E58"))
    assert response.data.attributes.lei == "9845001B2AD43E664E58"


def test_v2_aget_lei_returns_normalized_dto() -> None:
    """aget_lei should return a normalized compatibility DTO."""
    client, _ = _client_for_single_record()
    record = asyncio.run(client.aget_lei("9845001B2AD43E664E58"))
    assert record.lei == "9845001B2AD43E664E58"
    assert record.country is not None


def test_v2_asearch_builds_filter_params() -> None:
    """Asearch should wrap filter keys as filter[...] and paginate."""
    transport = FakeTransport({"lei-records": {"meta": {}, "data": []}})
    client = GleifClient(transport=transport)
    asyncio.run(
        client.asearch(
            filters={"fulltext": "bank"},
            sort="entity.legalName",
            page_size=5,
        ),
    )
    path, params = transport.calls[0]
    assert path == "lei-records"
    assert params["filter[fulltext]"] == "bank"
    assert params["sort"] == "entity.legalName"
    assert params["page[size]"] == 5


def test_v2_asearch_supports_owns_and_ownedby_filters() -> None:
    """The owns/ownedBy filters should pass through asearch."""
    transport = FakeTransport({"lei-records": {"meta": {}, "data": []}})
    client = GleifClient(transport=transport)
    asyncio.run(client.asearch(filters={"owns": "315700WQBDF1ZVVE0T64"}))
    asyncio.run(client.asearch(filters={"ownedBy": "529900IYQRX2JSSIZA36"}))
    assert transport.calls[0][1]["filter[owns]"] == "315700WQBDF1ZVVE0T64"
    assert transport.calls[1][1]["filter[ownedBy]"] == "529900IYQRX2JSSIZA36"


def test_v2_aisins_parses_payload() -> None:
    """Aisins should parse the ISIN mapping envelope."""
    lei = "5493001KJTIIGC8Y1R12"
    payload = {
        "meta": {},
        "data": [
            {
                "type": "isins",
                "id": "1",
                "attributes": {"lei": lei, "isin": "DE000ST8MPP0"},
            },
        ],
    }
    transport = FakeTransport({f"lei-records/{lei}/isins": payload})
    client = GleifClient(transport=transport)
    result = asyncio.run(client.aisins(lei))
    assert result.data[0].attributes.isin == "DE000ST8MPP0"


def test_v2_afuzzy_completions_parses_payload() -> None:
    """afuzzy_completions should parse matched values."""
    payload = {
        "data": [
            {"type": "fuzzycompletions", "attributes": {"value": "Factbook"}},
        ],
    }
    transport = FakeTransport({"fuzzycompletions": payload})
    client = GleifClient(transport=transport)
    result = asyncio.run(client.afuzzy_completions("factbook"))
    assert result.data[0].attributes.value == "Factbook"
    assert transport.calls[0][1] == {"field": "fulltext", "q": "factbook"}


def test_v2_afields_parses_payload() -> None:
    """Afields should parse the field metadata envelope."""
    payload = {
        "data": [
            {
                "type": "fields",
                "id": "lei",
                "attributes": {"key": "lei", "dataType": "STRING", "sortable": True},
            },
        ],
    }
    transport = FakeTransport({"fields": payload})
    client = GleifClient(transport=transport)
    result = asyncio.run(client.afields())
    assert result.data[0].attributes.data_type == "STRING"


def test_v2_ahealthcheck_returns_true_on_success() -> None:
    """Ahealthcheck should return True when the transport succeeds."""
    transport = FakeTransport({"fields": {"meta": {}, "data": []}})
    client = GleifClient(transport=transport)
    assert asyncio.run(client.ahealthcheck()) is True


def test_v2_ahealthcheck_returns_false_on_error() -> None:
    """Ahealthcheck should swallow transport errors and return False."""

    class FailingTransport:
        async def aget(
            self,
            path: str,
            params: dict[str, Any] | None = None,
        ) -> dict[str, Any]:
            raise RuntimeError("boom")

    client = GleifClient(transport=FailingTransport())  # type: ignore[arg-type]
    assert asyncio.run(client.ahealthcheck()) is False


def test_v2_async_context_manager_closes_transport() -> None:
    """The async context manager should close the transport on exit."""

    class TrackingTransport(FakeTransport):
        def __init__(self) -> None:
            super().__init__({})
            self.closed = False

        async def aclose(self) -> None:
            self.closed = True

    transport = TrackingTransport()

    async def _run() -> bool:
        async with GleifClient(transport=transport):
            pass
        return transport.closed

    assert asyncio.run(_run()) is True

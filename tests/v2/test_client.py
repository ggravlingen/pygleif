"""v2 namespace tests (offline via a fake transport)."""

from __future__ import annotations

import asyncio
from typing import Any

from pygleif.compat.interfaces import BaseApiClient
from pygleif.v2 import GleifClient

from .conftest import FakeTransport, load_fixture


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

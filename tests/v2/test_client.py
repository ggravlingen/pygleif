"""v2 namespace tests (offline via a fake transport)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pygleif.compat.interfaces import BaseApiClient
from pygleif.v2 import GleifClient

FIXTURE_DIR = Path(__file__).parent.parent / "v1" / "fixtures"


def _load(name: str) -> dict[str, Any]:
    """Load a JSON fixture from the shared v1 fixtures directory."""
    with (FIXTURE_DIR / f"{name}.json").open() as handle:
        return json.load(handle)


class FakeTransport:
    """Deterministic transport that returns canned payloads by path."""

    def __init__(self, responses: dict[str, dict[str, Any]]) -> None:
        """Store the path -> payload mapping."""
        self.responses = responses
        self.calls: list[tuple[str, dict[str, Any] | None]] = []

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Record the call and return the canned payload for ``path``."""
        self.calls.append((path, params))
        return self.responses[path]


def _client_for_single_record() -> tuple[GleifClient, FakeTransport]:
    """Build a client backed by the issued LEI fixture."""
    lei = "9845001B2AD43E664E58"
    payload = _load(f"{lei}_issued")
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
    """search should wrap filter keys as filter[...] and paginate."""
    transport = FakeTransport({"lei-records": {"meta": {}, "data": []}})
    client = GleifClient(transport=transport)
    client.search(filters={"fulltext": "bank"}, sort="entity.legalName", page_size=5)
    path, params = transport.calls[0]
    assert path == "lei-records"
    assert params["filter[fulltext]"] == "bank"
    assert params["sort"] == "entity.legalName"
    assert params["page[size]"] == 5


def test_v2_relationship_helpers_use_owns_and_ownedby() -> None:
    """owners/children should map to owns/ownedBy filters."""
    transport = FakeTransport({"lei-records": {"meta": {}, "data": []}})
    client = GleifClient(transport=transport)
    client.owners("315700WQBDF1ZVVE0T64")
    client.children("529900IYQRX2JSSIZA36")
    assert transport.calls[0][1]["filter[owns]"] == "315700WQBDF1ZVVE0T64"
    assert transport.calls[1][1]["filter[ownedBy]"] == "529900IYQRX2JSSIZA36"


def test_v2_isins_parses_payload() -> None:
    """isins should parse the ISIN mapping envelope."""
    lei = "5493001KJTIIGC8Y1R12"
    payload = {
        "meta": {},
        "data": [
            {"type": "isins", "id": "1", "attributes": {"lei": lei, "isin": "DE000ST8MPP0"}},
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
            {"type": "fuzzycompletions", "attributes": {"value": {"name": "Factbook"}}},
        ],
    }
    transport = FakeTransport({"fuzzycompletions": payload})
    client = GleifClient(transport=transport)
    result = client.fuzzy_completions("factbook")
    assert result.data[0].attributes.value.name == "Factbook"
    assert transport.calls[0][1] == {"field": "fulltext", "q": "factbook"}


def test_v2_fields_parses_payload() -> None:
    """fields should parse the field metadata envelope."""
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

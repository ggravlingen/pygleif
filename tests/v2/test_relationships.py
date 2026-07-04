"""Level 2 relationship and related-record endpoint tests (offline)."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from pygleif.v2 import GleifClient
from pygleif.v2.api import GLEIFResponse

from .conftest import FakeTransport, load_fixture

LEI = "529900W18LQJJN6SJ336"

RELATIONSHIP_PAYLOAD: dict[str, Any] = {
    "meta": {"goldenCopy": {"publishDate": "2026-07-04T00:00:00Z"}},
    "data": {
        "type": "relationship-records",
        "id": f"{LEI}|LEI|IS_DIRECTLY_CONSOLIDATED_BY|10|abc|",
        "attributes": {
            "validFrom": "2025-08-28T00:00:00Z",
            "validTo": None,
            "relationship": {
                "startNode": {"id": LEI, "type": "LEI"},
                "endNode": {"id": "O2RNE8IBXP4R0TD8PU41", "type": "LEI"},
                "type": "IS_DIRECTLY_CONSOLIDATED_BY",
                "status": "ACTIVE",
                "periods": [
                    {
                        "startDate": "2023-12-31T23:00:00Z",
                        "endDate": "2024-12-30T23:00:00Z",
                        "type": "ACCOUNTING_PERIOD",
                    },
                ],
            },
            "registration": {
                "initialRegistrationDate": "2017-10-25T12:09:30Z",
                "lastUpdateDate": "2025-08-27T14:35:08Z",
                "status": "PUBLISHED",
                "nextRenewalDate": "2026-10-17T22:00:00Z",
                "managingLou": "5299000J2N45DDNE4Y28",
                "corroborationLevel": "FULLY_CORROBORATED",
                "corroborationDocuments": "ACCOUNTS_FILING",
                "corroborationReference": None,
            },
        },
    },
}

EXCEPTION_PAYLOAD: dict[str, Any] = {
    "meta": {"goldenCopy": {"publishDate": "2026-07-04T00:00:00Z"}},
    "data": {
        "type": "reporting-exceptions",
        "id": f"{LEI}|0|abc|DIRECT_ACCOUNTING_CONSOLIDATION_PARENT|",
        "attributes": {
            "validFrom": None,
            "validTo": None,
            "lei": LEI,
            "category": "DIRECT_ACCOUNTING_CONSOLIDATION_PARENT",
            "reason": "NON_CONSOLIDATING",
            "reference": None,
        },
    },
}


def test_v2_parent_lookups_hit_dedicated_endpoints() -> None:
    """direct/ultimate parent should call the documented endpoints."""
    record = load_fixture("9845001B2AD43E664E58_issued")
    transport = FakeTransport(
        {
            f"lei-records/{LEI}/direct-parent": record,
            f"lei-records/{LEI}/ultimate-parent": record,
        },
    )
    client = GleifClient(transport=transport)
    assert isinstance(client.direct_parent(LEI), GLEIFResponse)
    assert isinstance(client.ultimate_parent(LEI), GLEIFResponse)
    assert transport.calls[0] == (f"lei-records/{LEI}/direct-parent", None)
    assert transport.calls[1] == (f"lei-records/{LEI}/ultimate-parent", None)


def test_v2_child_lookups_paginate() -> None:
    """direct/ultimate children should call their endpoints with pagination."""
    empty = {"meta": {}, "data": []}
    transport = FakeTransport(
        {
            f"lei-records/{LEI}/direct-children": empty,
            f"lei-records/{LEI}/ultimate-children": empty,
        },
    )
    client = GleifClient(transport=transport)
    client.direct_children(LEI, page_size=5)
    client.ultimate_children(LEI, page_number=2)
    assert transport.calls[0] == (
        f"lei-records/{LEI}/direct-children",
        {"page[number]": 1, "page[size]": 5},
    )
    assert transport.calls[1] == (
        f"lei-records/{LEI}/ultimate-children",
        {"page[number]": 2, "page[size]": 15},
    )


def test_v2_relationship_records_parse() -> None:
    """Relationship record responses should parse into typed models."""
    transport = FakeTransport(
        {f"lei-records/{LEI}/direct-parent-relationship": RELATIONSHIP_PAYLOAD},
    )
    client = GleifClient(transport=transport)
    result = client.direct_parent_relationship(LEI)
    relationship = result.data.attributes.relationship
    assert relationship is not None
    assert relationship.start_node is not None
    assert relationship.start_node.id == LEI
    assert relationship.status == "ACTIVE"
    assert relationship.periods[0].type == "ACCOUNTING_PERIOD"
    registration = result.data.attributes.registration
    assert registration is not None
    assert registration.managing_lou == "5299000J2N45DDNE4Y28"


def test_v2_child_relationship_lists_parse() -> None:
    """Child relationship list responses should parse into typed models."""
    payload = {"meta": {}, "data": [RELATIONSHIP_PAYLOAD["data"]]}
    transport = FakeTransport(
        {
            f"lei-records/{LEI}/direct-child-relationships": payload,
            f"lei-records/{LEI}/ultimate-child-relationships": payload,
        },
    )
    client = GleifClient(transport=transport)
    result = client.direct_child_relationships(LEI)
    assert result.data[0].attributes.valid_to is None
    client.ultimate_child_relationships(LEI, page_size=3)
    assert transport.calls[1][1] == {"page[number]": 1, "page[size]": 3}


def test_v2_reporting_exceptions_parse() -> None:
    """Reporting exception responses should parse into typed models."""
    transport = FakeTransport(
        {
            f"lei-records/{LEI}/direct-parent-reporting-exception": EXCEPTION_PAYLOAD,
            f"lei-records/{LEI}/ultimate-parent-reporting-exception": (
                EXCEPTION_PAYLOAD
            ),
        },
    )
    client = GleifClient(transport=transport)
    result = client.direct_parent_reporting_exception(LEI)
    assert result.data.attributes.reason == "NON_CONSOLIDATING"
    result = client.ultimate_parent_reporting_exception(LEI)
    assert result.data.attributes.category == (
        "DIRECT_ACCOUNTING_CONSOLIDATION_PARENT"
    )


def test_v2_related_record_endpoints() -> None:
    """lei-issuer/managing-lou/associated/successor should hit their paths."""
    record = load_fixture("9845001B2AD43E664E58_issued")
    issuer_payload = {
        "data": {
            "type": "lei-issuers",
            "id": "5299000J2N45DDNE4Y28",
            "attributes": {"lei": "5299000J2N45DDNE4Y28", "name": "Issuer"},
        },
    }
    transport = FakeTransport(
        {
            f"lei-records/{LEI}/lei-issuer": issuer_payload,
            f"lei-records/{LEI}/managing-lou": record,
            f"lei-records/{LEI}/associated-entity": record,
            f"lei-records/{LEI}/successor-entity": record,
        },
    )
    client = GleifClient(transport=transport)
    issuer = client.lei_issuer(LEI)
    assert issuer.data.attributes.name == "Issuer"
    assert isinstance(client.managing_lou(LEI), GLEIFResponse)
    assert isinstance(client.associated_entity(LEI), GLEIFResponse)
    assert isinstance(client.successor_entity(LEI), GLEIFResponse)
    assert [path for path, _ in transport.calls] == [
        f"lei-records/{LEI}/lei-issuer",
        f"lei-records/{LEI}/managing-lou",
        f"lei-records/{LEI}/associated-entity",
        f"lei-records/{LEI}/successor-entity",
    ]


def test_v2_field_modifications_builds_filter_params() -> None:
    """field_modifications should wrap its filters as filter[...] params."""
    payload = {
        "meta": {},
        "data": [
            {
                "type": "field-modifications",
                "id": "abc",
                "attributes": {
                    "lei": LEI,
                    "recordType": "RR",
                    "modificationType": "UPDATE",
                    "field": "/rr:Registration/rr:NextRenewalDate",
                    "date": "2025-08-28T00:00:00Z",
                    "valueOld": "2025-10-18",
                    "valueNew": "2026-10-18",
                    "context": {"relationshipType": "IS_DIRECTLY_CONSOLIDATED_BY"},
                },
            },
        ],
    }
    transport = FakeTransport({f"lei-records/{LEI}/field-modifications": payload})
    client = GleifClient(transport=transport)
    result = client.field_modifications(
        LEI,
        modification_type="UPDATE",
        record_type="RR",
        page_size=50,
    )
    assert result.data[0].attributes.modification_type == "UPDATE"
    params = transport.calls[0][1]
    assert params["filter[modificationType]"] == "UPDATE"
    assert params["filter[recordType]"] == "RR"
    assert "filter[field]" not in params
    assert params["page[size]"] == 50


def test_v2_lei_record_relationship_links_parse_kebab_case_keys() -> None:
    """The kebab-case relationship keys of real payloads must populate."""
    record = load_fixture("9845001B2AD43E664E58_issued")
    response = GLEIFResponse(**record)
    relationships = response.data.relationships
    assert relationships.managing_lou is not None
    assert relationships.managing_lou.links.related is not None
    assert relationships.lei_issuer is not None
    assert relationships.field_modifications is not None
    assert relationships.direct_parent is not None
    assert relationships.direct_parent.links.reporting_exception is not None


# -- async counterparts --------------------------------------------------


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("adirect_parent", "direct-parent"),
        ("aultimate_parent", "ultimate-parent"),
        ("amanaging_lou", "managing-lou"),
        ("aassociated_entity", "associated-entity"),
        ("asuccessor_entity", "successor-entity"),
    ],
)
def test_v2_async_single_record_lookups(method: str, path: str) -> None:
    """Async single-record lookups should hit the documented endpoints."""
    record = load_fixture("9845001B2AD43E664E58_issued")
    transport = FakeTransport({f"lei-records/{LEI}/{path}": record})
    client = GleifClient(transport=transport)
    result = asyncio.run(getattr(client, method)(LEI))
    assert isinstance(result, GLEIFResponse)
    assert transport.calls[0] == (f"lei-records/{LEI}/{path}", None)


def test_v2_async_relationship_records_parse() -> None:
    """Async relationship lookups should mirror the sync path."""
    payload = {"meta": {}, "data": [RELATIONSHIP_PAYLOAD["data"]]}
    transport = FakeTransport(
        {
            f"lei-records/{LEI}/ultimate-parent-relationship": RELATIONSHIP_PAYLOAD,
            f"lei-records/{LEI}/direct-child-relationships": payload,
        },
    )
    client = GleifClient(transport=transport)
    result = asyncio.run(client.aultimate_parent_relationship(LEI))
    relationship = result.data.attributes.relationship
    assert relationship is not None
    assert relationship.type == "IS_DIRECTLY_CONSOLIDATED_BY"
    listed = asyncio.run(client.adirect_child_relationships(LEI))
    assert listed.data[0].type == "relationship-records"


def test_v2_async_reporting_exception_parses() -> None:
    """Async reporting exception lookups should mirror the sync path."""
    transport = FakeTransport(
        {f"lei-records/{LEI}/direct-parent-reporting-exception": EXCEPTION_PAYLOAD},
    )
    client = GleifClient(transport=transport)
    result = asyncio.run(client.adirect_parent_reporting_exception(LEI))
    assert result.data.attributes.lei == LEI

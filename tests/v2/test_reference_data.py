"""Reference data, issuer, completion and field endpoint tests (offline)."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from pygleif.v2 import GleifClient

from .conftest import FakeTransport


def _list_payload(type_: str, attributes: dict[str, Any]) -> dict[str, Any]:
    """Build a minimal JSON:API list payload."""
    return {"meta": {}, "data": [{"type": type_, "id": "x", "attributes": attributes}]}


def _single_payload(type_: str, attributes: dict[str, Any]) -> dict[str, Any]:
    """Build a minimal JSON:API single-resource payload."""
    return {"data": {"type": type_, "id": "x", "attributes": attributes}}


@pytest.mark.parametrize(
    ("list_method", "detail_method", "path", "type_", "attributes"),
    [
        ("countries", "get_country", "countries", "countries", {"code": "US"}),
        (
            "jurisdictions",
            "get_jurisdiction",
            "jurisdictions",
            "jurisdictions",
            {"code": "US-DE"},
        ),
        ("regions", "get_region", "regions", "regions", {"code": "AD-07"}),
        (
            "entity_legal_forms",
            "get_entity_legal_form",
            "entity-legal-forms",
            "entity-legal-forms",
            {"code": "10UR", "names": [{"localName": "AB", "language": "sv"}]},
        ),
        (
            "official_organizational_roles",
            "get_official_organizational_role",
            "official-organizational-roles",
            "official-organizational-roles",
            {"code": "01D0O4", "elfCode": "AXSB"},
        ),
        (
            "registration_authorities",
            "get_registration_authority",
            "registration-authorities",
            "registration-authorities",
            {"code": "RA000001", "internationalName": "Registry"},
        ),
        (
            "registration_agents",
            "get_registration_agent",
            "registration-agents",
            "registration-agents",
            {"name": "Agent", "websites": ["https://example.com"]},
        ),
        (
            "lei_issuers",
            "get_lei_issuer",
            "lei-issuers",
            "lei-issuers",
            {"lei": "5299000J2N45DDNE4Y28", "name": "Issuer"},
        ),
        (
            "vlei_issuers",
            "get_vlei_issuer",
            "vlei-issuers",
            "vlei-issuers",
            {"lei": "549300O897ZC5H7CY412", "name": "QVI"},
        ),
    ],
)
def test_v2_catalog_resources_list_and_detail(
    list_method: str,
    detail_method: str,
    path: str,
    type_: str,
    attributes: dict[str, Any],
) -> None:
    """Each catalog resource should hit its list and detail endpoints."""
    transport = FakeTransport(
        {
            path: _list_payload(type_, attributes),
            f"{path}/x": _single_payload(type_, attributes),
        },
    )
    client = GleifClient(transport=transport)

    listed = getattr(client, list_method)(page_size=5)
    assert listed.data[0].type == type_
    assert transport.calls[0] == (path, {"page[number]": 1, "page[size]": 5})

    detail = getattr(client, detail_method)("x")
    assert detail.data.id == "x"
    assert transport.calls[1] == (f"{path}/x", None)

    alisted = asyncio.run(getattr(client, f"a{list_method}")())
    assert alisted.data[0].type == type_
    adetail = asyncio.run(getattr(client, f"a{detail_method}")("x"))
    assert adetail.data.id == "x"


def test_v2_catalog_attributes_are_typed() -> None:
    """Catalog responses should expose typed snake_case attributes."""
    transport = FakeTransport(
        {
            "countries": _list_payload("countries", {"code": "US", "name": "U.S."}),
            "entity-legal-forms/10UR": _single_payload(
                "entity-legal-forms",
                {
                    "code": "10UR",
                    "countryCode": "SE",
                    "names": [{"localName": "Aktiebolag", "languageCode": "sv"}],
                },
            ),
            "registration-authorities/RA000001": _single_payload(
                "registration-authorities",
                {
                    "code": "RA000001",
                    "internationalName": "Registry",
                    "jurisdictions": [{"countryCode": "IN"}],
                },
            ),
        },
    )
    client = GleifClient(transport=transport)
    assert client.countries().data[0].attributes.name == "U.S."
    elf = client.get_entity_legal_form("10UR").data.attributes
    assert elf.country_code == "SE"
    assert elf.names[0].local_name == "Aktiebolag"
    authority = client.get_registration_authority("RA000001").data.attributes
    assert authority.international_name == "Registry"
    assert authority.jurisdictions[0].country_code == "IN"


def test_v2_lei_issuer_jurisdictions() -> None:
    """lei_issuer_jurisdictions should hit the nested endpoint."""
    payload = _list_payload(
        "lei-issuer-accredited-jurisdictions",
        {"countryCode": "IN", "accreditedAs": "FULLY CORROBORATED"},
    )
    transport = FakeTransport({"lei-issuers/5299000J2N45DDNE4Y28/jurisdictions": payload})
    client = GleifClient(transport=transport)
    result = client.lei_issuer_jurisdictions("5299000J2N45DDNE4Y28")
    assert result.data[0].attributes.country_code == "IN"
    aresult = asyncio.run(client.alei_issuer_jurisdictions("5299000J2N45DDNE4Y28"))
    assert aresult.data[0].attributes.accredited_as == "FULLY CORROBORATED"


def test_v2_autocompletions_params_and_parse() -> None:
    """autocompletions should send field/q and parse suggestions."""
    payload = {
        "data": [
            {
                "type": "autocompletions",
                "attributes": {"value": "Global", "highlighting": "<b>Global</b>"},
                "relationships": {
                    "lei-records": {
                        "data": {"type": "lei-records", "id": "X"},
                        "links": {"related": "https://api.gleif.org/x"},
                    },
                },
            },
        ],
    }
    transport = FakeTransport({"autocompletions": payload})
    client = GleifClient(transport=transport)
    result = client.autocompletions("Global")
    assert transport.calls[0][1] == {"field": "fulltext", "q": "Global"}
    suggestion = result.data[0]
    assert suggestion.attributes.highlighting == "<b>Global</b>"
    assert suggestion.relationships is not None
    assert suggestion.relationships.lei_records is not None
    assert suggestion.relationships.lei_records.data.id == "X"

    aresult = asyncio.run(client.aautocompletions("Global", field="entity.legalName"))
    assert aresult.data[0].attributes.value == "Global"
    assert transport.calls[1][1] == {"field": "entity.legalName", "q": "Global"}


def test_v2_get_field_detail() -> None:
    """get_field should hit fields/{id} and parse the descriptor."""
    payload = {
        "data": {
            "type": "fields",
            "id": "LEIREC_FULLTEXT",
            "attributes": {"field": "fulltext", "sortable": False},
        },
    }
    transport = FakeTransport({"fields/LEIREC_FULLTEXT": payload})
    client = GleifClient(transport=transport)
    result = client.get_field("LEIREC_FULLTEXT")
    assert result.data.attributes.field == "fulltext"
    aresult = asyncio.run(client.aget_field("LEIREC_FULLTEXT"))
    assert aresult.data.id == "LEIREC_FULLTEXT"

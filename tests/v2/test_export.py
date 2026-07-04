"""Export endpoint and raw transport tests."""

from __future__ import annotations

import asyncio

import pytest

from pygleif.v2 import ExportFormat, GleifClient
from pygleif.v2.base import EXPORT_BASE_URL, Transport

from .conftest import FakeTransport


def test_v2_export_lei_records_uses_export_base_url() -> None:
    """export_lei_records should download from the /export/v1 base URL."""
    transport = FakeTransport(raw_responses={"lei-records.csv": b"LEI,LegalName\n"})
    client = GleifClient(transport=transport)
    payload = client.export_lei_records(
        filters={"entity.legalAddress.country": "SE"},
    )
    assert payload.startswith(b"LEI,")
    path, params, base_url = transport.raw_calls[0]
    assert path == "lei-records.csv"
    assert params == {"filter[entity.legalAddress.country]": "SE"}
    assert base_url == EXPORT_BASE_URL


def test_v2_export_lei_records_accepts_format_strings() -> None:
    """export_lei_records should accept plain format strings."""
    transport = FakeTransport(raw_responses={"lei-records.xlsx": b"PK"})
    client = GleifClient(transport=transport)
    assert client.export_lei_records(export_format="xlsx") == b"PK"
    assert transport.raw_calls[0][0] == "lei-records.xlsx"
    with pytest.raises(ValueError, match="pdf"):
        client.export_lei_records(export_format="pdf")


def test_v2_aexport_lei_records() -> None:
    """aexport_lei_records should mirror the sync export path."""
    transport = FakeTransport(raw_responses={"lei-records.json": b"[]"})
    client = GleifClient(transport=transport)
    payload = asyncio.run(
        client.aexport_lei_records(export_format=ExportFormat.JSON, sort="lei"),
    )
    assert payload == b"[]"
    path, params, base_url = transport.raw_calls[0]
    assert path == "lei-records.json"
    assert params == {"sort": "lei"}
    assert base_url == EXPORT_BASE_URL


def test_transport_build_url_supports_base_url_override() -> None:
    """_build_url should honor the per-request base URL override."""
    transport = Transport()
    url = transport._build_url(  # noqa: SLF001 - unit test of the helper
        "lei-records.csv",
        {"filter[lei]": "X"},
        base_url=EXPORT_BASE_URL,
    )
    assert url == f"{EXPORT_BASE_URL}/lei-records.csv?filter[lei]=X"

"""Compatibility tests that must pass under both pydantic namespaces."""

from __future__ import annotations

from pygleif.compat.adapters import normalize_record
from pygleif.compat.interfaces import BaseApiClient, RecordLike
from pygleif.compat.pydantic_support import PydanticNamespace


def test_namespace_detected(namespace_info) -> None:
    """The active pydantic namespace should be detected."""
    assert namespace_info.name in {PydanticNamespace.V1, PydanticNamespace.V2}


def test_normalize_record_produces_recordlike() -> None:
    """The adapter should build a frozen RecordLike DTO."""
    record = normalize_record(lei="1", legal_name="A", country="SE")
    assert isinstance(record, RecordLike)
    assert record.lei == "1"


def test_v1_client_conforms_to_protocol() -> None:
    """The frozen v1 client should satisfy the shared interface."""
    from pygleif.v1 import LegacyClient

    assert isinstance(LegacyClient(), BaseApiClient)


def test_v2_client_conforms_to_protocol() -> None:
    """The v2 client should satisfy the shared interface."""
    from pygleif.v2 import GleifClient

    assert isinstance(GleifClient(), BaseApiClient)


def test_backwards_compatible_toplevel_imports() -> None:
    """Historical top-level imports must keep resolving."""
    from pygleif import PyGleif, Search  # noqa: F401

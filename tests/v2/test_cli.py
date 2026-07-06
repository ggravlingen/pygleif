"""Tests for the pygleif CLI (offline via a fake transport)."""

from __future__ import annotations

from typing import Any

import pytest

from pygleif import __main__ as cli
from pygleif.v2 import GleifClient
from pygleif.v2.error import PyGLEIFNotFoundError

from .conftest import FakeTransport, load_fixture

LEI = "9845001B2AD43E664E58"


def _patch_client(monkeypatch: pytest.MonkeyPatch, transport: Any) -> None:
    """Make the CLI build clients backed by the given transport."""
    monkeypatch.setattr(
        cli,
        "GleifClient",
        lambda: GleifClient(transport=transport),
    )


def test_cli_get_prints_record(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``pygleif get`` should print the record JSON and exit 0."""
    transport = FakeTransport({f"lei-records/{LEI}": load_fixture(f"{LEI}_issued")})
    _patch_client(monkeypatch, transport)
    assert cli.main(["get", LEI]) == 0
    assert LEI in capsys.readouterr().out


def test_cli_get_summary_prints_normalized_record(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``pygleif --summary get`` should print the compact DTO."""
    transport = FakeTransport({f"lei-records/{LEI}": load_fixture(f"{LEI}_issued")})
    _patch_client(monkeypatch, transport)
    assert cli.main(["--summary", "get", LEI]) == 0
    out = capsys.readouterr().out
    assert '"legal_name"' in out


def test_cli_error_exits_nonzero(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A GLEIF error should print to stderr and exit 1."""

    class RaisingTransport:
        def get(
            self,
            path: str,
            params: dict[str, Any] | None = None,
        ) -> dict[str, Any]:
            raise PyGLEIFNotFoundError("Resource not found")

    _patch_client(monkeypatch, RaisingTransport())
    assert cli.main(["get", "UNKNOWN0000000000000"]) == 1
    assert "error:" in capsys.readouterr().err

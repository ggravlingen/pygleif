"""Tests for the pygleif CLI (offline via a fake transport)."""

from __future__ import annotations

from typing import Any

import pytest

from pygleif import __main__ as cli
from pygleif.v2 import GleifClient
from pygleif.v2.error import (
    PyGLEIFApiError,
    PyGLEIFNotFoundError,
    PyGLEIFRateLimitError,
)

from .conftest import FakeTransport, load_fixture

LEI = "9845001B2AD43E664E58"


class _RaisingTransport:
    """A transport whose ``get`` raises the given error, once constructed."""

    def __init__(self, exc: BaseException) -> None:
        """Store the error to raise on ``get``."""
        self._exc = exc

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Raise the configured error instead of returning data."""
        raise self._exc

    def close(self) -> None:
        """No-op close to satisfy the transport duck type."""


def _patch_client(monkeypatch: pytest.MonkeyPatch, transport: Any) -> None:
    """Make the CLI build clients backed by the given transport."""
    monkeypatch.setattr(
        cli,
        "GleifClient",
        lambda **_kwargs: GleifClient(transport=transport),
    )


def test_cli_get_prints_record(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``pygleif get`` should print the record JSON and exit 0."""
    transport = FakeTransport({f"lei-records/{LEI}": load_fixture(f"{LEI}_issued")})
    _patch_client(monkeypatch, transport)
    assert cli.main(["get", LEI]) == cli.EXIT_OK
    assert LEI in capsys.readouterr().out


def test_cli_get_summary_prints_normalized_record(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``pygleif --summary get`` should print the compact DTO."""
    transport = FakeTransport({f"lei-records/{LEI}": load_fixture(f"{LEI}_issued")})
    _patch_client(monkeypatch, transport)
    assert cli.main(["--summary", "get", LEI]) == cli.EXIT_OK
    out = capsys.readouterr().out
    assert '"legal_name"' in out


def test_cli_generic_error_exits_1(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A generic GLEIF API error should print to stderr and exit 1."""
    _patch_client(
        monkeypatch,
        _RaisingTransport(PyGLEIFApiError("boom")),
    )
    assert cli.main(["get", "UNKNOWN0000000000000"]) == cli.EXIT_ERROR
    assert "error:" in capsys.readouterr().err


def test_cli_not_found_exits_with_dedicated_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A 404 should exit with a distinct code so scripts can branch on it."""
    _patch_client(
        monkeypatch,
        _RaisingTransport(PyGLEIFNotFoundError("Resource not found")),
    )
    assert cli.main(["get", "UNKNOWN0000000000000"]) == cli.EXIT_NOT_FOUND


def test_cli_rate_limit_exits_with_dedicated_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A 429 should exit with a distinct code so scripts can branch on it."""
    _patch_client(
        monkeypatch,
        _RaisingTransport(PyGLEIFRateLimitError("rate limited")),
    )
    assert cli.main(["get", LEI]) == cli.EXIT_RATE_LIMITED


def test_cli_keyboard_interrupt_exits_130(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ctrl-C during a request should exit 130, not dump a traceback."""
    _patch_client(monkeypatch, _RaisingTransport(KeyboardInterrupt()))
    assert cli.main(["get", LEI]) == cli.EXIT_INTERRUPTED
    assert "interrupted" in capsys.readouterr().err


def test_cli_passes_timeout_and_retries_to_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``--timeout``/``--retries`` should reach the constructed client."""
    seen: dict[str, Any] = {}
    transport = FakeTransport({f"lei-records/{LEI}": load_fixture(f"{LEI}_issued")})

    def fake_client(**kwargs: Any) -> GleifClient:
        seen.update(kwargs)
        return GleifClient(transport=transport)

    monkeypatch.setattr(cli, "GleifClient", fake_client)
    assert cli.main(["--timeout", "5", "--retries", "1", "get", LEI]) == cli.EXIT_OK
    assert seen == {"timeout": 5.0, "retries": 1, "requests_per_minute": 60}


def test_cli_rate_limit_zero_disables_pacing(monkeypatch: pytest.MonkeyPatch) -> None:
    """``--rate-limit 0`` should reach the client as ``requests_per_minute=None``."""
    seen: dict[str, Any] = {}
    transport = FakeTransport({f"lei-records/{LEI}": load_fixture(f"{LEI}_issued")})

    def fake_client(**kwargs: Any) -> GleifClient:
        seen.update(kwargs)
        return GleifClient(transport=transport)

    monkeypatch.setattr(cli, "GleifClient", fake_client)
    assert cli.main(["--rate-limit", "0", "get", LEI]) == cli.EXIT_OK
    assert seen["requests_per_minute"] is None

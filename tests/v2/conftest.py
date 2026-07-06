"""Shared test helpers for the v2 suite (offline fake transport)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURE_DIR = Path(__file__).parent / "fixtures"
V1_FIXTURE_DIR = Path(__file__).parent.parent / "v1" / "fixtures"


def load_fixture(name: str) -> dict[str, Any]:
    """Load a JSON fixture, falling back to the shared v1 fixtures."""
    path = FIXTURE_DIR / f"{name}.json"
    if not path.exists():
        path = V1_FIXTURE_DIR / f"{name}.json"
    with path.open() as handle:
        return json.load(handle)


class FakeTransport:
    """Deterministic transport that returns canned payloads by path."""

    def __init__(
        self,
        responses: dict[str, dict[str, Any]] | None = None,
        raw_responses: dict[str, bytes] | None = None,
    ) -> None:
        """Store the path -> payload mappings."""
        self.responses = responses or {}
        self.raw_responses = raw_responses or {}
        self.calls: list[tuple[str, dict[str, Any] | None]] = []
        self.raw_calls: list[tuple[str, dict[str, Any] | None, str | None]] = []

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Record the call and return the canned payload for ``path``."""
        self.calls.append((path, params))
        return self.responses[path]

    async def aget(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Async counterpart of :meth:`get`, backed by the same canned data."""
        return self.get(path, params)

    def get_raw(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        base_url: str | None = None,
    ) -> bytes:
        """Record the call and return the canned bytes for ``path``."""
        self.raw_calls.append((path, params, base_url))
        return self.raw_responses[path]

    async def aget_raw(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        base_url: str | None = None,
    ) -> bytes:
        """Async counterpart of :meth:`get_raw`."""
        return self.get_raw(path, params, base_url=base_url)

    def close(self) -> None:
        """No-op close to satisfy the transport duck type."""

    async def aclose(self) -> None:
        """No-op close to satisfy the transport duck type."""


class PagedFakeTransport(FakeTransport):
    """Fake transport that serves successive payloads per path.

    Unlike :class:`FakeTransport`, each call to ``get`` for a path pops
    the next payload from its list, which lets tests exercise pagination
    where the same path is requested repeatedly.
    """

    def __init__(self, pages: dict[str, list[dict[str, Any]]]) -> None:
        """Store the path -> list-of-payloads mappings."""
        super().__init__({})
        self.pages = {path: list(payloads) for path, payloads in pages.items()}

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Record the call and pop the next canned payload for ``path``."""
        self.calls.append((path, params))
        return self.pages[path].pop(0)

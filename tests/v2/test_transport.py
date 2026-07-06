"""Tests for the httpx-backed v2 Transport (offline via httpx.MockTransport)."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
import pytest

from pygleif.v2.base import (
    EXPORT_BASE_URL,
    JSON_API_ACCEPT,
    MAX_RETRY_DELAY_SECONDS,
    Transport,
    _retry_delay,
)
from pygleif.v2.error import (
    PyGLEIFApiError,
    PyGLEIFNotFoundError,
    PyGLEIFRateLimitError,
)


def _transport_for(handler: Any, **kwargs: Any) -> Transport:
    """Build a Transport whose sync and async clients hit the handler."""
    mock = httpx.MockTransport(handler)
    return Transport(httpx_transport=mock, httpx_async_transport=mock, **kwargs)


# -- error mapping ---------------------------------------------------------


def test_transport_maps_404_to_not_found() -> None:
    """A 404 should raise PyGLEIFNotFoundError with request context."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"errors": [{"title": "Not Found"}]})

    transport = _transport_for(handler)
    with pytest.raises(PyGLEIFNotFoundError) as excinfo:
        transport.get("lei-records/UNKNOWN")
    assert excinfo.value.status_code == 404
    assert excinfo.value.url is not None
    assert excinfo.value.url.endswith("lei-records/UNKNOWN")


def test_transport_maps_429_to_rate_limit_with_retry_after() -> None:
    """A 429 should raise PyGLEIFRateLimitError carrying Retry-After."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, headers={"Retry-After": "7"})

    transport = _transport_for(handler)
    with pytest.raises(PyGLEIFRateLimitError) as excinfo:
        transport.get("lei-records")
    assert excinfo.value.status_code == 429
    assert excinfo.value.retry_after == 7.0


def test_transport_maps_500_to_api_error_with_body() -> None:
    """A 5xx should raise PyGLEIFApiError with a body excerpt."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="upstream exploded")

    transport = _transport_for(handler)
    with pytest.raises(PyGLEIFApiError) as excinfo:
        transport.get("fields")
    assert excinfo.value.status_code == 500
    assert excinfo.value.body == "upstream exploded"


def test_transport_wraps_network_errors() -> None:
    """Network-level failures should surface as PyGLEIFApiError."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    transport = _transport_for(handler)
    with pytest.raises(PyGLEIFApiError) as excinfo:
        transport.get("fields")
    assert excinfo.value.status_code is None
    assert excinfo.value.url is not None
    assert excinfo.value.url.endswith("fields")


def test_transport_async_maps_404_to_not_found() -> None:
    """The async path should map errors like the sync path."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    transport = _transport_for(handler)
    with pytest.raises(PyGLEIFNotFoundError) as excinfo:
        asyncio.run(transport.aget("lei-records/UNKNOWN"))
    assert excinfo.value.status_code == 404


# -- headers and configuration ---------------------------------------------


def test_transport_sends_user_agent_and_json_api_accept() -> None:
    """JSON requests should identify pygleif and ask for JSON:API."""
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"data": []})

    transport = _transport_for(handler)
    transport.get("fields")
    assert seen[0].headers["User-Agent"].startswith("pygleif")
    assert seen[0].headers["Accept"] == JSON_API_ACCEPT


def test_transport_get_raw_skips_json_api_accept() -> None:
    """File downloads must not force JSON:API content negotiation."""
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, content=b"lei,name\n")

    transport = _transport_for(handler)
    body = transport.get_raw("lei-records.csv", base_url=EXPORT_BASE_URL)
    assert body == b"lei,name\n"
    assert seen[0].headers["Accept"] != JSON_API_ACCEPT
    assert str(seen[0].url).startswith(EXPORT_BASE_URL)


def test_transport_timeout_is_configurable() -> None:
    """The constructor timeout should reach the httpx client."""
    transport = _transport_for(lambda request: httpx.Response(200), timeout=3)
    assert transport.client.timeout == httpx.Timeout(3)


# -- retries -----------------------------------------------------------------


def _flaky_handler(failures: int) -> Any:
    """Return a handler failing with 429 ``failures`` times, then 200."""
    attempts: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(1)
        if len(attempts) <= failures:
            return httpx.Response(429, headers={"Retry-After": "0"})
        return httpx.Response(200, json={"ok": True})

    handler.attempts = attempts  # type: ignore[attr-defined]
    return handler


def test_transport_retries_transient_statuses() -> None:
    """With retries configured, transient failures should be retried."""
    handler = _flaky_handler(failures=2)
    transport = _transport_for(handler, retries=2)
    assert transport.get("fields") == {"ok": True}
    assert len(handler.attempts) == 3


def test_transport_default_does_not_retry() -> None:
    """With the default retries=0, the first failure should raise."""
    handler = _flaky_handler(failures=1)
    transport = _transport_for(handler)
    with pytest.raises(PyGLEIFRateLimitError):
        transport.get("fields")
    assert len(handler.attempts) == 1


def test_transport_async_retries_transient_statuses() -> None:
    """The async path should retry like the sync path."""
    handler = _flaky_handler(failures=2)
    transport = _transport_for(handler, retries=2)
    assert asyncio.run(transport.aget("fields")) == {"ok": True}
    assert len(handler.attempts) == 3


def test_retry_delay_prefers_retry_after_and_caps() -> None:
    """The backoff should honor Retry-After, fall back, and stay capped."""
    with_header = httpx.Response(429, headers={"Retry-After": "7"})
    without_header = httpx.Response(429)
    invalid_header = httpx.Response(429, headers={"Retry-After": "later"})
    huge_header = httpx.Response(429, headers={"Retry-After": "9000"})
    assert _retry_delay(with_header, attempt=0) == 7.0
    assert _retry_delay(without_header, attempt=3) == 8.0
    assert _retry_delay(invalid_header, attempt=1) == 2.0
    assert _retry_delay(huge_header, attempt=0) == MAX_RETRY_DELAY_SECONDS

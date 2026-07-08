"""Tests for the httpx2-backed v2 Transport (offline via httpx2.MockTransport)."""

from __future__ import annotations

import asyncio
from email.utils import formatdate
import threading
import time
from typing import Any

import httpx2
import pytest

from pygleif.v2 import base as base_module
from pygleif.v2.base import (
    DEFAULT_REQUESTS_PER_MINUTE,
    DEFAULT_RETRIES,
    EXPORT_BASE_URL,
    JSON_API_ACCEPT,
    MAX_RETRY_DELAY_SECONDS,
    RATE_LIMIT_PERIOD_SECONDS,
    RateLimiter,
    Transport,
    _retry_after_seconds,
    _retry_delay,
)
from pygleif.v2.error import (
    PyGLEIFApiError,
    PyGLEIFNotFoundError,
    PyGLEIFRateLimitError,
    PyGLEIFResponseError,
)


def _transport_for(handler: Any, **kwargs: Any) -> Transport:
    """Build a Transport whose sync and async clients hit the handler."""
    mock = httpx2.MockTransport(handler)
    return Transport(httpx_transport=mock, httpx_async_transport=mock, **kwargs)


# -- error mapping ---------------------------------------------------------


def test_transport_maps_404_to_not_found() -> None:
    """A 404 should raise PyGLEIFNotFoundError with request context."""

    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(404, json={"errors": [{"title": "Not Found"}]})

    transport = _transport_for(handler)
    with pytest.raises(PyGLEIFNotFoundError) as excinfo:
        transport.get("lei-records/UNKNOWN")
    assert excinfo.value.status_code == 404
    assert excinfo.value.url is not None
    assert excinfo.value.url.endswith("lei-records/UNKNOWN")


def test_transport_maps_429_to_rate_limit_with_retry_after() -> None:
    """A 429 should raise PyGLEIFRateLimitError carrying Retry-After."""

    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(429, headers={"Retry-After": "7"})

    transport = _transport_for(handler, retries=0)
    with pytest.raises(PyGLEIFRateLimitError) as excinfo:
        transport.get("lei-records")
    assert excinfo.value.status_code == 429
    assert excinfo.value.retry_after == 7.0


def test_transport_maps_500_to_api_error_with_body() -> None:
    """A 5xx should raise PyGLEIFApiError with a body excerpt."""

    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(500, text="upstream exploded")

    transport = _transport_for(handler, retries=0)
    with pytest.raises(PyGLEIFApiError) as excinfo:
        transport.get("fields")
    assert excinfo.value.status_code == 500
    assert excinfo.value.body == "upstream exploded"


def test_transport_wraps_network_errors() -> None:
    """Network-level failures should surface as PyGLEIFApiError."""

    def handler(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError("boom")

    transport = _transport_for(handler, retries=0)
    with pytest.raises(PyGLEIFApiError) as excinfo:
        transport.get("fields")
    assert excinfo.value.status_code is None
    assert excinfo.value.url is not None
    assert excinfo.value.url.endswith("fields")


def test_transport_async_maps_404_to_not_found() -> None:
    """The async path should map errors like the sync path."""

    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(404)

    transport = _transport_for(handler, retries=0)
    with pytest.raises(PyGLEIFNotFoundError) as excinfo:
        asyncio.run(transport.aget("lei-records/UNKNOWN"))
    assert excinfo.value.status_code == 404


def test_transport_get_wraps_invalid_json() -> None:
    """A 200 response with a non-JSON body should raise PyGLEIFResponseError."""

    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, content=b"<html>not json</html>")

    transport = _transport_for(handler, retries=0)
    with pytest.raises(PyGLEIFResponseError) as excinfo:
        transport.get("fields")
    assert excinfo.value.body is not None
    assert "not json" in excinfo.value.body


def test_transport_aget_wraps_invalid_json() -> None:
    """Async counterpart of the JSON-decode wrapping test."""

    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, content=b"nope")

    transport = _transport_for(handler, retries=0)
    with pytest.raises(PyGLEIFResponseError):
        asyncio.run(transport.aget("fields"))


# -- headers and configuration ---------------------------------------------


def test_transport_sends_user_agent_and_json_api_accept() -> None:
    """JSON requests should identify pygleif and ask for JSON:API."""
    seen: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return httpx2.Response(200, json={"data": []})

    transport = _transport_for(handler)
    transport.get("fields")
    assert seen[0].headers["User-Agent"].startswith("pygleif")
    assert seen[0].headers["Accept"] == JSON_API_ACCEPT


def test_transport_get_raw_skips_json_api_accept() -> None:
    """File downloads must not force JSON:API content negotiation."""
    seen: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return httpx2.Response(200, content=b"lei,name\n")

    transport = _transport_for(handler)
    body = transport.get_raw("lei-records.csv", base_url=EXPORT_BASE_URL)
    assert body == b"lei,name\n"
    assert seen[0].headers["Accept"] != JSON_API_ACCEPT
    assert str(seen[0].url).startswith(EXPORT_BASE_URL)


def test_transport_timeout_is_configurable() -> None:
    """The constructor timeout should reach the httpx2 client."""
    transport = _transport_for(lambda request: httpx2.Response(200), timeout=3)
    assert transport.client.timeout == httpx2.Timeout(3)


def test_transport_client_creation_is_thread_safe() -> None:
    """Concurrent first access to ``.client`` must not create duplicates."""
    transport = _transport_for(lambda request: httpx2.Response(200))
    barrier = threading.Barrier(8)
    clients: list[httpx2.Client] = []
    lock = threading.Lock()

    def touch() -> None:
        barrier.wait()
        client = transport.client
        with lock:
            clients.append(client)

    threads = [threading.Thread(target=touch) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len({id(client) for client in clients}) == 1


# -- retries -----------------------------------------------------------------


def _flaky_handler(failures: int) -> Any:
    """Return a handler failing with 429 ``failures`` times, then 200."""
    attempts: list[int] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        attempts.append(1)
        if len(attempts) <= failures:
            return httpx2.Response(429, headers={"Retry-After": "0"})
        return httpx2.Response(200, json={"ok": True})

    handler.attempts = attempts  # type: ignore[attr-defined]
    return handler


def _flaky_network_handler(failures: int) -> Any:
    """Return a handler raising a connection error ``failures`` times, then 200."""
    attempts: list[int] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        attempts.append(1)
        if len(attempts) <= failures:
            raise httpx2.ConnectError("boom")
        return httpx2.Response(200, json={"ok": True})

    handler.attempts = attempts  # type: ignore[attr-defined]
    return handler


def test_transport_retries_transient_statuses() -> None:
    """With retries configured, transient failures should be retried."""
    handler = _flaky_handler(failures=2)
    transport = _transport_for(handler, retries=2)
    assert transport.get("fields") == {"ok": True}
    assert len(handler.attempts) == 3


def test_transport_default_retries_is_three() -> None:
    """The documented default should give three extra attempts."""
    assert Transport().retries == DEFAULT_RETRIES == 3


def test_transport_retries_by_default() -> None:
    """A Transport built with no explicit ``retries`` should still retry.

    GLEIF's 60 req/min limit makes 429 routine, so retrying must be on by
    default rather than something every caller has to opt into.
    """
    handler = _flaky_handler(failures=2)
    transport = _transport_for(handler)
    assert transport.get("fields") == {"ok": True}
    assert len(handler.attempts) == 3


def test_transport_zero_retries_does_not_retry() -> None:
    """With retries explicitly disabled, the first failure should raise."""
    handler = _flaky_handler(failures=1)
    transport = _transport_for(handler, retries=0)
    with pytest.raises(PyGLEIFRateLimitError):
        transport.get("fields")
    assert len(handler.attempts) == 1


def test_transport_async_retries_transient_statuses() -> None:
    """The async path should retry like the sync path."""
    handler = _flaky_handler(failures=2)
    transport = _transport_for(handler, retries=2)
    assert asyncio.run(transport.aget("fields")) == {"ok": True}
    assert len(handler.attempts) == 3


def test_transport_retries_network_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    """Transient network failures should be retried like transient statuses."""
    monkeypatch.setattr(base_module.time, "sleep", lambda _seconds: None)
    handler = _flaky_network_handler(failures=2)
    transport = _transport_for(handler, retries=2)
    assert transport.get("fields") == {"ok": True}
    assert len(handler.attempts) == 3


def test_transport_async_retries_network_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The async path should retry network errors like the sync path."""

    async def no_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr(base_module.asyncio, "sleep", no_sleep)
    handler = _flaky_network_handler(failures=2)
    transport = _transport_for(handler, retries=2)
    assert asyncio.run(transport.aget("fields")) == {"ok": True}
    assert len(handler.attempts) == 3


def test_transport_network_error_exhausts_retries() -> None:
    """Once retries are exhausted, the network error should still surface."""
    handler = _flaky_network_handler(failures=99)
    transport = _transport_for(handler, retries=1)
    with pytest.raises(PyGLEIFApiError):
        transport.get("fields")
    assert len(handler.attempts) == 2


def test_retry_after_seconds_parses_http_date() -> None:
    """An HTTP-date ``Retry-After`` (not just integer seconds) should parse."""
    future = formatdate(time.time() + 5, usegmt=True)
    response = httpx2.Response(429, headers={"Retry-After": future})
    delay = _retry_after_seconds(response)
    assert delay is not None
    assert 0.0 < delay <= 6.0


def test_retry_after_seconds_returns_none_without_response() -> None:
    """A network-level failure has no response to read Retry-After from."""
    assert _retry_after_seconds(None) is None


def test_retry_delay_prefers_retry_after_and_caps() -> None:
    """An explicit Retry-After should be honored exactly, and stay capped."""
    with_header = httpx2.Response(429, headers={"Retry-After": "7"})
    huge_header = httpx2.Response(429, headers={"Retry-After": "9000"})
    assert _retry_delay(with_header, attempt=0) == 7.0
    assert _retry_delay(huge_header, attempt=0) == MAX_RETRY_DELAY_SECONDS


def test_retry_delay_falls_back_to_jittered_backoff() -> None:
    """Without a usable Retry-After, backoff should be jittered and capped."""
    invalid_header = httpx2.Response(429, headers={"Retry-After": "later"})
    for attempt, upper_bound in ((1, 2.0), (3, 8.0), (10, MAX_RETRY_DELAY_SECONDS)):
        delay = _retry_delay(invalid_header, attempt=attempt)
        assert 0.0 <= delay <= upper_bound
    delay_no_response = _retry_delay(None, attempt=1)
    assert 0.0 <= delay_no_response <= 2.0


# -- rate limiting -----------------------------------------------------------


class _FakeClock:
    """Deterministic monotonic clock + sleep for rate-limiter tests.

    Rate limiting is a function of wall-clock progress, unlike the retry
    backoff tests above (which only need ``sleep`` to be a no-op): a
    no-op-only patch would leave the limiter's internal ``while`` loop
    spinning forever, since ``time.monotonic()`` would never advance. This
    fake advances its own clock whenever ``sleep``/``asleep`` is called, so
    waits resolve deterministically and instantly.
    """

    def __init__(self) -> None:
        self.now = 0.0

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds

    async def asleep(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def fake_clock(monkeypatch: pytest.MonkeyPatch) -> _FakeClock:
    """Patch ``base_module`` time so rate-limiter waits resolve instantly."""
    clock = _FakeClock()
    monkeypatch.setattr(base_module.time, "monotonic", clock.monotonic)
    monkeypatch.setattr(base_module.time, "sleep", clock.sleep)
    monkeypatch.setattr(base_module.asyncio, "sleep", clock.asleep)
    return clock


def test_rate_limiter_admits_up_to_max_calls_immediately(
    fake_clock: _FakeClock,
) -> None:
    """Calls within the quota should return without waiting."""
    limiter = RateLimiter(max_calls=3, period=60.0)
    assert limiter.wait() == 0.0
    assert limiter.wait() == 0.0
    assert limiter.wait() == 0.0
    assert fake_clock.now == 0.0


def test_rate_limiter_blocks_once_quota_is_exhausted(fake_clock: _FakeClock) -> None:
    """A call past the quota should wait for the oldest slot to age out."""
    limiter = RateLimiter(max_calls=2, period=60.0)
    limiter.wait()
    limiter.wait()
    waited = limiter.wait()
    assert waited == 60.0
    assert fake_clock.now == 60.0


def test_rate_limiter_await_turn_admits_up_to_max_calls_immediately(
    fake_clock: _FakeClock,
) -> None:
    """The async path should behave like the sync path within quota."""

    async def run() -> list[float]:
        limiter = RateLimiter(max_calls=3, period=60.0)
        return [await limiter.await_turn() for _ in range(3)]

    assert asyncio.run(run()) == [0.0, 0.0, 0.0]
    assert fake_clock.now == 0.0


def test_rate_limiter_await_turn_blocks_once_quota_is_exhausted(
    fake_clock: _FakeClock,
) -> None:
    """The async path should wait like the sync path once exhausted."""

    async def run() -> float:
        limiter = RateLimiter(max_calls=2, period=60.0)
        await limiter.await_turn()
        await limiter.await_turn()
        return await limiter.await_turn()

    assert asyncio.run(run()) == 60.0


def test_rate_limiter_admits_at_most_max_calls_concurrently() -> None:
    """Concurrent callers must never over-admit past ``max_calls``.

    Correctness here comes from the lock in ``RateLimiter._try_reserve``,
    which enforces the quota atomically; this drives it with real threads
    to confirm no race lets more than ``max_calls`` in without waiting.
    """
    limiter = RateLimiter(max_calls=4, period=0.2)
    barrier = threading.Barrier(8)
    results: list[float] = []
    lock = threading.Lock()

    def touch() -> None:
        barrier.wait()
        waited = limiter.wait()
        with lock:
            results.append(waited)

    threads = [threading.Thread(target=touch) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sum(1 for waited in results if waited == 0.0) == 4


def test_transport_default_requests_per_minute_matches_gleif_limit() -> None:
    """The documented default should pace to GLEIF's 60 req/min limit."""
    assert Transport().requests_per_minute == DEFAULT_REQUESTS_PER_MINUTE == 60


def test_transport_requests_per_minute_none_disables_pacing() -> None:
    """Passing ``requests_per_minute=None`` should skip the limiter entirely."""
    transport = _transport_for(
        lambda request: httpx2.Response(200),
        requests_per_minute=None,
    )
    assert transport._rate_limiter is None


def test_transport_paces_requests_past_the_quota(fake_clock: _FakeClock) -> None:
    """Once the quota is spent, further sync requests should be throttled."""
    seen: list[int] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(1)
        return httpx2.Response(200, json={"ok": True})

    transport = _transport_for(handler, requests_per_minute=2, retries=0)
    transport.get("fields")
    transport.get("fields")
    transport.get("fields")
    assert len(seen) == 3
    assert fake_clock.now == RATE_LIMIT_PERIOD_SECONDS


def test_transport_async_paces_requests_past_the_quota(
    fake_clock: _FakeClock,
) -> None:
    """The async path should throttle like the sync path once exhausted."""
    seen: list[int] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(1)
        return httpx2.Response(200, json={"ok": True})

    transport = _transport_for(handler, requests_per_minute=2, retries=0)

    async def run() -> None:
        await transport.aget("fields")
        await transport.aget("fields")
        await transport.aget("fields")

    asyncio.run(run())
    assert len(seen) == 3
    assert fake_clock.now == RATE_LIMIT_PERIOD_SECONDS


def test_transport_retries_also_draw_from_the_rate_limit_quota(
    fake_clock: _FakeClock,
) -> None:
    """A retried attempt is a real send too, so it must also be paced."""
    handler = _flaky_handler(failures=1)
    transport = _transport_for(handler, requests_per_minute=1, retries=1)
    assert transport.get("fields") == {"ok": True}
    assert len(handler.attempts) == 2
    # First send exhausts the quota; the retry attempt has to wait for it.
    assert fake_clock.now == RATE_LIMIT_PERIOD_SECONDS

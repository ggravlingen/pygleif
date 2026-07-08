"""HTTP transport layer for the v2 GLEIF client.

Wraps ``httpx2`` to build JSON API requests, apply filters and pagination,
and map transport failures to the v2 error hierarchy. Both synchronous
(``get``) and asynchronous (``aget``) request paths are supported, backed
by a lazily-created ``httpx2.Client`` / ``httpx2.AsyncClient`` pair.

Requests identify themselves with a ``pygleif/{version}`` user agent and
can opt into bounded retries (with ``Retry-After`` aware backoff) for
transient failures such as the GLEIF rate limit.
"""

from __future__ import annotations

import asyncio
from collections import deque
import datetime as dt
from email.utils import parsedate_to_datetime
from enum import IntEnum
from importlib import metadata
import logging
import random
import threading
import time
from typing import Any, Protocol, Self, runtime_checkable
from urllib import parse

import httpx2

from pygleif.v2.error import (
    PyGLEIFApiError,
    PyGLEIFNotFoundError,
    PyGLEIFRateLimitError,
    PyGLEIFResponseError,
)

logger = logging.getLogger("pygleif")

API_BASE_URL = "https://api.gleif.org/api/v1"
EXPORT_BASE_URL = "https://api.gleif.org/export/v1"
DEFAULT_TIMEOUT_SECONDS = 10.0
JSON_API_ACCEPT = "application/vnd.api+json"

#: Transient statuses worth retrying: the rate limit and server errors.
RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
MAX_RETRY_DELAY_SECONDS = 30.0
#: Extra attempts for transient failures by default; GLEIF's 60 req/min
#: limit makes 429 a routine event rather than an anomaly.
DEFAULT_RETRIES = 3

RATE_LIMIT_PERIOD_SECONDS = 60.0
#: Proactive pacing matching GLEIF's documented 60 req/min limit; pass
#: ``requests_per_minute=None`` to disable and rely solely on reactive
#: retries.
DEFAULT_REQUESTS_PER_MINUTE = 60


class HttpErrorCodes(IntEnum):
    """Relevant HTTP error codes returned by the GLEIF API."""

    NOT_FOUND = 404
    TOO_MANY_REQUESTS = 429


def _user_agent() -> str:
    """Return the ``pygleif/{version}`` user agent string."""
    try:
        return f"pygleif/{metadata.version('pygleif')}"
    except metadata.PackageNotFoundError:
        return "pygleif"


def _retry_after_seconds(response: httpx2.Response | None) -> float | None:
    """Parse the ``Retry-After`` header (seconds or HTTP-date form)."""
    if response is None:
        return None
    value = response.headers.get("Retry-After")
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        pass
    try:
        target = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    now = dt.datetime.now(target.tzinfo)
    return max((target - now).total_seconds(), 0.0)


def _retry_delay(response: httpx2.Response | None, attempt: int) -> float:
    """Return the capped backoff delay before the next attempt.

    Honors an explicit ``Retry-After`` exactly (the server knows best);
    otherwise falls back to exponential backoff with full jitter so
    concurrent clients retrying together don't all retry in lockstep.
    """
    delay = _retry_after_seconds(response)
    if delay is None:
        delay = random.uniform(0, float(2**attempt))  # noqa: S311 - jitter, not crypto
    return min(delay, MAX_RETRY_DELAY_SECONDS)


class RateLimiter:
    """Sliding-window limiter admitting at most `max_calls` per `period`.

    Backed by a deque of `time.monotonic()` timestamps guarded by a
    `threading.Lock`, shared by both the sync and async request paths
    (`wait` and `await_turn` respectively) so pacing draws from a single
    quota regardless of which path a caller uses. The lock is held only for
    the bookkeeping that decides whether to reserve a slot or sleep, never
    across the sleep itself, so concurrent callers don't serialize behind
    each other's wait.
    """

    def __init__(
        self,
        max_calls: int,
        period: float = RATE_LIMIT_PERIOD_SECONDS,
    ) -> None:
        """Admit at most `max_calls` calls per `period` seconds."""
        self._max_calls = max_calls
        self._period = period
        self._lock = threading.Lock()
        self._call_times: deque[float] = deque()

    def _try_reserve(self) -> float:
        """Reserve a slot if one is free; else return seconds until one is."""
        with self._lock:
            now = time.monotonic()
            cutoff = now - self._period
            while self._call_times and self._call_times[0] <= cutoff:
                self._call_times.popleft()
            if len(self._call_times) < self._max_calls:
                self._call_times.append(now)
                return 0.0
            return self._call_times[0] - cutoff

    def wait(self) -> float:
        """Block until a slot is free, reserve it, and return the wait time."""
        waited = 0.0
        while True:
            sleep_for = self._try_reserve()
            if sleep_for <= 0.0:
                return waited
            waited += sleep_for
            time.sleep(sleep_for)

    async def await_turn(self) -> float:
        """Async counterpart of :meth:`wait`."""
        waited = 0.0
        while True:
            sleep_for = self._try_reserve()
            if sleep_for <= 0.0:
                return waited
            waited += sleep_for
            await asyncio.sleep(sleep_for)


@runtime_checkable
class TransportLike(Protocol):
    """The duck type :class:`~pygleif.v2.client.GleifClient` requires.

    :class:`Transport` is the production implementation; tests inject
    lightweight fakes satisfying the same surface.
    """

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[Any, Any]:
        """Issue a GET request and return the decoded JSON body."""
        ...

    async def aget(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[Any, Any]:
        """Async counterpart of :meth:`get`."""
        ...

    def get_raw(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        base_url: str | None = None,
    ) -> bytes:
        """Issue a GET request and return the raw response body."""
        ...

    async def aget_raw(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        base_url: str | None = None,
    ) -> bytes:
        """Async counterpart of :meth:`get_raw`."""
        ...

    def close(self) -> None:
        """Close the sync connection pool, if one was created."""
        ...

    async def aclose(self) -> None:
        """Close the async connection pool, if one was created."""
        ...


class Transport:
    """Perform GET requests against the GLEIF JSON API, sync or async."""

    def __init__(  # noqa: PLR0913 - one arg per independent client setting
        self,
        base_url: str = API_BASE_URL,
        *,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        retries: int = DEFAULT_RETRIES,
        requests_per_minute: int | None = DEFAULT_REQUESTS_PER_MINUTE,
        httpx_transport: httpx2.BaseTransport | None = None,
        httpx_async_transport: httpx2.AsyncBaseTransport | None = None,
    ) -> None:
        """Init the transport.

        ``retries`` is the number of extra attempts for transient failures
        (:data:`RETRY_STATUSES` and network-level errors), honoring
        ``Retry-After`` with the delay capped at
        :data:`MAX_RETRY_DELAY_SECONDS`; pass ``0`` to disable retries.
        ``requests_per_minute`` proactively paces every attempt (including
        retries) to at most that many requests per rolling 60-second window,
        so well-behaved usage rarely draws a 429 in the first place; pass
        ``None`` to disable pacing and rely solely on reactive retries. The
        ``httpx_*transport`` hooks exist mainly so tests can inject an
        ``httpx2.MockTransport``.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retries = retries
        self.requests_per_minute = requests_per_minute
        self._rate_limiter = (
            RateLimiter(requests_per_minute) if requests_per_minute else None
        )
        self._httpx_transport = httpx_transport
        self._httpx_async_transport = httpx_async_transport
        self._client: httpx2.Client | None = None
        self._async_client: httpx2.AsyncClient | None = None
        self._client_lock = threading.Lock()
        self._async_client_lock = threading.Lock()

    @property
    def client(self) -> httpx2.Client:
        """Return the lazily-created sync ``httpx2.Client``.

        Double-checked locking: the outer check lets the common case (a
        client already exists) skip the lock entirely. The inner check
        re-verifies after acquiring it, because another thread may have
        built the client while this one was waiting on the lock — without
        it, two threads could each construct a client and one would leak
        its connection pool.
        """
        if self._client is None:
            with self._client_lock:
                if self._client is None:
                    kwargs: dict[str, Any] = {}
                    if self._httpx_transport is not None:
                        kwargs["transport"] = self._httpx_transport
                    self._client = httpx2.Client(
                        timeout=self.timeout,
                        headers={"User-Agent": _user_agent()},
                        **kwargs,
                    )
        return self._client

    @property
    def async_client(self) -> httpx2.AsyncClient:
        """Return the lazily-created ``httpx2.AsyncClient``.

        Same double-checked locking as :attr:`client`: skip the lock when
        a client already exists, and re-check after acquiring it in case
        another thread (e.g. a different worker running its own event
        loop) built one first while this one was waiting.
        """
        if self._async_client is None:
            with self._async_client_lock:
                if self._async_client is None:
                    kwargs: dict[str, Any] = {}
                    if self._httpx_async_transport is not None:
                        kwargs["transport"] = self._httpx_async_transport
                    self._async_client = httpx2.AsyncClient(
                        timeout=self.timeout,
                        headers={"User-Agent": _user_agent()},
                        **kwargs,
                    )
        return self._async_client

    def _build_url(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        base_url: str | None = None,
    ) -> str:
        """Compose a full request URL with an encoded query string.

        JSON API bracketed keys (e.g. ``filter[lei]`` or ``page[size]``)
        are preserved without percent-encoding the brackets, matching the
        format the GLEIF API expects. ``base_url`` overrides the transport
        default (used by the ``/export/v1`` endpoints).
        """
        base = (base_url or self.base_url).rstrip("/")
        url = f"{base}/{path.lstrip('/')}"
        if not params:
            return url
        # ``safe`` keeps JSON:API bracket syntax intact.
        query = parse.urlencode(
            {k: v for k, v in params.items() if v is not None},
            safe="[]",
        )
        return f"{url}?{query}" if query else url

    @staticmethod
    def _map_status_error(exc: httpx2.HTTPStatusError) -> PyGLEIFApiError:
        """Map an ``httpx2`` status error to the v2 error hierarchy."""
        response = exc.response
        code = response.status_code
        url = str(exc.request.url)
        body = response.text[:200]
        if code == HttpErrorCodes.NOT_FOUND:
            return PyGLEIFNotFoundError(
                f"Resource not found: {url}",
                status_code=code,
                url=url,
                body=body,
            )
        if code == HttpErrorCodes.TOO_MANY_REQUESTS:
            return PyGLEIFRateLimitError(
                f"GLEIF rate limit exceeded (60 requests/minute): {url}",
                retry_after=_retry_after_seconds(response),
                status_code=code,
                url=url,
                body=body,
            )
        return PyGLEIFApiError(
            f"HTTP {code} error for {url}",
            status_code=code,
            url=url,
            body=body,
        )

    def _paced_get(
        self,
        url: str,
        headers: dict[str, str] | None,
    ) -> httpx2.Response:
        """GET, first pacing to ``self._rate_limiter``'s quota if set."""
        if self._rate_limiter is not None:
            waited = self._rate_limiter.wait()
            if waited > 0:
                logger.warning(
                    "pygleif: throttled %s for %.2fs to respect rate limit",
                    url,
                    waited,
                )
        return self.client.get(url, headers=headers)

    async def _apaced_get(
        self,
        url: str,
        headers: dict[str, str] | None,
    ) -> httpx2.Response:
        """Async counterpart of :meth:`_paced_get`."""
        if self._rate_limiter is not None:
            waited = await self._rate_limiter.await_turn()
            if waited > 0:
                logger.warning(
                    "pygleif: throttled %s for %.2fs to respect rate limit",
                    url,
                    waited,
                )
        return await self.async_client.get(url, headers=headers)

    def _send_with_retry(
        self,
        url: str,
        headers: dict[str, str] | None,
    ) -> httpx2.Response:
        """GET with up to ``self.retries`` extra attempts on transient errors.

        Retries both transient HTTP statuses (:data:`RETRY_STATUSES`) and
        network-level failures (``httpx2.TransportError``, e.g. connection
        resets or timeouts) so a momentary blip doesn't fail the request.
        Every attempt, including retries, is paced through
        :meth:`_paced_get` so retries draw from the same rate-limit quota.
        """
        for attempt in range(self.retries):
            try:
                response = self._paced_get(url, headers)
            except httpx2.TransportError as exc:
                delay = _retry_delay(None, attempt)
                logger.warning(
                    "pygleif: network error on attempt %d/%d for %s (%s); "
                    "retrying in %.1fs",
                    attempt + 1,
                    self.retries + 1,
                    url,
                    exc,
                    delay,
                )
                time.sleep(delay)
                continue
            if response.status_code not in RETRY_STATUSES:
                return response
            delay = _retry_delay(response, attempt)
            logger.warning(
                "pygleif: got HTTP %d on attempt %d/%d for %s; retrying in %.1fs",
                response.status_code,
                attempt + 1,
                self.retries + 1,
                url,
                delay,
            )
            time.sleep(delay)
        return self._paced_get(url, headers)

    async def _asend_with_retry(
        self,
        url: str,
        headers: dict[str, str] | None,
    ) -> httpx2.Response:
        """Async counterpart of :meth:`_send_with_retry`."""
        for attempt in range(self.retries):
            try:
                response = await self._apaced_get(url, headers)
            except httpx2.TransportError as exc:
                delay = _retry_delay(None, attempt)
                logger.warning(
                    "pygleif: network error on attempt %d/%d for %s (%s); "
                    "retrying in %.1fs",
                    attempt + 1,
                    self.retries + 1,
                    url,
                    exc,
                    delay,
                )
                await asyncio.sleep(delay)
                continue
            if response.status_code not in RETRY_STATUSES:
                return response
            delay = _retry_delay(response, attempt)
            logger.warning(
                "pygleif: got HTTP %d on attempt %d/%d for %s; retrying in %.1fs",
                response.status_code,
                attempt + 1,
                self.retries + 1,
                url,
                delay,
            )
            await asyncio.sleep(delay)
        return await self._apaced_get(url, headers)

    def _request(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        base_url: str | None = None,
        accept: str | None = None,
    ) -> httpx2.Response:
        """Issue a GET request, mapping failures to the v2 errors."""
        url = self._build_url(path, params, base_url=base_url)
        headers = {"Accept": accept} if accept else None
        logger.debug("pygleif: GET %s", url)
        try:
            response = self._send_with_retry(url, headers)
            response.raise_for_status()
        except httpx2.HTTPStatusError as exc:
            raise self._map_status_error(exc) from exc
        except httpx2.HTTPError as exc:
            msg = f"An unexpected error occurred: {exc!s}"
            raise PyGLEIFApiError(msg, url=url) from exc
        logger.debug("pygleif: %s -> %d", url, response.status_code)
        return response

    async def _arequest(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        base_url: str | None = None,
        accept: str | None = None,
    ) -> httpx2.Response:
        """Async counterpart of :meth:`_request`."""
        url = self._build_url(path, params, base_url=base_url)
        headers = {"Accept": accept} if accept else None
        logger.debug("pygleif: GET %s", url)
        try:
            response = await self._asend_with_retry(url, headers)
            response.raise_for_status()
        except httpx2.HTTPStatusError as exc:
            raise self._map_status_error(exc) from exc
        except httpx2.HTTPError as exc:
            msg = f"An unexpected error occurred: {exc!s}"
            raise PyGLEIFApiError(msg, url=url) from exc
        logger.debug("pygleif: %s -> %d", url, response.status_code)
        return response

    @staticmethod
    def _decode_json(response: httpx2.Response) -> dict[Any, Any]:
        """Decode a response body as JSON, mapping decode failures."""
        try:
            return response.json()
        except ValueError as exc:
            url = str(response.request.url)
            msg = f"Response body is not valid JSON: {url}"
            raise PyGLEIFResponseError(
                msg,
                url=url,
                body=response.text[:200],
            ) from exc

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[Any, Any]:
        """Issue a GET request and return the decoded JSON body."""
        return self._decode_json(self._request(path, params, accept=JSON_API_ACCEPT))

    async def aget(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[Any, Any]:
        """Issue an async GET request and return the decoded JSON body."""
        response = await self._arequest(path, params, accept=JSON_API_ACCEPT)
        return self._decode_json(response)

    def get_raw(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        base_url: str | None = None,
    ) -> bytes:
        """Issue a GET request and return the raw response body.

        Used for non-JSON endpoints such as the ``/export/v1`` file
        downloads; ``base_url`` overrides the transport default. No
        JSON:API ``Accept`` header is sent, so the server's content
        negotiation stays untouched for file formats.
        """
        return self._request(path, params, base_url=base_url).content

    async def aget_raw(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        base_url: str | None = None,
    ) -> bytes:
        """Issue an async GET request and return the raw response body.

        Async counterpart of :meth:`get_raw`.
        """
        response = await self._arequest(path, params, base_url=base_url)
        return response.content

    def close(self) -> None:
        """Close the underlying sync client, if one was created."""
        if self._client is not None:
            self._client.close()
            self._client = None

    async def aclose(self) -> None:
        """Close the underlying async client, if one was created."""
        if self._async_client is not None:
            await self._async_client.aclose()
            self._async_client = None

    def __enter__(self) -> Self:
        """Enter the sync context manager."""
        return self

    def __exit__(self, *exc_info: object) -> None:
        """Close the sync client on context exit."""
        self.close()

    async def __aenter__(self) -> Self:
        """Enter the async context manager."""
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        """Close the async client on context exit."""
        await self.aclose()

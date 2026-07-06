"""HTTP transport layer for the v2 GLEIF client.

Wraps ``httpx`` to build JSON API requests, apply filters and pagination,
and map transport failures to the v2 error hierarchy. Both synchronous
(``get``) and asynchronous (``aget``) request paths are supported, backed
by a lazily-created ``httpx.Client`` / ``httpx.AsyncClient`` pair.

Requests identify themselves with a ``pygleif/{version}`` user agent and
can opt into bounded retries (with ``Retry-After`` aware backoff) for
transient failures such as the GLEIF rate limit.
"""

from __future__ import annotations

import asyncio
from enum import IntEnum
from importlib import metadata
import time
from typing import Any, Protocol, Self, runtime_checkable
from urllib import parse

import httpx

from pygleif.v2.error import (
    PyGLEIFApiError,
    PyGLEIFNotFoundError,
    PyGLEIFRateLimitError,
)

API_BASE_URL = "https://api.gleif.org/api/v1"
EXPORT_BASE_URL = "https://api.gleif.org/export/v1"
DEFAULT_TIMEOUT_SECONDS = 10.0
JSON_API_ACCEPT = "application/vnd.api+json"

#: Transient statuses worth retrying: the rate limit and server errors.
RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
MAX_RETRY_DELAY_SECONDS = 30.0


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


def _retry_after_seconds(response: httpx.Response) -> float | None:
    """Parse the ``Retry-After`` header (integer-seconds form only)."""
    value = response.headers.get("Retry-After")
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _retry_delay(response: httpx.Response, attempt: int) -> float:
    """Return the capped backoff delay before the next attempt."""
    delay = _retry_after_seconds(response)
    if delay is None:
        delay = float(2**attempt)
    return min(delay, MAX_RETRY_DELAY_SECONDS)


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

    def __init__(
        self,
        base_url: str = API_BASE_URL,
        *,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        retries: int = 0,
        httpx_transport: httpx.BaseTransport | None = None,
        httpx_async_transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        """Init the transport.

        ``retries`` is the number of extra attempts for transient failures
        (:data:`RETRY_STATUSES`), honoring ``Retry-After`` with the delay
        capped at :data:`MAX_RETRY_DELAY_SECONDS`; the default of ``0``
        never sleeps. The ``httpx_*transport`` hooks exist mainly so tests
        can inject an ``httpx.MockTransport``.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retries = retries
        self._httpx_transport = httpx_transport
        self._httpx_async_transport = httpx_async_transport
        self._client: httpx.Client | None = None
        self._async_client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.Client:
        """Return the lazily-created sync ``httpx.Client``."""
        if self._client is None:
            kwargs: dict[str, Any] = {}
            if self._httpx_transport is not None:
                kwargs["transport"] = self._httpx_transport
            self._client = httpx.Client(
                timeout=self.timeout,
                headers={"User-Agent": _user_agent()},
                **kwargs,
            )
        return self._client

    @property
    def async_client(self) -> httpx.AsyncClient:
        """Return the lazily-created ``httpx.AsyncClient``."""
        if self._async_client is None:
            kwargs: dict[str, Any] = {}
            if self._httpx_async_transport is not None:
                kwargs["transport"] = self._httpx_async_transport
            self._async_client = httpx.AsyncClient(
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
    def _map_status_error(exc: httpx.HTTPStatusError) -> PyGLEIFApiError:
        """Map an ``httpx`` status error to the v2 error hierarchy."""
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

    def _send_with_retry(
        self,
        url: str,
        headers: dict[str, str] | None,
    ) -> httpx.Response:
        """GET with up to ``self.retries`` extra attempts on transient errors."""
        for attempt in range(self.retries):
            response = self.client.get(url, headers=headers)
            if response.status_code not in RETRY_STATUSES:
                return response
            time.sleep(_retry_delay(response, attempt))
        return self.client.get(url, headers=headers)

    async def _asend_with_retry(
        self,
        url: str,
        headers: dict[str, str] | None,
    ) -> httpx.Response:
        """Async counterpart of :meth:`_send_with_retry`."""
        for attempt in range(self.retries):
            response = await self.async_client.get(url, headers=headers)
            if response.status_code not in RETRY_STATUSES:
                return response
            await asyncio.sleep(_retry_delay(response, attempt))
        return await self.async_client.get(url, headers=headers)

    def _request(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        base_url: str | None = None,
        accept: str | None = None,
    ) -> httpx.Response:
        """Issue a GET request, mapping failures to the v2 errors."""
        url = self._build_url(path, params, base_url=base_url)
        headers = {"Accept": accept} if accept else None
        try:
            response = self._send_with_retry(url, headers)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise self._map_status_error(exc) from exc
        except httpx.HTTPError as exc:
            msg = f"An unexpected error occurred: {exc!s}"
            raise PyGLEIFApiError(msg, url=url) from exc
        return response

    async def _arequest(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        base_url: str | None = None,
        accept: str | None = None,
    ) -> httpx.Response:
        """Async counterpart of :meth:`_request`."""
        url = self._build_url(path, params, base_url=base_url)
        headers = {"Accept": accept} if accept else None
        try:
            response = await self._asend_with_retry(url, headers)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise self._map_status_error(exc) from exc
        except httpx.HTTPError as exc:
            msg = f"An unexpected error occurred: {exc!s}"
            raise PyGLEIFApiError(msg, url=url) from exc
        return response

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[Any, Any]:
        """Issue a GET request and return the decoded JSON body."""
        return self._request(path, params, accept=JSON_API_ACCEPT).json()

    async def aget(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[Any, Any]:
        """Issue an async GET request and return the decoded JSON body."""
        response = await self._arequest(path, params, accept=JSON_API_ACCEPT)
        return response.json()

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

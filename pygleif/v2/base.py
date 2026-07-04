"""HTTP transport layer for the v2 GLEIF client.

Wraps ``httpx`` to build JSON API requests, apply filters and pagination,
and map transport failures to the v2 error hierarchy. Both synchronous
(``get``) and asynchronous (``aget``) request paths are supported, backed
by a lazily-created ``httpx.Client`` / ``httpx.AsyncClient`` pair.
"""

from __future__ import annotations

from enum import IntEnum
from typing import Any, Self
from urllib import parse

import httpx

from pygleif.v2.error import (
    PyGLEIFApiError,
    PyGLEIFNotFoundError,
    PyGLEIFRateLimitError,
)

API_BASE_URL = "https://api.gleif.org/api/v1"
EXPORT_BASE_URL = "https://api.gleif.org/export/v1"


class HttpErrorCodes(IntEnum):
    """Relevant HTTP error codes returned by the GLEIF API."""

    NOT_FOUND = 404
    TOO_MANY_REQUESTS = 429


class Transport:
    """Perform GET requests against the GLEIF JSON API, sync or async."""

    TIMEOUT_SECOND = 10

    def __init__(self, base_url: str = API_BASE_URL) -> None:
        """Init the transport with a configurable base URL."""
        self.base_url = base_url.rstrip("/")
        self._client: httpx.Client | None = None
        self._async_client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.Client:
        """Return the lazily-created sync ``httpx.Client``."""
        if self._client is None:
            self._client = httpx.Client(timeout=self.TIMEOUT_SECOND)
        return self._client

    @property
    def async_client(self) -> httpx.AsyncClient:
        """Return the lazily-created ``httpx.AsyncClient``."""
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(timeout=self.TIMEOUT_SECOND)
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
        code = exc.response.status_code
        if code == HttpErrorCodes.NOT_FOUND:
            return PyGLEIFNotFoundError("Resource not found")
        if code == HttpErrorCodes.TOO_MANY_REQUESTS:
            return PyGLEIFRateLimitError(
                "GLEIF rate limit exceeded (60 requests/minute)",
            )
        return PyGLEIFApiError(f"HTTP Error encountered: {code}")

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[Any, Any]:
        """Issue a GET request and return the decoded JSON body."""
        url = self._build_url(path, params)
        try:
            response = self.client.get(url)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise self._map_status_error(exc) from exc
        except httpx.HTTPError as exc:
            msg = f"An unexpected error occurred: {exc!s}"
            raise PyGLEIFApiError(msg) from exc
        return response.json()

    async def aget(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[Any, Any]:
        """Issue an async GET request and return the decoded JSON body."""
        url = self._build_url(path, params)
        try:
            response = await self.async_client.get(url)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise self._map_status_error(exc) from exc
        except httpx.HTTPError as exc:
            msg = f"An unexpected error occurred: {exc!s}"
            raise PyGLEIFApiError(msg) from exc
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
        downloads; ``base_url`` overrides the transport default.
        """
        url = self._build_url(path, params, base_url=base_url)
        try:
            response = self.client.get(url)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise self._map_status_error(exc) from exc
        except httpx.HTTPError as exc:
            msg = f"An unexpected error occurred: {exc!s}"
            raise PyGLEIFApiError(msg) from exc
        return response.content

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
        url = self._build_url(path, params, base_url=base_url)
        try:
            response = await self.async_client.get(url)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise self._map_status_error(exc) from exc
        except httpx.HTTPError as exc:
            msg = f"An unexpected error occurred: {exc!s}"
            raise PyGLEIFApiError(msg) from exc
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

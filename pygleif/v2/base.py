"""HTTP transport layer for the v2 GLEIF client.

Thin wrapper around the standard library ``urllib`` that builds JSON API
requests, applies filters and pagination, and maps transport failures to
the v2 error hierarchy. No third-party HTTP dependency is required.
"""

from __future__ import annotations

from enum import IntEnum
import json
from typing import Any
from urllib import error, parse, request

from pygleif.v2.error import (
    PyGLEIFApiError,
    PyGLEIFNotFoundError,
    PyGLEIFRateLimitError,
)

API_BASE_URL = "https://api.gleif.org/api/v1"


class HttpErrorCodes(IntEnum):
    """Relevant HTTP error codes returned by the GLEIF API."""

    NOT_FOUND = 404
    TOO_MANY_REQUESTS = 429


class Transport:
    """Perform GET requests against the GLEIF JSON API."""

    TIMEOUT_SECOND = 10

    def __init__(self, base_url: str = API_BASE_URL) -> None:
        """Init the transport with a configurable base URL."""
        self.base_url = base_url.rstrip("/")

    def _build_url(self, path: str, params: dict[str, Any] | None = None) -> str:
        """Compose a full request URL with an encoded query string.

        JSON API bracketed keys (e.g. ``filter[lei]`` or ``page[size]``)
        are preserved without percent-encoding the brackets, matching the
        format the GLEIF API expects.
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        if not params:
            return url
        # ``safe`` keeps JSON:API bracket syntax intact.
        query = parse.urlencode(
            {k: v for k, v in params.items() if v is not None},
            safe="[]",
        )
        return f"{url}?{query}" if query else url

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[Any, Any]:
        """Issue a GET request and return the decoded JSON body."""
        url = self._build_url(path, params)
        try:
            with request.urlopen(url, timeout=self.TIMEOUT_SECOND) as response:  # noqa: S310 - fixed https base URL
                return json.loads(response.read())
        except error.HTTPError as exc:
            if exc.code == HttpErrorCodes.NOT_FOUND:
                msg = "Resource not found"
                raise PyGLEIFNotFoundError(msg) from exc
            if exc.code == HttpErrorCodes.TOO_MANY_REQUESTS:
                msg = "GLEIF rate limit exceeded (60 requests/minute)"
                raise PyGLEIFRateLimitError(msg) from exc
            msg = f"HTTP Error encountered: {exc.code}"
            raise PyGLEIFApiError(msg) from exc
        except error.URLError as exc:
            msg = f"URL Error encountered: {exc.reason}"
            raise PyGLEIFApiError(msg) from exc
        except Exception as exc:
            msg = f"An unexpected error occurred: {exc!s}"
            raise PyGLEIFApiError(msg) from exc

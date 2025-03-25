"""A base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import IntEnum
import json
from typing import TYPE_CHECKING, Any, cast
from urllib import error, request

from pygleif.error import PyGLEIFApiError

if TYPE_CHECKING:
    from .api import GLEIFResponse, SearchResponse


class HttpErrorCodes(IntEnum):
    """Represent HTTP error codes."""

    NOT_FOUND = 404


class PyGleifBase(ABC):
    """Base class for a GLEIF API request."""

    TIMEOUT_SECOND = 10  # 10 seconds

    search_string: str

    @property
    def json_response(self) -> dict[Any, Any]:
        """Return JSON response."""
        try:
            with request.urlopen(
                f"https://api.gleif.org/api/v1/lei-records/{self.search_string}",
                timeout=self.TIMEOUT_SECOND,
            ) as response:
                return cast("dict[Any, Any]", json.loads(response.read()))
        except error.HTTPError as e:
            if e.code == HttpErrorCodes.NOT_FOUND:
                msg = "Resource not found"
                raise PyGLEIFApiError(msg) from e

            msg = f"HTTP Error encountered: {e.code}"
            raise PyGLEIFApiError(msg) from e
        except error.URLError as e:
            msg = f"URL Error encountered: {e.reason}"
            raise PyGLEIFApiError(msg) from e
        except Exception as e:
            msg = f"An unexpected error occurred: {e!s}"
            raise PyGLEIFApiError(msg) from e

    @property
    @abstractmethod
    def response(self) -> GLEIFResponse | SearchResponse | None:
        """Return response."""

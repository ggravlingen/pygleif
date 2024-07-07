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

    BASE_URL = "https://api.gleif.org/api/v1/lei-records/"
    TIMEOUT_SECOND = 10  # 10 seconds

    search_string: str

    @property
    def json_response(self) -> dict[Any, Any]:
        """Return JSON response."""
        full_url = f"{self.BASE_URL}{self.search_string}"
        try:
            with request.urlopen(
                full_url,
                timeout=self.TIMEOUT_SECOND,
            ) as fdesc:
                return cast(dict[Any, Any], json.loads(fdesc.read()))
        except error.HTTPError as e:
            if e.code == HttpErrorCodes.NOT_FOUND:
                raise PyGLEIFApiError(f"Resource {full_url} not found")
            else:
                raise PyGLEIFApiError(f"HTTP Error encountered: {e.code}")
        except error.URLError as e:
            raise PyGLEIFApiError(f"URL Error encountered: {e.reason}")
        except Exception as e:
            raise PyGLEIFApiError(f"An unexpected error occurred: {e!s}")

    @property
    @abstractmethod
    def response(self) -> GLEIFResponse | SearchResponse | None:
        """Return response."""

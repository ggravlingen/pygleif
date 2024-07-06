"""GLEIF API."""

from typing import Any

from .api import GLEIFResponse
from .const import URL_API
from .utils import load_json


class PyGleif:
    """Query GLEIF API and return response."""

    def __init__(self, lei_code: str) -> None:
        """Init class."""
        self.lei_code = lei_code

    @property
    def json_response(self) -> list[Any] | dict[Any, Any]:
        """Return JSON response."""
        return load_json(search_url=URL_API, search_string=self.lei_code)

    @property
    def response(self) -> GLEIFResponse:
        """Return response."""
        return GLEIFResponse(**self.json_response)

"""GLEIF API."""

from .api import GLEIFResponse
from .base import PyGleifBase


class PyGleif(PyGleifBase):
    """Query GLEIF API and return response."""

    def __init__(self, lei_code: str) -> None:
        """Init class."""
        self.search_string = lei_code

    @property
    def response(self) -> GLEIFResponse:
        """Return response."""
        return GLEIFResponse(**self.json_response)

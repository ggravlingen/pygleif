"""GLEIF API."""
from .api import GLEIFResponse
from .const import URL_API
from .utils import load_json


class PyGleif:
    """Query GLEIF API and return response."""

    def __init__(self, lei_code: str) -> None:
        """Init class."""
        json_data = load_json(search_url=URL_API, search_string=lei_code)
        self.response = GLEIFResponse(**json_data)

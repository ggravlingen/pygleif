"""GLEIF API."""
from .api import GLEIFResponse
from .utils import load_json


class PyGleif:
    """Query GLEIF API and return response."""

    def __init__(self, lei_code: str) -> None:
        """Init class."""
        json_data = load_json(lei_code)
        self.response = GLEIFResponse(**json_data)

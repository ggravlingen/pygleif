"""Search."""


from pygleif.api import SearchResponse
from pygleif.const import URL_SEARCH

from .utils import load_json


class Search:
    """Class to use the search form of the GLEIF web site."""

    def __init__(self, orgnr: str) -> None:
        """Init class."""
        json_data = load_json(search_url=URL_SEARCH, search_string=orgnr)
        self.response = SearchResponse(**json_data)

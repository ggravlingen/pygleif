"""Search."""
from __future__ import annotations

from typing import Optional

from pygleif.api import SearchResponse
from pygleif.const import URL_SEARCH

from .utils import load_json


class Search:
    """Class to use the search form of the GLEIF web site."""

    response = Optional[SearchResponse]

    def __init__(self, orgnr: str) -> None:
        """Init class."""
        json_data = load_json(search_url=URL_SEARCH, search_string=orgnr)

        if json_data["data"]:
            self.response = SearchResponse(**json_data)
        else:
            self.response = None

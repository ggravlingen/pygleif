"""Search."""

from __future__ import annotations

from enum import Enum
from urllib import parse

from pygleif.api import SearchResponse

from .base import PyGleifBase


class SearchType(str, Enum):
    """Enum for search types."""

    FULL_TEXT = "fulltext"


class Search(PyGleifBase):
    """Class to use the search form of the GLEIF web site."""

    def __init__(
        self,
        search_string: str,
        search_type: SearchType = SearchType.FULL_TEXT,
    ) -> None:
        """Init class."""
        encoded_search_string = parse.quote(search_string, safe="")
        self.search_string = (
            f"?filter[{search_type.value.lower()}]={encoded_search_string}"
        )

    @property
    def response(self) -> SearchResponse | None:
        """Return response."""
        return SearchResponse(**self.json_response)

"""Search."""

from __future__ import annotations

from urllib import parse

from pygleif.api import SearchResponse

from .base import PyGleifBase


class Search(PyGleifBase):
    """Class to use the search form of the GLEIF web site."""

    def __init__(self, orgnr: str) -> None:
        """Init class."""
        encoded_org_nr = parse.quote(orgnr, safe="")
        self.search_string = f"?filter[fulltext]={encoded_org_nr}"

    @property
    def response(self) -> SearchResponse | None:
        """Return response."""
        return SearchResponse(**self.json_response)

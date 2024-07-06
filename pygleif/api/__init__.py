"""Pydantic Representation of models."""

from pydantic import BaseModel

from .data import Data
from .meta import Meta


class GLEIFResponse(BaseModel):
    """Represent a base response."""

    meta: Meta
    data: Data


class SearchResponse(BaseModel):
    """Represent search result response."""

    meta: Meta
    data: list[Data]

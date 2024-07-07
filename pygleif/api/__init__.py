"""Pydantic Representation of models."""

from .data import Data
from .meta import Meta
from .shared import BaseSchema


class GLEIFResponse(BaseSchema):
    """Represent a base response."""

    meta: Meta
    data: Data


class SearchResponse(BaseSchema):
    """Represent search result response."""

    meta: Meta
    data: list[Data]

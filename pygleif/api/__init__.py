"""Pydantic Representation of models."""

from pydantic.v1 import BaseModel, Field

from .data import Data
from .meta import Meta


class GLEIFResponse(BaseModel):
    """Represent a base response."""

    meta: Meta = Field(alias="meta")
    data: Data = Field(alias="data")


class SearchResponse(BaseModel):
    """Represent search result response."""

    meta: Meta = Field(alias="meta")
    data: list[Data] = Field(alias="data")

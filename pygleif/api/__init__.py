"""Pydantic Representation of models."""
from pydantic import BaseModel, Field

from .data import Data
from .meta import Meta


class GLEIFResponse(BaseModel):
    """Represent a base response."""

    meta: Meta = Field(alias="meta")
    data: Data = Field(alias="data")

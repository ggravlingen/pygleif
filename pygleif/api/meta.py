"""Meta data."""
from datetime import datetime

from pydantic import BaseModel, Field


class GoldenCopy(BaseModel):
    """Represent golden copy information."""

    publish_date: datetime = Field(alias="publishDate")


class Meta(BaseModel):
    """Represent meta information."""

    golden_copy: GoldenCopy = Field(alias="goldenCopy")

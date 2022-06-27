"""Meta data."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class GoldenCopy(BaseModel):
    """Represent golden copy information."""

    publish_date: datetime = Field(alias="publishDate")


class Pagination(BaseModel):
    """Represent response pagination."""

    current_page: int = Field(alias="currentPage")
    per_page: int = Field(alias="perPage")
    _from: int = Field(alias="from")
    to: int = Field(alias="to")
    total: int = Field(alias="total")
    last_page: int = Field(alias="lastPage")


class Meta(BaseModel):
    """Represent meta information."""

    golden_copy: GoldenCopy = Field(alias="goldenCopy")
    # Pagination is part of the search response
    pagination: Optional[Pagination] = Field(alias="pagination")

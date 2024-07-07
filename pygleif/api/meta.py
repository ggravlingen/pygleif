"""Meta data."""

from datetime import datetime

from .shared import BaseSchema


class GoldenCopy(BaseSchema):
    """Represent golden copy information."""

    publish_date: datetime


class Pagination(BaseSchema):
    """Represent response pagination."""

    current_page: int
    per_page: int
    _from: int
    to: int | None = None
    total: int
    last_page: int


class Meta(BaseSchema):
    """Represent meta information."""

    golden_copy: GoldenCopy
    pagination: Pagination | None = None

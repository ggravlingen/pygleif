"""Shared classes."""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class BaseSchema(BaseModel):
    """Define base schema."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

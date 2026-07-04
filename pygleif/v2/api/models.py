"""Pydantic v2-bound models for the full GLEIF API v1.0 surface.

Covers the resources exposed by https://api.gleif.org/api/v1:

- ``lei-records``      -> :class:`GLEIFResponse`, :class:`SearchResponse`
- ``lei-records/{lei}/isins`` -> :class:`IsinResponse`
- ``fuzzycompletions`` -> :class:`FuzzyCompletionResponse`
- ``fields``           -> :class:`FieldsResponse`

The JSON API responses use camelCase keys; models accept both camelCase
(via the alias generator) and snake_case (``populate_by_name``).
"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - needed at runtime by pydantic
from typing import Any

from pygleif.v2.pydantic_shim import BaseModel, ConfigDict, Field, to_camel

DESCRIPTION_VALUES: dict[str, str] = {
    "lei": (
        "The LEI code is a 20-character, alpha-numeric code that defines the ISO "
        "17442 compatible identifier for the legal entity."
    ),
}


class BaseSchema(BaseModel):
    """Base schema with camelCase aliasing for GLEIF JSON API payloads."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


# ---------------------------------------------------------------------------
# LEI record (Level 1) models
# ---------------------------------------------------------------------------
class ValidatedAt(BaseSchema):
    """Represent validated-at information."""

    id: str
    other: str | None


class Registration(BaseSchema):
    """Represent registration information."""

    corroboration_level: str
    initial_registration_date: datetime
    last_update_date: datetime
    managing_lou: str
    next_renewal_date: datetime
    other_validation_authorities: list[Any]
    status: str
    validated_as: str | None = None
    validated_at: ValidatedAt


class GeneralEntity(BaseSchema):
    """Represent a general entity."""

    lei: str | None = Field(..., description=DESCRIPTION_VALUES["lei"])
    name: str | None


class Address(BaseSchema):
    """Represent an address."""

    language: str | None
    address_lines: list[str]
    address_number: str | None
    address_number_within_building: str | None
    mail_routing: str | None
    city: str
    region: str | None
    country: str
    postal_code: str | None


class Expiration(BaseSchema):
    """Represent expiration data."""

    date: str | None
    reason: str | None


class LegalForm(BaseSchema):
    """Represent the legal form."""

    id: str | None
    other: str | None


class Name(BaseSchema):
    """Represent a name."""

    name: str | None
    language: str | None = None
    type: str | None = None


class RegisteredAt(BaseSchema):
    """Represent registered-at information."""

    id: str
    other: str | None


class Entity(BaseSchema):
    """Represent entity information."""

    associated_entity: GeneralEntity
    category: str
    creation_date: str | None
    event_groups: list[Any]
    expiration: Expiration
    headquarters_address: Address
    jurisdiction: str
    legal_address: Address
    legal_form: LegalForm
    legal_name: Name
    other_addresses: list[Any]
    other_names: list[Name]
    registered_as: str | None = None
    registered_at: RegisteredAt
    status: str
    successor_entities: list[Any]
    sub_category: str | None = None
    successor_entity: GeneralEntity
    transliteraded_other_names: list[Any] | None = None


class Attributes(BaseSchema):
    """Represent attribute information."""

    bic: list[str] | None
    lei: str = Field(..., description=DESCRIPTION_VALUES["lei"])
    entity: Entity
    registration: Registration


class LinkData(BaseSchema):
    """Represent a link."""

    self: str | None
    related: str | None = None
    reporting_exception: str | None = None


class Links(BaseSchema):
    """Represent a wrapped link."""

    links: LinkData


class Relationships(BaseSchema):
    """Represent relationships between records."""

    managing_lou: Links | None = None
    lei_issuer: Links | None = None
    field_modifications: Links | None = None
    direct_parent: Links | None = None
    ultimate_parent: Links | None = None
    direct_children: Links | None = None
    isins: Links | None = None


class Data(BaseSchema):
    """Represent an LEI record data object."""

    id: str
    type: str
    attributes: Attributes
    links: LinkData
    relationships: Relationships


#: Preferred v2 name for a single LEI record.
LeiRecord = Data


# ---------------------------------------------------------------------------
# Meta / pagination
# ---------------------------------------------------------------------------
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

    golden_copy: GoldenCopy | None = None
    pagination: Pagination | None = None


# ---------------------------------------------------------------------------
# Response envelopes
# ---------------------------------------------------------------------------
class GLEIFResponse(BaseSchema):
    """Single LEI record response (``/lei-records/{lei}``)."""

    meta: Meta
    data: Data


class SearchResponse(BaseSchema):
    """Search / list response (``/lei-records``)."""

    meta: Meta
    data: list[Data]


# ---------------------------------------------------------------------------
# ISIN resource (``/lei-records/{lei}/isins``)
# ---------------------------------------------------------------------------
class IsinAttributes(BaseSchema):
    """Attributes of an ISIN-LEI mapping."""

    lei: str
    isin: str


class IsinData(BaseSchema):
    """A single ISIN-LEI mapping record."""

    type: str
    id: str
    attributes: IsinAttributes


class IsinResponse(BaseSchema):
    """ISIN mapping list response."""

    meta: Meta
    data: list[IsinData]


# ---------------------------------------------------------------------------
# Fuzzy completions (``/fuzzycompletions``)
# ---------------------------------------------------------------------------
class FuzzyCompletionValue(BaseSchema):
    """Matched value inside a fuzzy completion result."""

    name: str | None = None


class FuzzyCompletionAttributes(BaseSchema):
    """Attributes of a fuzzy completion result."""

    value: FuzzyCompletionValue


class FuzzyCompletionRelationships(BaseSchema):
    """Relationships of a fuzzy completion result (link to the LEI record)."""

    lei_records: Links | None = None


class FuzzyCompletion(BaseSchema):
    """A single fuzzy completion match."""

    type: str
    attributes: FuzzyCompletionAttributes
    relationships: FuzzyCompletionRelationships | None = None


class FuzzyCompletionResponse(BaseSchema):
    """Fuzzy completion list response."""

    data: list[FuzzyCompletion]


# ---------------------------------------------------------------------------
# Fields metadata (``/fields``)
# ---------------------------------------------------------------------------
class FieldAttributes(BaseSchema):
    """Metadata describing a single LEI data field."""

    key: str | None = None
    field: str | None = None
    label: str | None = None
    data_type: str | None = None
    enum: list[Any] | None = None
    resource: str | None = None
    sortable: bool | None = None
    operators: list[str] | None = None
    contexts: list[Any] | None = None
    xpath: str | None = None


class FieldDescriptor(BaseSchema):
    """A single field descriptor from the ``/fields`` endpoint."""

    type: str
    id: str
    attributes: FieldAttributes


class FieldsResponse(BaseSchema):
    """Fields metadata list response."""

    meta: Meta | None = None
    data: list[FieldDescriptor]

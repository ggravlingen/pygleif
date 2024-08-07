"""Data."""

from datetime import datetime
from typing import Any

from .shared import BaseSchema


class ValidatedAt(BaseSchema):
    """Represent validated at information."""

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
    """Represent a general entity ."""

    lei: str | None
    name: str | None


class Address(BaseSchema):
    """Represent address ."""

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
    """Represent the name."""

    language: str | None
    name: str
    type: str | None = None


class RegisteredAt(BaseSchema):
    """Represent registered at."""

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
    sub_category: str | None | None = None
    successor_entity: GeneralEntity
    transliteraded_other_names: list[Any] | None = None


class Attributes(BaseSchema):
    """Represent attribute information."""

    bic: list[str] | None
    lei: str
    entity: Entity
    registration: Registration


class LinkData(BaseSchema):
    """Represent a link ."""

    self: str | None
    related: str | None = None
    reporting_exception: str | None = None


class Links(BaseSchema):
    """Represent a link ."""

    links: LinkData


class Relationships(BaseSchema):
    """Represent a relationships ."""

    managing_lou: Links | None = None
    lei_issuer: Links | None = None
    field_modifications: Links | None = None
    direct_parent: Links | None = None
    ultimate_parent: Links | None = None


class Data(BaseSchema):
    """Represent data information."""

    id: str
    type: str
    attributes: Attributes
    links: LinkData
    relationships: Relationships

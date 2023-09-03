"""Data."""
from datetime import datetime
from typing import Any

from pydantic.v1 import BaseModel, Field


class ValidatedAt(BaseModel):
    """Represent validated at information."""

    id: str = Field(alias="id")
    other: str | None = Field(alias="other")


class Registration(BaseModel):
    """Represent registration information."""

    corroboration_level: str = Field(alias="corroborationLevel")
    initial_registration_date: datetime = Field(alias="initialRegistrationDate")
    last_update_date: datetime = Field(alias="lastUpdateDate")
    managing_lou: str = Field(alias="managingLou")
    next_renewal_date: datetime = Field(alias="nextRenewalDate")
    other_validation_authorities: list[Any] = Field(alias="otherValidationAuthorities")
    status: str = Field(alias="status")
    validated_as: str = Field(alias="validatedAs")
    validated_at: ValidatedAt = Field(alias="validatedAt")


class GeneralEntity(BaseModel):
    """Represent a general entity ."""

    lei: str | None = Field(alias="lei")
    name: str | None = Field(alias="name")


class Address(BaseModel):
    """Represent address ."""

    language: str = Field(alias="language")
    address_lines: list[str] = Field(alias="addressLines")
    address_number: str | None = Field(alias="addressNumber")
    address_number_within_building: str | None = Field(
        alias="addressNumberWithinBuilding"
    )
    mail_routing: str | None = Field(alias="mailRouting")
    city: str = Field(alias="city")
    region: str | None = Field(alias="region")
    country: str = Field(alias="country")
    postal_code: str | None = Field(alias="postalCode")


class Expiration(BaseModel):
    """Represent expiration data."""

    date: str | None = Field(alias="date")
    reason: str | None = Field(alias="reason")


class LegalForm(BaseModel):
    """Represent the legal form."""

    id: str | None = Field(alias="id")
    other: str | None = Field(alias="other")


class Name(BaseModel):
    """Represent the name."""

    language: str = Field(alias="language")
    name: str = Field(alias="name")
    type: str | None = Field(alias="type")


class RegisteredAt(BaseModel):
    """Represent registered at."""

    id: str = Field(alias="id")
    other: str | None = Field(alias="other")


class Entity(BaseModel):
    """Represent entity information."""

    associated_entity: GeneralEntity = Field(alias="associatedEntity")
    category: str = Field(alias="category")
    creation_date: str | None = Field(alias="creationDate")
    event_groups: list[Any] = Field(alias="eventGroups")
    expiration: Expiration = Field(alias="expiration")
    headquarters_address: Address = Field(alias="headquartersAddress")
    jurisdiction: str = Field(alias="jurisdiction")
    legal_address: Address = Field(alias="legalAddress")
    legal_form: LegalForm = Field(alias="legalForm")
    legal_name: Name = Field(alias="legalName")
    other_addresses: list[Any] = Field(alias="otherAddresses")
    other_names: list[Name] = Field(alias="otherNames")
    registered_as: str = Field(alias="registeredAs")
    registered_at: RegisteredAt = Field(alias="registeredAt")
    status: str = Field(alias="status")
    successor_entities: list[Any] = Field(alias="successorEntities")
    sub_category: str | None = Field(alias="subCategory")
    successor_entity: GeneralEntity = Field(alias="successorEntity")
    transliteraded_other_names: list[Any] = Field(alias="transliteratedOtherNames")


class Attributes(BaseModel):
    """Represent attribute information."""

    bic: list[str] | None = Field(alias="bic")
    lei: str = Field(alias="lei")
    entity: Entity = Field(alias="entity")
    registration: Registration = Field(alias="registration")


class LinkData(BaseModel):
    """Represent a link ."""

    self: str | None = Field(alias="self")
    related: str | None = Field(alias="related")
    reporting_exception: str | None = Field(alias="reporting-exception")


class Links(BaseModel):
    """Represent a link ."""

    links: LinkData = Field(alias="links")


class Relationships(BaseModel):
    """Represent a relationships ."""

    managing_lou: Links = Field(alias="managing-lou")
    lei_issuer: Links = Field(alias="lei-issuer")
    field_modifications: Links = Field(alias="field-modifications")
    direct_parent: Links = Field(alias="direct-parent")
    ultimate_parent: Links = Field(alias="ultimate-parent")


class Data(BaseModel):
    """Represent data information."""

    id: str = Field(alias="id")
    type: str = Field(alias="type")
    attributes: Attributes = Field(alias="attributes")
    links: LinkData = Field(alias="links")
    relationships: Relationships = Field(alias="relationships")

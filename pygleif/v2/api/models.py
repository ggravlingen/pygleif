"""Pydantic v2-bound models for the full GLEIF API v1.0 surface.

Covers the resources exposed by https://api.gleif.org/api/v1:

- ``lei-records``      -> :class:`GLEIFResponse`, :class:`SearchResponse`
- ``lei-records/{lei}/isins`` -> :class:`IsinResponse`
- ``lei-records/{lei}/*-relationship(s)`` -> :class:`RelationshipResponse`,
  :class:`RelationshipListResponse`
- ``lei-records/{lei}/*-reporting-exception`` ->
  :class:`ReportingExceptionResponse`
- ``lei-records/{lei}/field-modifications`` ->
  :class:`FieldModificationResponse`
- ``fuzzycompletions`` -> :class:`FuzzyCompletionResponse`
- ``autocompletions``  -> :class:`AutocompletionResponse`
- ``fields``           -> :class:`FieldsResponse`, :class:`FieldResponse`
- ``lei-issuers``      -> :class:`LeiIssuersResponse`, :class:`LeiIssuerResponse`
- ``vlei-issuers``     -> :class:`VLeiIssuersResponse`, :class:`VLeiIssuerResponse`
- reference data (``countries``, ``entity-legal-forms``,
  ``official-organizational-roles``, ``jurisdictions``, ``regions``,
  ``registration-authorities``, ``registration-agents``) -> typed
  ``*Response`` / list envelopes built on :class:`ResourceData`

The JSON API responses use camelCase keys; models accept both camelCase
(via the alias generator) and snake_case (``populate_by_name``). Keys the
API serves in kebab-case (e.g. ``managing-lou``) carry explicit aliases.
"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - needed at runtime by pydantic
from typing import Any, Generic, TypeVar

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

    self: str | None = None
    related: str | None = None
    relationship_record: str | None = Field(None, alias="relationship-record")
    relationship_records: str | None = Field(None, alias="relationship-records")
    lei_record: str | None = Field(None, alias="lei-record")
    reporting_exception: str | None = Field(None, alias="reporting-exception")


class ResourceIdentifier(BaseSchema):
    """A JSON:API resource identifier (``type`` + ``id``)."""

    type: str | None = None
    id: str | None = None


class Links(BaseSchema):
    """Represent a JSON:API relationship object (links plus identifier)."""

    links: LinkData
    data: ResourceIdentifier | None = None


class Relationships(BaseSchema):
    """Represent relationships between records.

    The API serves these keys in kebab-case (``managing-lou`` etc.), hence
    the explicit aliases.
    """

    managing_lou: Links | None = Field(None, alias="managing-lou")
    lei_issuer: Links | None = Field(None, alias="lei-issuer")
    field_modifications: Links | None = Field(None, alias="field-modifications")
    direct_parent: Links | None = Field(None, alias="direct-parent")
    ultimate_parent: Links | None = Field(None, alias="ultimate-parent")
    direct_children: Links | None = Field(None, alias="direct-children")
    ultimate_children: Links | None = Field(None, alias="ultimate-children")
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
# Fuzzy completions (``/fuzzycompletions``) and autocompletions
# ---------------------------------------------------------------------------
class CompletionRelationships(BaseSchema):
    """Relationships of a completion result (link to the LEI record)."""

    lei_records: Links | None = Field(None, alias="lei-records")


class FuzzyCompletionAttributes(BaseSchema):
    """Attributes of a fuzzy completion result."""

    value: str | None = None


class FuzzyCompletion(BaseSchema):
    """A single fuzzy completion match."""

    type: str
    attributes: FuzzyCompletionAttributes
    relationships: CompletionRelationships | None = None


class FuzzyCompletionResponse(BaseSchema):
    """Fuzzy completion list response."""

    data: list[FuzzyCompletion]


class AutocompletionAttributes(BaseSchema):
    """Attributes of an autocompletion suggestion."""

    value: str | None = None
    highlighting: str | None = None


class Autocompletion(BaseSchema):
    """A single autocompletion suggestion."""

    type: str
    attributes: AutocompletionAttributes
    relationships: CompletionRelationships | None = None


class AutocompletionResponse(BaseSchema):
    """Autocompletion list response."""

    data: list[Autocompletion]


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


class FieldResponse(BaseSchema):
    """Single field metadata response (``/fields/{id}``)."""

    data: FieldDescriptor


# ---------------------------------------------------------------------------
# Generic JSON:API envelopes for typed resources
# ---------------------------------------------------------------------------
AttributesT = TypeVar("AttributesT", bound=BaseSchema)


class ResourceData(BaseSchema, Generic[AttributesT]):
    """A JSON:API data object with resource-specific typed attributes."""

    type: str
    id: str
    attributes: AttributesT
    links: LinkData | None = None


class ResourceResponse(BaseSchema, Generic[AttributesT]):
    """Single-resource response envelope."""

    meta: Meta | None = None
    data: ResourceData[AttributesT]


class ResourceListResponse(BaseSchema, Generic[AttributesT]):
    """Resource list response envelope."""

    meta: Meta | None = None
    data: list[ResourceData[AttributesT]]


# ---------------------------------------------------------------------------
# Relationship records (Level 2, ``/lei-records/{lei}/*-relationship(s)``)
# ---------------------------------------------------------------------------
class RelationshipNode(BaseSchema):
    """Start or end node of a relationship record."""

    id: str | None = None
    type: str | None = None


class RelationshipPeriod(BaseSchema):
    """Validity period reported for a relationship."""

    start_date: datetime | None = None
    end_date: datetime | None = None
    type: str | None = None


class RelationshipDetail(BaseSchema):
    """The reported relationship between two LEI records."""

    start_node: RelationshipNode | None = None
    end_node: RelationshipNode | None = None
    type: str | None = None
    status: str | None = None
    periods: list[RelationshipPeriod] = Field(default_factory=list)


class RelationshipRegistration(BaseSchema):
    """Registration details of a relationship record."""

    initial_registration_date: datetime | None = None
    last_update_date: datetime | None = None
    status: str | None = None
    next_renewal_date: datetime | None = None
    managing_lou: str | None = None
    corroboration_level: str | None = None
    corroboration_documents: str | None = None
    corroboration_reference: str | None = None


class RelationshipAttributes(BaseSchema):
    """Attributes of a relationship record."""

    valid_from: datetime | None = None
    valid_to: datetime | None = None
    relationship: RelationshipDetail | None = None
    registration: RelationshipRegistration | None = None


RelationshipData = ResourceData[RelationshipAttributes]
RelationshipResponse = ResourceResponse[RelationshipAttributes]
RelationshipListResponse = ResourceListResponse[RelationshipAttributes]


# ---------------------------------------------------------------------------
# Reporting exceptions (``/lei-records/{lei}/*-reporting-exception``)
# ---------------------------------------------------------------------------
class ReportingExceptionAttributes(BaseSchema):
    """Attributes of a Level 2 reporting exception."""

    valid_from: datetime | None = None
    valid_to: datetime | None = None
    lei: str | None = None
    category: str | None = None
    reason: str | None = None
    reference: str | None = None


ReportingExceptionData = ResourceData[ReportingExceptionAttributes]
ReportingExceptionResponse = ResourceResponse[ReportingExceptionAttributes]


# ---------------------------------------------------------------------------
# Field modifications (``/lei-records/{lei}/field-modifications``)
# ---------------------------------------------------------------------------
class FieldModificationAttributes(BaseSchema):
    """A single historical change to an LEI record field."""

    lei: str | None = None
    record_type: str | None = None
    modification_type: str | None = None
    field: str | None = None
    date: datetime | None = None
    value_old: Any = None
    value_new: Any = None
    context: Any = None


FieldModificationData = ResourceData[FieldModificationAttributes]
FieldModificationResponse = ResourceListResponse[FieldModificationAttributes]


# ---------------------------------------------------------------------------
# LEI issuers (``/lei-issuers``) and vLEI issuers (``/vlei-issuers``)
# ---------------------------------------------------------------------------
class LeiIssuerAttributes(BaseSchema):
    """Attributes of an LEI issuer (Local Operating Unit)."""

    lei: str | None = None
    name: str | None = None
    marketing_name: str | None = None
    reporting_name: str | None = None
    website: str | None = None
    organization_type: str | None = None
    short_description: str | None = None
    legal_domicile: str | None = None
    accreditation_date: str | None = None


LeiIssuerData = ResourceData[LeiIssuerAttributes]
LeiIssuerResponse = ResourceResponse[LeiIssuerAttributes]
LeiIssuersResponse = ResourceListResponse[LeiIssuerAttributes]


class LeiIssuerJurisdictionAttributes(BaseSchema):
    """Jurisdiction an LEI issuer is accredited for."""

    country_code: str | None = None
    accredited_as: str | None = None
    start_date: str | None = None
    end_date: str | None = None


LeiIssuerJurisdictionsResponse = ResourceListResponse[LeiIssuerJurisdictionAttributes]


class VLeiIssuerAttributes(BaseSchema):
    """Attributes of a qualified vLEI issuing organization."""

    lei: str | None = None
    name: str | None = None
    website: str | None = None
    marketing_name: str | None = None
    qualification_date: str | None = None


VLeiIssuerData = ResourceData[VLeiIssuerAttributes]
VLeiIssuerResponse = ResourceResponse[VLeiIssuerAttributes]
VLeiIssuersResponse = ResourceListResponse[VLeiIssuerAttributes]


# ---------------------------------------------------------------------------
# Reference data code lists
# ---------------------------------------------------------------------------
class CountryAttributes(BaseSchema):
    """ISO 3166 country code entry."""

    code: str | None = None
    name: str | None = None


CountryData = ResourceData[CountryAttributes]
CountryResponse = ResourceResponse[CountryAttributes]
CountriesResponse = ResourceListResponse[CountryAttributes]


class JurisdictionAttributes(BaseSchema):
    """Legal jurisdiction entry (ISO 3166 country / sub-region codes)."""

    code: str | None = None
    name: str | None = None


JurisdictionData = ResourceData[JurisdictionAttributes]
JurisdictionResponse = ResourceResponse[JurisdictionAttributes]
JurisdictionsResponse = ResourceListResponse[JurisdictionAttributes]


class RegionAttributes(BaseSchema):
    """ISO 3166 sub-region code entry."""

    code: str | None = None
    name: str | None = None


RegionData = ResourceData[RegionAttributes]
RegionResponse = ResourceResponse[RegionAttributes]
RegionsResponse = ResourceListResponse[RegionAttributes]


class LocalizedName(BaseSchema):
    """Localized name entry used by the ELF and OOR code lists."""

    name: str | None = None
    local_name: str | None = None
    language: str | None = None
    language_code: str | None = None
    transliterated_name: str | None = None


class EntityLegalFormAttributes(BaseSchema):
    """ISO 20275 entity legal form (ELF) code entry."""

    code: str | None = None
    country: str | None = None
    jurisdiction: str | None = None
    country_code: str | None = None
    subdivision_code: str | None = None
    date_created: str | None = None
    status: str | None = None
    names: list[LocalizedName] = Field(default_factory=list)


EntityLegalFormData = ResourceData[EntityLegalFormAttributes]
EntityLegalFormResponse = ResourceResponse[EntityLegalFormAttributes]
EntityLegalFormsResponse = ResourceListResponse[EntityLegalFormAttributes]


class OfficialOrganizationalRoleAttributes(BaseSchema):
    """ISO 5009 official organizational role (OOR) code entry."""

    code: str | None = None
    country: str | None = None
    jurisdiction: str | None = None
    country_code: str | None = None
    subdivision_code: str | None = None
    date_created: str | None = None
    status: str | None = None
    elf_code: str | None = None
    names: list[LocalizedName] = Field(default_factory=list)


OfficialOrganizationalRoleData = ResourceData[OfficialOrganizationalRoleAttributes]
OfficialOrganizationalRoleResponse = ResourceResponse[
    OfficialOrganizationalRoleAttributes
]
OfficialOrganizationalRolesResponse = ResourceListResponse[
    OfficialOrganizationalRoleAttributes
]


class RegistrationAuthorityJurisdiction(BaseSchema):
    """Jurisdiction covered by a registration authority."""

    country: str | None = None
    country_code: str | None = None
    jurisdiction: str | None = None


class RegistrationAuthorityAttributes(BaseSchema):
    """GLEIF Registration Authority (RA) code list entry."""

    code: str | None = None
    international_name: str | None = None
    local_name: str | None = None
    international_organization_name: str | None = None
    local_organization_name: str | None = None
    website: str | None = None
    jurisdictions: list[RegistrationAuthorityJurisdiction] = Field(
        default_factory=list,
    )


RegistrationAuthorityData = ResourceData[RegistrationAuthorityAttributes]
RegistrationAuthorityResponse = ResourceResponse[RegistrationAuthorityAttributes]
RegistrationAuthoritiesResponse = ResourceListResponse[RegistrationAuthorityAttributes]


class RegistrationAgentAttributes(BaseSchema):
    """Registration agent entry."""

    name: str | None = None
    lei: str | None = None
    lei_issuer: str | None = None
    websites: list[str] = Field(default_factory=list)


RegistrationAgentData = ResourceData[RegistrationAgentAttributes]
RegistrationAgentResponse = ResourceResponse[RegistrationAgentAttributes]
RegistrationAgentsResponse = ResourceListResponse[RegistrationAgentAttributes]

from .const import (
    ATTR_ADDRESS_CITY,
    ATTR_ADDRESS_COUNTRY,
    ATTR_DOLLAR_SIGN,
    ATTR_ADDRESS_LINE1,
    ATTR_ADDRESS_POSTAL_CODE,
    ATTR_ADDRESS_REGION,
    ATTR_ADDRESS_TYPE_HQ,
    ATTR_ADDRESS_TYPE_LEGAL,
    ATTR_ENTITY,
    ATTR_REGISTER,
    ATTR_REGISTRATION,
    URL_API
)
import urllib.request
import json
from bs4 import BeautifulSoup

class GLEIF:
    """Parse JSON from GLEIF registry. Supports v1 of API."""

    def __init__(self, lei_code):
        self.lei_code = lei_code

    @property
    def raw(self):
        r = urllib.request.urlopen(URL_API+self.lei_code)
        return json.loads(r.read().decode('UTF-8'))[0]

    @property
    def lei(self):
        return self.raw['LEI'][ATTR_DOLLAR_SIGN]

    @property
    def entity(self):
        return GLEIFEntity(self)

    @property
    def registration(self):
        return GLEIFRegistration(self)


class GLEIFRegistration:

    def __init__(self, registration):
        self._registration = registration

    @property
    def raw(self):
        return self._registration.raw[ATTR_REGISTRATION]

    @property
    def initial_registration_date(self):
        return self.raw['InitialRegistrationDate'][ATTR_DOLLAR_SIGN]

    @property
    def last_update_date(self):
        return self.raw['LastUpdateDate'][ATTR_DOLLAR_SIGN]

    @property
    def managing_lou(self):
        return self.raw['ManagingLOU'][ATTR_DOLLAR_SIGN]

    @property
    def next_renewal_date(self):
        return self.raw['NextRenewalDate'][ATTR_DOLLAR_SIGN]

    @property
    def registration_status(self):
        return self.raw['RegistrationStatus'][ATTR_DOLLAR_SIGN]

    @property
    def validation_sources(self):
        return self.raw['ValidationSources'][ATTR_DOLLAR_SIGN]


class GLEIFEntity:

    def __init__(self, entity):
        self._entity = entity

    @property
    def raw(self):
        return self._entity.raw[ATTR_ENTITY]

    @property
    def business_register_entity_id(self):
        return self.raw['BusinessRegisterEntityID'][ATTR_REGISTER]

    @property
    def entity_status(self):
        return self.raw['EntityStatus'][ATTR_DOLLAR_SIGN]

    @property
    def legal_form(self):
        return self.raw['LegalForm'][ATTR_DOLLAR_SIGN]

    @property
    def legal_jurisdiction(self):
        return self.raw['LegalJurisdiction'][ATTR_DOLLAR_SIGN]

    @property
    def legal_name(self):
        return self.raw['LegalName'][ATTR_DOLLAR_SIGN]

    @property
    def headquarters_address(self):
        return Address(self, ATTR_ADDRESS_TYPE_HQ)

    @property
    def legal_address(self):
        return Address(self, ATTR_ADDRESS_TYPE_LEGAL)


class Address:

    def __init__(self, address, address_type):
        self._address = address
        self.address_type = address_type

    @property
    def raw(self):
        return self._address.raw[self.address_type]

    @property
    def city(self):
        return self.raw[ATTR_ADDRESS_CITY][ATTR_DOLLAR_SIGN]

    @property
    def country(self):
        return self.raw[ATTR_ADDRESS_COUNTRY][ATTR_DOLLAR_SIGN]

    @property
    def line1(self):
        return self.raw[ATTR_ADDRESS_LINE1][ATTR_DOLLAR_SIGN]

    @property
    def postal_code(self):
        return self.raw[ATTR_ADDRESS_POSTAL_CODE][ATTR_DOLLAR_SIGN]

    @property
    def region(self):
        return self.raw[ATTR_ADDRESS_REGION][ATTR_DOLLAR_SIGN]


class GLEIFParseRelationshipRecord:

    def __init__(self, record_xml):
        self.record_xml = record_xml

    @property
    def raw(self):
        return BeautifulSoup(self.record_xml, 'xml')

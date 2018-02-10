from .const import (
    ATTR_ADDRESS_CITY,
    ATTR_ADDRESS_COUNTRY,
    ATTR_DOLLAR_SIGN,
    ATTR_ENTITY_BUSINESS_REGISTER_ENTITY_ID,
    ATTR_ENTITY_ENTITY_STATUS,
    ATTR_ENTITY_LEGAL_FORM,
    ATTR_ENTITY_LEGAL_JURISDICTION,
    ATTR_ENTITY_LEGAL_NAME,
    ATTR_ADDRESS_LINE1,
    ATTR_ADDRESS_POSTAL_CODE,
    ATTR_ADDRESS_REGION,
    ATTR_ADDRESS_TYPE_HQ,
    ATTR_ADDRESS_TYPE_LEGAL,
    ATTR_ENTITY,
    ATTR_INITIAL_REGISTRATION_DATE,
    ATTR_LAST_UPDATE_DATE,
    ATTR_MANAGING_LOU,
    ATTR_NEXT_RENEWAL_DATE,
    ATTR_LEI,
    ATTR_REGISTER,
    ATTR_REGISTRATION_STATUS,
    ATTR_REGISTRATION,
    ATTR_VALIDATION_SOURCES,
    URL_API
)
import urllib.request
import json
from bs4 import BeautifulSoup
from dateutil import parser


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
        return self.raw[ATTR_LEI][ATTR_DOLLAR_SIGN]

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
        if ATTR_INITIAL_REGISTRATION_DATE in self.raw:
            return parser.parse(
                self.raw[ATTR_INITIAL_REGISTRATION_DATE][ATTR_DOLLAR_SIGN])

    @property
    def last_update_date(self):
        if ATTR_LAST_UPDATE_DATE in self.raw:
            return parser.parse(
                self.raw[ATTR_LAST_UPDATE_DATE][ATTR_DOLLAR_SIGN])

    @property
    def managing_lou(self):
        if ATTR_MANAGING_LOU in self.raw:
            return self.raw[ATTR_MANAGING_LOU][ATTR_DOLLAR_SIGN]

    @property
    def next_renewal_date(self):
        if ATTR_NEXT_RENEWAL_DATE in self.raw:
            return parser.parse(
                self.raw[ATTR_NEXT_RENEWAL_DATE][ATTR_DOLLAR_SIGN])

    @property
    def registration_status(self):
        if ATTR_REGISTRATION_STATUS in self.raw:
            return self.raw[ATTR_REGISTRATION_STATUS][ATTR_DOLLAR_SIGN]

    @property
    def validation_sources(self):
        if ATTR_VALIDATION_SOURCES in self.raw:
            return self.raw[ATTR_VALIDATION_SOURCES][ATTR_DOLLAR_SIGN]


class GLEIFEntity:
    def __init__(self, entity):
        self._entity = entity

    @property
    def raw(self):
        return self._entity.raw[ATTR_ENTITY]

    @property
    def business_register_entity_id(self):
        if ATTR_ENTITY_BUSINESS_REGISTER_ENTITY_ID in self.raw:
            return self.raw[
                ATTR_ENTITY_BUSINESS_REGISTER_ENTITY_ID][ATTR_REGISTER]

    @property
    def entity_status(self):
        if ATTR_ENTITY_ENTITY_STATUS in self.raw:
            return self.raw[ATTR_ENTITY_ENTITY_STATUS][ATTR_DOLLAR_SIGN]

    @property
    def legal_form(self):
        if ATTR_ENTITY_LEGAL_FORM in self.raw:
            return self.raw[ATTR_ENTITY_LEGAL_FORM][ATTR_DOLLAR_SIGN]

    @property
    def legal_jurisdiction(self):
        if ATTR_ENTITY_LEGAL_JURISDICTION in self.raw:
            return self.raw[ATTR_ENTITY_LEGAL_JURISDICTION][ATTR_DOLLAR_SIGN]

    @property
    def legal_name(self):
        if ATTR_ENTITY_LEGAL_NAME in self.raw:
            return self.raw[ATTR_ENTITY_LEGAL_NAME][ATTR_DOLLAR_SIGN]

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
        if ATTR_ADDRESS_CITY in self.raw:
            return self.raw[ATTR_ADDRESS_CITY][ATTR_DOLLAR_SIGN]

    @property
    def country(self):
        if ATTR_ADDRESS_COUNTRY in self.raw:
            return self.raw[ATTR_ADDRESS_COUNTRY][ATTR_DOLLAR_SIGN]

    @property
    def line1(self):
        if ATTR_ADDRESS_LINE1 in self.raw:
            return self.raw[ATTR_ADDRESS_LINE1][ATTR_DOLLAR_SIGN]

    @property
    def postal_code(self):
        if ATTR_ADDRESS_POSTAL_CODE in self.raw:
            return self.raw[ATTR_ADDRESS_POSTAL_CODE][ATTR_DOLLAR_SIGN]

    @property
    def region(self):
        if ATTR_ADDRESS_REGION in self.raw:
            return self.raw[ATTR_ADDRESS_REGION][ATTR_DOLLAR_SIGN]


class GLEIFParseRelationshipRecord:

    def __init__(self, record_xml):
        self.record_xml = record_xml

    @property
    def raw(self):
        return BeautifulSoup(self.record_xml, 'xml')

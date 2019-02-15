import warnings
from .const import (
    ATTR_ADDRESS_CITY,
    ATTR_ADDRESS_COUNTRY,
    ATTR_DOLLAR_SIGN,
    ATTR_ENTITY_REGISTRATION_AUTHORITY,
    ATTR_ENTITY_REGISTRATION_AUTHORITY_ENTITY_ID,
    ATTR_ENTITY_ENTITY_STATUS,
    ATTR_ENTITY_LEGAL_FORM,
    ATTR_ENTITY_LEGAL_FORM_CODE,
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
    ATTR_REGISTRATION_STATUS,
    ATTR_REGISTRATION,
    ATTR_VALIDATION_SOURCES,
    URL_API,
    LEGAL_FORMS,
    URL_SEARCH,
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
    def json_data(self):
        return urllib.request.urlopen(URL_API+self.lei_code)

    @property
    def lei_exists(self):

        try:
            self.raw
            return False
        except IndexError:
            return True

    @property
    def raw(self):
        return json.loads(self.json_data.read().decode('UTF-8'))[0]

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
    def registration_authority_entity_id(self):
        """
        Some entities return the register entity id,
        but other do not. Unsure if this is a bug or
        inconsistently registered data.
        """

        if ATTR_ENTITY_REGISTRATION_AUTHORITY in self.raw:
            try:
                return self.raw[
                    ATTR_ENTITY_REGISTRATION_AUTHORITY][
                    ATTR_ENTITY_REGISTRATION_AUTHORITY_ENTITY_ID][
                    ATTR_DOLLAR_SIGN]
            except KeyError:
                pass

    @property
    def business_register_entity_id(self):
        """Deprecated."""

        warnings.warn("This property is deprecated.", DeprecationWarning)

        return self.registration_authority_entity_id

    @property
    def entity_status(self):
        if ATTR_ENTITY_ENTITY_STATUS in self.raw:
            return self.raw[ATTR_ENTITY_ENTITY_STATUS][ATTR_DOLLAR_SIGN]

    @property
    def legal_form(self):
        """In some cases, the legal form is stored in the JSON-data.
        In other cases, an ELF-code, consisting of mix of exactly
        four letters and numbers are stored. This ELF-code
        can be looked up in a registry where a code maps to
        a organizational type. ELF-codes are not unique,
        it can reoccur under different names in different
        countries"""

        if ATTR_ENTITY_LEGAL_FORM in self.raw:
            try:
                return LEGAL_FORMS[self.legal_jurisdiction][
                    self.raw[ATTR_ENTITY_LEGAL_FORM][
                        ATTR_ENTITY_LEGAL_FORM_CODE][ATTR_DOLLAR_SIGN]
                ]
            except KeyError:
                legal_form = self.raw[
                    ATTR_ENTITY_LEGAL_FORM][
                    ATTR_ENTITY_LEGAL_FORM_CODE][ATTR_DOLLAR_SIGN]

                if len(legal_form) == 4:
                    # If this is returned, the ELF should
                    # be added to the constants.
                    return 'ELF code: ' + legal_form
                else:
                    return legal_form

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


class Search:
    """Class to use the search form of the GLEIF web site."""

    def __init__(self, orgnr=None):
        """Init class."""

        # Allow searching using organisation number
        self.orgnr = orgnr

    @property
    def json_data(self):
        """Get raw data from the service."""

        return urllib.request.urlopen(URL_SEARCH + self.orgnr)

    @property
    def raw(self):
        """Return parsed json."""

        return json.loads(self.json_data.read().decode('UTF-8'))

    @property
    def lei(self):
        """Return the LEI code."""

        try:
            return self.raw['data'][0]['attributes']['lei']
        except IndexError:
            return None

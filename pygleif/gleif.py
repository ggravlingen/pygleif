import urllib.request
import json


class GLEIF:
    """Parse JSON from GLEIF registry. Supports v1 of API."""

    def __init__(self, lei_code):
        self.lei_code = lei_code

    @property
    def raw(self):
        r = urllib.request.urlopen(
            'https://leilookup.gleif.org/api/v1/leirecords?lei=' +
            self.lei_code)
        return json.loads(r.read().decode('UTF-8'))[0]

    @property
    def lei(self):
        return self.raw['LEI']['$']

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
        return self._registration.raw['Registration']

    @property
    def initial_registration_date(self):
        return self.raw['InitialRegistrationDate']['$']

    @property
    def last_update_date(self):
        return self.raw['LastUpdateDate']['$']

    @property
    def managing_lou(self):
        return self.raw['ManagingLOU']['$']

    @property
    def next_renewal_date(self):
        return self.raw['NextRenewalDate']['$']

    @property
    def registration_status(self):
        return self.raw['RegistrationStatus']['$']

    @property
    def validation_sources(self):
        return self.raw['ValidationSources']['$']


class GLEIFEntity:

    def __init__(self, entity):
        self._entity = entity

    @property
    def raw(self):
        return self._entity.raw['Entity']

    @property
    def business_register_entity_id(self):
        return self.raw['BusinessRegisterEntityID']['@register']

    @property
    def entity_status(self):
        return self.raw['EntityStatus']['$']

    @property
    def legal_form(self):
        return self.raw['LegalForm']['$']

    @property
    def legal_jurisdiction(self):
        return self.raw['LegalJurisdiction']['$']

    @property
    def legal_name(self):
        return self.raw['LegalName']['$']

    @property
    def headquarters_address(self):
        return Address(self, 'HeadquartersAddress')

    @property
    def legal_address(self):
        return Address(self, 'LegalAddress')


class Address:

    def __init__(self, address, address_type):
        self._address = address
        self.address_type = address_type

    @property
    def raw(self):
        return self._address.raw[self.address_type]

    @property
    def city(self):
        return self.raw['City']['$']

    @property
    def country(self):
        return self.raw['Country']['$']

    @property
    def line1(self):
        return self.raw['Line1']['$']

    @property
    def postal_code(self):
        return self.raw['PostalCode']['$']

    @property
    def region(self):
        return self.raw['Region']['$']

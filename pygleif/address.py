"""Address."""
from pygleif.const import (
    ATTR_ADDRESS_CITY,
    ATTR_ADDRESS_COUNTRY,
    ATTR_ADDRESS_LINE1,
    ATTR_ADDRESS_POSTAL_CODE,
    ATTR_ADDRESS_REGION,
)


class Address:
    def __init__(self, address, address_type):
        self._address = address
        self.address_type = address_type

    @property
    def raw(self):
        return self._address.raw.get(self.address_type)

    @property
    def city(self):
        return self.raw.get(ATTR_ADDRESS_CITY, None)

    @property
    def country(self):
        return self.raw.get(ATTR_ADDRESS_COUNTRY, None)

    @property
    def line1(self):
        address_lines = self.raw.get(ATTR_ADDRESS_LINE1, None)
        if address_lines:
            return address_lines[0]

    @property
    def postal_code(self):
        return self.raw.get(ATTR_ADDRESS_POSTAL_CODE, None)

    @property
    def region(self):
        return self.raw.get(ATTR_ADDRESS_REGION, None)

"""Registration data."""
from dateutil import parser

from pygleif.const import (
    ATTR_INITIAL_REGISTRATION_DATE,
    ATTR_LAST_UPDATE_DATE,
    ATTR_MANAGING_LOU,
    ATTR_NEXT_RENEWAL_DATE,
    ATTR_REGISTRATION,
    ATTR_STATUS,
    ATTR_VALIDATION_SOURCES,
)


class GLEIFRegistration:
    def __init__(self, registration):
        self._registration = registration

    @property
    def raw(self):
        return self._registration.raw.get(ATTR_REGISTRATION)

    @property
    def initial_registration_date(self):
        if ATTR_INITIAL_REGISTRATION_DATE in self.raw:
            return parser.parse(self.raw.get(ATTR_INITIAL_REGISTRATION_DATE))

    @property
    def last_update_date(self):
        if ATTR_LAST_UPDATE_DATE in self.raw:
            return parser.parse(self.raw.get(ATTR_LAST_UPDATE_DATE))

    @property
    def managing_lou(self):
        if ATTR_MANAGING_LOU in self.raw:
            return self.raw[ATTR_MANAGING_LOU]

    @property
    def next_renewal_date(self):
        if ATTR_NEXT_RENEWAL_DATE in self.raw:
            return parser.parse(self.raw[ATTR_NEXT_RENEWAL_DATE])

    @property
    def registration_status(self):
        if ATTR_STATUS in self.raw:
            return self.raw[ATTR_STATUS]

    @property
    def validation_sources(self):
        if ATTR_VALIDATION_SOURCES in self.raw:
            return self.raw[ATTR_VALIDATION_SOURCES]

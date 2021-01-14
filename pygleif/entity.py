"""Entity."""

from pygleif.address import Address
from pygleif.const import (
    ATTR_ADDRESS_TYPE_HQ,
    ATTR_ADDRESS_TYPE_LEGAL,
    ATTR_ENTITY,
    ATTR_ENTITY_LEGAL_FORM,
    ATTR_ENTITY_LEGAL_NAME,
    ATTR_ENTITY_REGISTERED_AS,
    ATTR_ID,
    ATTR_JURISDICTION,
    ATTR_NAME,
    ATTR_STATUS,
    LEGAL_FORMS,
)


class GLEIFEntity:
    def __init__(self, entity):
        self._entity = entity

    @property
    def raw(self):
        """Return raw data."""
        return self._entity.raw[ATTR_ENTITY]

    @property
    def registration_authority_entity_id(self):
        """
        Some entities return the register entity id,
        but other do not. Unsure if this is a bug or
        inconsistently registered data.
        """
        return self.raw.get(ATTR_ENTITY_REGISTERED_AS)

    @property
    def entity_status(self):
        """Return entity status."""
        return self.raw.get(ATTR_STATUS)

    @property
    def legal_form(self):
        """In some cases, the legal form is stored in the JSON-data.
        In other cases, an ELF-code, consisting of mix of exactly
        four letters and numbers are stored. This ELF-code
        can be looked up in a registry where a code maps to
        a organizational type. ELF-codes are not unique,
        it can reoccur under different names in different
        countries"""
        legal_form_id = self.raw.get(ATTR_ENTITY_LEGAL_FORM).get(ATTR_ID)

        if (
            self.legal_jurisdiction in LEGAL_FORMS
            and legal_form_id in LEGAL_FORMS[self.legal_jurisdiction]
        ):
            return LEGAL_FORMS[self.legal_jurisdiction][legal_form_id]

        return f"ELF code: {legal_form_id}"

    @property
    def legal_jurisdiction(self):
        """Return legal jurisdiction."""
        return self.raw.get(ATTR_JURISDICTION)

    @property
    def legal_name(self):
        """Return legal name."""
        return self.raw.get(ATTR_ENTITY_LEGAL_NAME).get(ATTR_NAME)

    @property
    def headquarters_address(self):
        return Address(self, ATTR_ADDRESS_TYPE_HQ)

    @property
    def legal_address(self):
        return Address(self, ATTR_ADDRESS_TYPE_LEGAL)

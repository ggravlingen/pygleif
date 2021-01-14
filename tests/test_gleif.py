"""Tests."""
import datetime
import unittest

from dateutil.tz import tzutc

from pygleif import GLEIF, GLEIFParseRelationshipRecord
from sample_data import XML_DATA


class TestGLEIFEntity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = GLEIF("549300MLUDYVRQOOXS22")

    def test_lei(self):
        self.assertEqual(self.data.lei, "549300MLUDYVRQOOXS22")

    def test_gleif_entity_registration_authority_entity_id(self):
        self.assertEqual(self.data.entity.registration_authority_entity_id, "917685991")

    def test_gleif_entity_legal_jurisdiction(self):
        self.assertEqual(self.data.entity.legal_jurisdiction, "NO")

    def test_gleif_entity_legal_form(self):
        self.assertEqual(self.data.entity.legal_form, "Aksjeselskap")

    def test_gleif_entity_legal_name(self):
        self.assertEqual(self.data.entity.legal_name, "NORDIC CREDIT RATING AS")

    def test_gleif_entity_entity_status(self):
        self.assertEqual(self.data.entity.entity_status, "ACTIVE")


class TestGLEIFEntityLegalAddress(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = GLEIF("549300MLUDYVRQOOXS22")

    def test_gleif_entity_legal_address_line1(self):
        self.assertEqual(
            self.data.entity.legal_address.line1, "Biskop Gunnerus' gate 14A"
        )

    def test_gleif_entity_legal_address_city(self):
        self.assertEqual(self.data.entity.legal_address.city, "OSLO")

    def test_gleif_entity_legal_address_region(self):
        self.assertEqual(self.data.entity.legal_address.region, "NO-03")

    def test_gleif_entity_legal_address_country(self):
        self.assertEqual(self.data.entity.legal_address.country, "NO")

    def test_gleif_entity_legal_address_postal_code(self):
        self.assertEqual(self.data.entity.legal_address.postal_code, "0185")


class TestGLEIFEntityHQAddress(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = GLEIF("549300MLUDYVRQOOXS22")

    def test_gleif_entity_hq_address_line1(self):
        self.assertEqual(
            self.data.entity.headquarters_address.line1, "Biskop Gunnerus' gate 14A"
        )

    def test_gleif_entity_hq_address_city(self):
        self.assertEqual(self.data.entity.headquarters_address.city, "OSLO")

    def test_gleif_entity_hq_address_region(self):
        self.assertEqual(self.data.entity.headquarters_address.region, "NO-03")

    def test_gleif_entity_hq_address_country(self):
        self.assertEqual(self.data.entity.headquarters_address.country, "NO")

    def test_gleif_entity_hq_address_postal_code(self):
        self.assertEqual(self.data.entity.headquarters_address.postal_code, "0185")


class TestGLEIFEntityRegistration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = GLEIF("549300MLUDYVRQOOXS22")

    def test_gleif_registration_initial_registration_date(self):
        self.assertEqual(
            self.data.registration.initial_registration_date,
            datetime.datetime(2017, 4, 29, 2, 2, tzinfo=tzutc()),
        )

    def test_gleif_registration_last_update_date(self):
        self.assertEqual(
            datetime.datetime(2020, 11, 4, 8, 22, 43, tzinfo=tzutc()),
            self.data.registration.last_update_date,
        )

    def test_gleif_registration_registration_status(self):
        self.assertEqual(self.data.registration.registration_status, "ISSUED")

    def test_gleif_registration_next_renewal_date(self):
        self.assertEqual(
            self.data.registration.next_renewal_date,
            datetime.datetime(2021, 12, 4, 12, 36, 42, tzinfo=tzutc()),
        )

    def test_gleif_registration_managing_lou(self):
        self.assertEqual(self.data.registration.managing_lou, "529900F6BNUR3RJ2WH29")

    def test_gleif_registration_validation_sources(self):
        self.assertEqual(
            self.data.registration.validation_sources, "FULLY_CORROBORATED"
        )


class TestGLEIFRelationshipRecord(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = GLEIFParseRelationshipRecord(XML_DATA)

    def test_relationship_record(self):
        self.assertEqual(
            self.data.raw.Relationship.StartNode.NodeID.text, "097900BEJX0000001852"
        )


class TestEntitySpecialCase(unittest.TestCase):
    def test_break_gleif_entity(self):
        data = GLEIF("549300MWQEN1427O5L53")
        self.assertEqual(data.entity.legal_form, "Aktiebolag")

        data = GLEIF("MAES062Z21O4RZ2U7M96")
        self.assertEqual(data.entity.legal_form, "ELF code: ZRPO")

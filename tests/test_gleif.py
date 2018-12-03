from pygleif import GLEIF, GLEIFParseRelationshipRecord
import datetime
from dateutil.tz import tzutc
import unittest
from sample_data import XML_DATA


class TestGLEIF(unittest.TestCase):

    def setUp(self):
        self.data = GLEIF('549300MLUDYVRQOOXS22')

    def test_lei(self):
        self.assertEqual(self.data.lei, '549300MLUDYVRQOOXS22')

    def test_gleif_entity(self):
        self.assertEqual(self.data.entity.registration_authority_entity_id,
                         "917 685 991")
        self.assertEqual(self.data.entity.legal_jurisdiction, "NO")
        self.assertEqual(self.data.entity.legal_form, "Aksjeselskap")
        self.assertEqual(self.data.entity.legal_name,
                         "Nordic Credit Rating AS")
        self.assertEqual(self.data.entity.entity_status, "ACTIVE")

    def test_gleif_entity_legal_address(self):
        self.assertEqual(self.data.entity.legal_address.line1,
                         "Haakon VII's gate 1")
        self.assertEqual(self.data.entity.legal_address.city, "Oslo")
        self.assertEqual(self.data.entity.legal_address.region, "NO-03")
        self.assertEqual(self.data.entity.legal_address.country, "NO")
        self.assertEqual(self.data.entity.legal_address.postal_code, "0161")

    def test_gleif_entity_hq_address(self):
        self.assertEqual(self.data.entity.headquarters_address.line1,
                         "Haakon VII's gate 1")
        self.assertEqual(self.data.entity.headquarters_address.city, "Oslo")
        self.assertEqual(self.data.entity.headquarters_address.region,
                         "NO-03")
        self.assertEqual(self.data.entity.headquarters_address.country, "NO")
        self.assertEqual(self.data.entity.headquarters_address.postal_code,
                         "0161")

    def test_gleif_registration(self):

        self.assertEqual(self.data.registration.initial_registration_date,
                         datetime.datetime(2017, 4, 29, 2, 2, tzinfo=tzutc()))
        self.assertEqual(self.data.registration.last_update_date,
                         datetime.datetime(2018, 4, 9, 21, 30, tzinfo=tzutc()))
        self.assertEqual(self.data.registration.registration_status, "ISSUED")
        self.assertEqual(self.data.registration.next_renewal_date,
                         datetime.datetime(2019, 4, 3, 10, 30,
                                           tzinfo=tzutc()))
        self.assertEqual(self.data.registration.managing_lou,
                         "EVK05KS7XY1DEII3R011")
        self.assertEqual(self.data.registration.validation_sources,
                         "FULLY_CORROBORATED")


class TestGLEIFRelationshipRecord(unittest.TestCase):

    def setUp(self):
        self.data = GLEIFParseRelationshipRecord(XML_DATA)

    def test_relationship_record(self):
        self.assertEqual(self.data.raw.Relationship.StartNode.NodeID.text,
                         '097900BEJX0000001852')


class TestEntitySpecialCase(unittest.TestCase):

    def test_break_gleif_entity(self):
        data = GLEIF('549300MWQEN1427O5L53')
        self.assertEqual(data.entity.legal_form, "Aktiebolag")

        data = GLEIF('MAES062Z21O4RZ2U7M96')
        self.assertEqual(data.entity.legal_form, "ELF code: ZRPO")

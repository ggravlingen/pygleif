from pygleif.gleif import GLEIF, GLEIFParseRelationshipRecord
import datetime
from dateutil.tz import tzutc
import unittest
from sample_data import LEI_DATA, XML_DATA


class TestGLEIF(unittest.TestCase):

    def test_gleif(self):
        data = GLEIF('549300MLUDYVRQOOXS22')

        assert data.lei == '549300MLUDYVRQOOXS22'


    def test_gleif_entity(self):
        data = GLEIF('549300MLUDYVRQOOXS22')

        assert data.entity.business_register_entity_id == "NO001"

        assert data.entity.legal_address.line1 == "Haakon VII's gate 1"
        assert data.entity.legal_address.city == "Oslo"
        assert data.entity.legal_address.region == "NO-03"
        assert data.entity.legal_address.country == "NO"
        assert data.entity.legal_address.postal_code == "0161"

        assert data.entity.headquarters_address.line1 == "Haakon VII's gate 1"
        assert data.entity.headquarters_address.city == "Oslo"
        assert data.entity.headquarters_address.region == "NO-03"
        assert data.entity.headquarters_address.country == "NO"
        assert data.entity.headquarters_address.postal_code == "0161"

        assert data.entity.business_register_entity_id == "NO001"
        assert data.entity.legal_jurisdiction == "NO"
        assert data.entity.legal_form == "Aksjeselskap"
        assert data.entity.legal_name == "Nordic Credit Rating AS"
        assert data.entity.entity_status == "ACTIVE"


    def test_gleif_registration(self):
        data = GLEIF('549300MLUDYVRQOOXS22')

        assert data.registration.initial_registration_date\
            == datetime.datetime(2017, 4, 29, 2, 2, tzinfo=tzutc())
        assert data.registration.last_update_date\
            == datetime.datetime(2017, 4, 29, 2, 2, tzinfo=tzutc())
        assert data.registration.registration_status == "ISSUED"
        assert data.registration.next_renewal_date\
            == datetime.datetime(2018, 4, 27, 6, 32, tzinfo=tzutc())
        assert data.registration.managing_lou == "EVK05KS7XY1DEII3R011"
        assert data.registration.validation_sources == "FULLY_CORROBORATED"


class TestGLEIFRelationshipRecord(unittest.TestCase):

    def test_relationship_record(self):
        data = GLEIFParseRelationshipRecord(XML_DATA)

        assert data.raw.Relationship.StartNode.NodeID.text\
            == '097900BEJX0000001852'

from pygleif.gleif import GLEIF

LEI_DATA = '''[{
    "LEI": {"$": "549300MLUDYVRQOOXS22"},
    "Entity": {"LegalName": {"$": "Nordic Credit Rating AS"},
    "LegalAddress":{
        "Line1": {"$": "Haakon VII's gate 1"},
        "City": {"$": "Oslo"},
        "Region": {"$": "NO-03"},
        "Country": {"$": "NO"},
        "PostalCode": {"$": "0161"}},
    "HeadquartersAddress": {
        "Line1": {"$": "Haakon VII's gate 1"},
        "City": {"$": "Oslo"},
        "Region": {"$": "NO-03"},
        "Country": {"$": "NO"},
        "PostalCode": {"$": "0161"}},
      "BusinessRegisterEntityID": {"@register": "NO001"},
      "LegalJurisdiction": {"$": "NO"},
      "LegalForm": {"$": "AKSJESELSKAP"},
      "EntityStatus": {"$": "ACTIVE"}
    },
    "Registration": {
      "InitialRegistrationDate": {"$": "2017-04-29T02:02:39.295Z"},
      "LastUpdateDate": {"$": "2017-04-29T02:02:39.274Z"},
      "RegistrationStatus": {"$": "ISSUED"},
      "NextRenewalDate": {"$": "2018-04-27T06:32:56.863Z"},
      "ManagingLOU": {"$": "EVK05KS7XY1DEII3R011"},
      "ValidationSources": {"$": "FULLY_CORROBORATED"}
    }
  }
]'''


def test_gleif():
    data = GLEIF('549300MLUDYVRQOOXS22')

    assert data.lei == '549300MLUDYVRQOOXS22'


def test_gleif_entity():
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
    assert data.entity.legal_form == "AKSJESELSKAP"
    assert data.entity.entity_status == "ACTIVE"


def test_gleif_registration():
    data = GLEIF('549300MLUDYVRQOOXS22')

    assert data.registration.initial_registration_date\
        == "2017-04-29T02:02:39.295Z"
    assert data.registration.last_update_date\
        == "2017-04-29T02:02:39.274Z"
    assert data.registration.registration_status == "ISSUED"
    assert data.registration.next_renewal_date\
        == "2018-04-27T06:32:56.863Z"
    assert data.registration.managing_lou == "EVK05KS7XY1DEII3R011"
    assert data.registration.validation_sources == "FULLY_CORROBORATED"

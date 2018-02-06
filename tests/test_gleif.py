from pygleif.gleif import GLEIFEntity

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
      "InitialRegistrationDate": {
        "$": "2017-04-29T02:02:39.295Z"
      },
      "LastUpdateDate": {
        "$": "2017-04-29T02:02:39.274Z"
      },
      "RegistrationStatus": {
        "$": "ISSUED"
      },
      "NextRenewalDate": {
        "$": "2018-04-27T06:32:56.863Z"
      },
      "ManagingLOU": {
        "$": "EVK05KS7XY1DEII3R011"
      },
      "ValidationSources": {
        "$": "FULLY_CORROBORATED"
      }
    }
  }
]'''


def test_gleif():
    data = GLEIFEntity(LEI_DATA['Entity'])

    assert data.business_register_entity_id == 'NO001'

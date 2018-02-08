from pygleif.gleif import GLEIF, GLEIFParseRelationshipRecord

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


XML = '''<rr:Relationship>
            <rr:StartNode>
                <rr:NodeID>097900BEJX0000001852</rr:NodeID>
                <rr:NodeIDType>LEI</rr:NodeIDType>
            </rr:StartNode>
            <rr:EndNode>
                <rr:NodeID>315700FA4G1UK2XEQF20</rr:NodeID>
                <rr:NodeIDType>LEI</rr:NodeIDType>
            </rr:EndNode>
            <rr:RelationshipType>IS_DIRECTLY_CONSOLIDATED_BY</rr:RelationshipType>
            <rr:RelationshipPeriods>
                <rr:RelationshipPeriod>
                    <rr:StartDate>2017-12-14T00:00:00Z </rr:StartDate>
                    <rr:PeriodType>ACCOUNTING_PERIOD</rr:PeriodType>
                </rr:RelationshipPeriod>
                <rr:RelationshipPeriod>
                    <rr:StartDate>2006-09-22T00:00:00Z</rr:StartDate>
                    <rr:PeriodType>RELATIONSHIP_PERIOD</rr:PeriodType>
                </rr:RelationshipPeriod>
                <rr:RelationshipPeriod>
                    <rr:StartDate>2017-12-14T00:00:00Z</rr:StartDate>
                    <rr:PeriodType>DOCUMENT_FILING_PERIOD</rr:PeriodType>
                </rr:RelationshipPeriod>
            </rr:RelationshipPeriods>
            <rr:RelationshipStatus>ACTIVE</rr:RelationshipStatus>
            <rr:RelationshipQualifiers>
                <rr:RelationshipQualifier>
                    <rr:QualifierDimension>ACCOUNTING_STANDARD</rr:QualifierDimension>
                    <rr:QualifierCategory>IFRS</rr:QualifierCategory>
                </rr:RelationshipQualifier>
            </rr:RelationshipQualifiers>
            <rr:RelationshipQuantifiers>
                <rr:RelationshipQuantifier>
                    <rr:MeasurementMethod>ACCOUNTING_CONSOLIDATION</rr:MeasurementMethod>
                    <rr:QuantifierAmount>1.00</rr:QuantifierAmount>
                    <rr:QuantifierUnits>PERCENTAGE</rr:QuantifierUnits>
                </rr:RelationshipQuantifier>
            </rr:RelationshipQuantifiers>
        </rr:Relationship>
        <rr:Registration>
            <rr:InitialRegistrationDate>2017-12-14T00:00:00Z</rr:InitialRegistrationDate>
            <rr:LastUpdateDate>2017-12-14T00:00:00Z </rr:LastUpdateDate>
            <rr:RegistrationStatus>PUBLISHED</rr:RegistrationStatus>
            <rr:NextRenewalDate>2018-12-13T00:00:00Z</rr:NextRenewalDate>
            <rr:ManagingLOU>097900BEFH0000000217</rr:ManagingLOU>
            <rr:ValidationSources>FULLY_CORROBORATED</rr:ValidationSources>
            <rr:ValidationDocuments>OTHER_OFFICIAL_DOCUMENTS</rr:ValidationDocuments>
        </rr:Registration>'''


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
    assert data.entity.legal_name == "Nordic Credit Rating AS"
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


def test_relationship_record():
    data = GLEIFParseRelationshipRecord(XML)

    assert data.raw.Relationship.StartNode.NodeID.text\
           == '097900BEJX0000001852'

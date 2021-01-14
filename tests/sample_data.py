LEI_DATA = """[
  {
    "LEI": {
      "$": "097900BEJX0000001852"
    },
    "Entity": {
      "LegalName": {
        "@xml:lang": "sk",
        "$": "ZSE Energia, a.s."
      },
      "TransliteratedOtherEntityNames": {
        "TransliteratedOtherEntityName": [
          {
            "@type": "AUTO_ASCII_TRANSLITERATED_LEGAL_NAME",
            "$": "ZSE ENERGIA, AS"
          }
        ]
      },
      "LegalAddress": {
        "@xml:lang": "sk",
        "FirstAddressLine": {
          "$": "Čulenova 6"
        },
        "City": {
          "$": "Bratislava"
        },
        "Country": {
          "$": "SK"
        },
        "PostalCode": {
          "$": "81647"
        }
      },
      "HeadquartersAddress": {
        "@xml:lang": "sk",
        "FirstAddressLine": {
          "$": "Čulenova 6"
        },
        "City": {
          "$": "Bratislava"
        },
        "Country": {
          "$": "SK"
        },
        "PostalCode": {
          "$": "81647"
        }
      },
      "RegistrationAuthority": {
        "RegistrationAuthorityID": {
          "$": "RA000526"
        },
        "OtherRegistrationAuthorityID": {
          "$": "Okresný súd Bratislava I - 3978/B"
        },
        "RegistrationAuthorityEntityID": {
          "$": "36677281"
        }
      },
      "LegalJurisdiction": {
        "$": "SK"
      },
      "LegalForm": {
        "EntityLegalFormCode": {
          "$": "2EEG"
        }
      },
      "EntityStatus": {
        "$": "ACTIVE"
      },
      "NextVersion": null
    },
    "Registration": {
      "InitialRegistrationDate": {
        "$": "2014-09-23T00:00:00.00Z"
      },
      "LastUpdateDate": {
        "$": "2018-11-08T00:00:00.00Z"
      },
      "RegistrationStatus": {
        "$": "ISSUED"
      },
      "NextRenewalDate": {
        "$": "2019-12-13T00:00:00.00Z"
      },
      "ManagingLOU": {
        "$": "097900BEFH0000000217"
      },
      "ValidationSources": {
        "$": "FULLY_CORROBORATED"
      },
      "ValidationAuthority": {
        "ValidationAuthorityID": {
          "$": "RA000526"
        },
        "OtherValidationAuthorityID": {
          "$": "Okresný súd Bratislava I - 3978/B"
        },
        "ValidationAuthorityEntityID": {
          "$": "36677281"
        }
      },
      "NextVersion": null
    },
    "NextVersion": null
  }
]"""


XML_DATA = """<rr:Relationship>
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
        </rr:Registration>"""

URL_API = 'https://leilookup.gleif.org/api/v1/leirecords?lei='
URL_LEVEL2_CONCAT_FILES\
    = 'https://leidata.gleif.org/api/v1/concatenated-files/rr/%date%/zip'

ATTR_DOLLAR_SIGN = '$'

ATTR_LEI = 'LEI'

ATTR_ENTITY_BUSINESS_REGISTER_ENTITY_ID = 'BusinessRegisterEntityID'
ATTR_ENTITY_ENTITY_STATUS = 'EntityStatus'
ATTR_ENTITY_LEGAL_FORM = 'LegalForm'
ATTR_ENTITY_LEGAL_JURISDICTION = 'LegalJurisdiction'
ATTR_ENTITY_LEGAL_NAME = 'LegalName'

ATTR_INITIAL_REGISTRATION_DATE = 'InitialRegistrationDate'
ATTR_LAST_UPDATE_DATE = 'LastUpdateDate'
ATTR_MANAGING_LOU = 'ManagingLOU'
ATTR_NEXT_RENEWAL_DATE = 'NextRenewalDate'
ATTR_REGISTRATION_STATUS = 'RegistrationStatus'
ATTR_VALIDATION_SOURCES = 'ValidationSources'

ATTR_ADDRESS_TYPE_HQ = 'HeadquartersAddress'
ATTR_ADDRESS_TYPE_LEGAL = 'LegalAddress'
ATTR_ADDRESS_CITY = 'City'
ATTR_ADDRESS_COUNTRY = 'Country'
ATTR_ADDRESS_LINE1 = 'Line1'
ATTR_ADDRESS_POSTAL_CODE = 'PostalCode'
ATTR_ADDRESS_REGION = 'Region'

ATTR_REGISTER = '@register'
ATTR_REGISTRATION = 'Registration'
ATTR_ENTITY = 'Entity'

# The ELF codes are unique per country, not globally.
# Hence the nested dict.
LEGAL_FORMS = {
    'NO': {
        '326Y': 'Ansvarlig selskap',
        '3C7U': 'Stiftelse',
        '3L58': 'Kommunalt foretak',
        '4ZRR': 'Norskregistrert utenlandsk foretak',
        '50TD': 'Statsforetak',
        '5ZTZ': 'Fylkeskommunalt foretak',
        '8S9H': 'Gjensidig forsikringsselskap',
        '9DI1': 'Boligbyggelag',
        'AEV1': 'Partsrederi',
        'BJ65': 'Pensjonskasse',
        'CF5L': 'Ansvarlig selskap, delt ansvar',
        'DRPL': 'Europeisk økonomisk foretaksgruppe',
        'EXD7': 'Enkeltpersonforetak',
        'FSBD': 'Forening/lag/innretning (eller bare forening?)',
        'GYY6': 'Annen juridisk person',
        'IQGE': 'Allmennaksjeselskap',
        'K5P8': 'Samvirkeforetak',
        'LJJW': 'Verdipapirfond',
        'M9IQ': 'Kommandittselskap',
        'O0EU': 'Borettslag',
        'O7LB': 'Europeisk samvirkeforetak',
        'PB3V': 'Konkursbo',
        'Q0Q1': 'Selskap med begrenset ansvar',
        'R71C': 'Sparebank',
        'V06W': 'Europeisk selskap',
        'YI42': 'Aksjeselskap',
        'YTMC': 'Interkommunalt selskap',
        'ZQ0Q': 'Eierseksjonssameie'
    },
    'SE': {
        '1TN0': 'Ideell förening (som bedriver näringsverksamhet)',
        '2UAX': 'Trossamfund (som bedriver näringsverksamhet)',
        '381R': 'Medlemsbank',
        '54P7': 'Europabolag',
        '9YIP': 'Europakooperativ',
        'AZTO': 'Sambruksförening',
        'BEAY': 'Handelsbolag',
        'BYQJ': 'Bankaktiebolag',
        'C61P': 'Ekonomisk förening',
        'CX05': 'Kommanditbolag',
        'G04R': 'Sparbank',
        'M0Y0': 'Försäkringsförening',
        'O1QI': 'Ömsesidigt försäkringsbolag',
        'OJ9I': 'Försäkringsaktiebolag',
        'PDQ0': 'Kooperativ hyresrättsförening',
        'RLJO': 'Europeisk ekonomisk intressegruppering',
        'RYFP': 'Europeisk gruppering för territoriellt samarbete',
        'SSOM': 'Bostadsrättsförening',
        'WZDB': 'Bostadsförening',
        'XJHM': 'Aktiebolag'
    }
}

URL_API = "https://api.gleif.org/api/v1/lei-records/"
URL_LEVEL2_CONCAT_FILES = (
    "https://leidata.gleif.org/api/v1/concatenated-files/rr/%date%/zip"
)
URL_SEARCH = "https://api.gleif.org/api/v1/lei-records?filter%5Bfulltext%5D="
URL_DIRECT_CHILD = (
    "https://api.gleif.org/api/v1/lei-records/{}/direct-" "child-relationships"
)

ATTR_LEI = "lei"
ATTR_ENTITY_REGISTERED_AS = "registeredAs"
ATTR_JURISDICTION = "jurisdiction"
ATTR_ENTITY_LEGAL_NAME = "legalName"
ATTR_NAME = "name"
ATTR_STATUS = "status"
ATTR_ENTITY_LEGAL_FORM = "legalForm"
ATTR_ID = "id"


# RegistrationAuthorityEntityID
ATTR_ENTITY_ENTITY_STATUS = "EntityStatus"
ATTR_ENTITY_LEGAL_FORM_CODE = "EntityLegalFormCode"

ATTR_INITIAL_REGISTRATION_DATE = "initialRegistrationDate"
ATTR_LAST_UPDATE_DATE = "lastUpdateDate"
ATTR_MANAGING_LOU = "managingLou"
ATTR_NEXT_RENEWAL_DATE = "nextRenewalDate"
ATTR_VALIDATION_SOURCES = "corroborationLevel"

ATTR_ADDRESS_TYPE_HQ = "headquartersAddress"
ATTR_ADDRESS_TYPE_LEGAL = "legalAddress"
ATTR_ADDRESS_CITY = "city"
ATTR_ADDRESS_COUNTRY = "country"
ATTR_ADDRESS_LINE1 = "addressLines"
ATTR_ADDRESS_POSTAL_CODE = "postalCode"
ATTR_ADDRESS_REGION = "region"

ATTR_REGISTER = "@register"
ATTR_REGISTRATION = "registration"
ATTR_ENTITY = "entity"

# Allowed attributes for a record
ALLOW_ATTR_REGISTRATION_STATUS = ["ISSUED", "LAPSED"]

# The ELF codes are unique per country, not globally.
# Hence the nested dict.
LEGAL_FORMS = {
    "NO": {
        "326Y": "Ansvarlig selskap",
        "3C7U": "Stiftelse",
        "3L58": "Kommunalt foretak",
        "4ZRR": "Norskregistrert utenlandsk foretak",
        "50TD": "Statsforetak",
        "5ZTZ": "Fylkeskommunalt foretak",
        "8S9H": "Gjensidig forsikringsselskap",
        "9DI1": "Boligbyggelag",
        "AEV1": "Partsrederi",
        "BJ65": "Pensjonskasse",
        "CF5L": "Ansvarlig selskap, delt ansvar",
        "DRPL": "Europeisk økonomisk foretaksgruppe",
        "EXD7": "Enkeltpersonforetak",
        "FSBD": "Forening/lag/innretning (eller bare forening?)",
        "GYY6": "Annen juridisk person",
        "IQGE": "Allmennaksjeselskap",
        "K5P8": "Samvirkeforetak",
        "LJJW": "Verdipapirfond",
        "M9IQ": "Kommandittselskap",
        "O0EU": "Borettslag",
        "O7LB": "Europeisk samvirkeforetak",
        "PB3V": "Konkursbo",
        "Q0Q1": "Selskap med begrenset ansvar",
        "R71C": "Sparebank",
        "V06W": "Europeisk selskap",
        "YI42": "Aksjeselskap",
        "YTMC": "Interkommunalt selskap",
        "ZQ0Q": "Eierseksjonssameie",
    },
    "SE": {
        "1TN0": "Ideell förening (som bedriver näringsverksamhet)",
        "2UAX": "Trossamfund (som bedriver näringsverksamhet)",
        "381R": "Medlemsbank",
        "54P7": "Europabolag",
        "9YIP": "Europakooperativ",
        "AZTO": "Sambruksförening",
        "BEAY": "Handelsbolag",
        "BYQJ": "Bankaktiebolag",
        "C61P": "Ekonomisk förening",
        "CX05": "Kommanditbolag",
        "G04R": "Sparbank",
        "M0Y0": "Försäkringsförening",
        "O1QI": "Ömsesidigt försäkringsbolag",
        "OJ9I": "Försäkringsaktiebolag",
        "PDQ0": "Kooperativ hyresrättsförening",
        "RLJO": "Europeisk ekonomisk intressegruppering",
        "RYFP": "Europeisk gruppering för territoriellt samarbete",
        "SSOM": "Bostadsrättsförening",
        "WZDB": "Bostadsförening",
        "XJHM": "Aktiebolag",
    },
}

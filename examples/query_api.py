# Hack to allow relative import above top level package
import sys
import os
folder = os.path.dirname(os.path.abspath(__file__))  # noqa
sys.path.insert(0, os.path.normpath("%s/.." % folder))  # noqa
from pprint import pprint
from pygleif.gleif import GLEIF


gleif_data = GLEIF('549300MLUDYVRQOOXS23')

pprint((gleif_data.raw))
print(gleif_data.entity.legal_jurisdiction)
print(gleif_data.entity.legal_form)
print(gleif_data.entity.business_register_entity_id)

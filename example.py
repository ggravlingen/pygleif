from pygleif import Search, DirectChild
from pprint import pprint


gleif_search_data = Search('989932667')
gleif_child_data = DirectChild('549300ZQH0FIF1P0MX67')

pprint(gleif_child_data.valid_child_records)

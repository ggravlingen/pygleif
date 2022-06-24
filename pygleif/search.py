"""Search."""
import json
from urllib import request as url

from pygleif.const import ALLOW_ATTR_REGISTRATION_STATUS, URL_SEARCH


class Search:
    """Class to use the search form of the GLEIF web site."""

    def __init__(self, orgnr=None):
        """Init class."""
        # Allow searching using organisation number
        self.orgnr = orgnr

    @property
    def json_data(self):
        """Get raw data from the service."""
        return url.urlopen(URL_SEARCH + url.quote(self.orgnr))

    @property
    def raw(self):
        """Return parsed json."""
        return json.loads(self.json_data.read().decode("UTF-8"))

    @property
    def valid_record(self):
        """Loop through data to find a valid record. Return first valid."""
        for d in self.raw["data"]:

            # We're not very greedy here, but it seems some records have
            # lapsed even through the issuer is active
            if (
                d["attributes"]["registration"]["status"]
                in ALLOW_ATTR_REGISTRATION_STATUS
            ):
                return d["attributes"]

    @property
    def lei(self):
        """Return the LEI code."""
        try:
            return self.valid_record["lei"]
        except (IndexError, TypeError):
            return None

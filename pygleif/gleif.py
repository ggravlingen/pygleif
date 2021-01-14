from .const import (
    ATTR_LEI,
    URL_API,
)
import urllib.request as url
import json

from .entity import GLEIFEntity
from .registration import GLEIFRegistration


class GLEIF:
    """Parse JSON from GLEIF registry. Supports v1 of API."""

    def __init__(self, lei_code):
        self.lei_code = lei_code

    @property
    def json_data(self):
        return url.urlopen(URL_API + self.lei_code)

    @property
    def lei_exists(self):
        try:
            self.raw
            return False
        except IndexError:
            return True

    @property
    def raw(self):
        return json.loads(self.json_data.read().decode("UTF-8"))["data"]["attributes"]

    @property
    def lei(self):
        return self.raw[ATTR_LEI]

    @property
    def entity(self):
        return GLEIFEntity(self)

    @property
    def registration(self):
        return GLEIFRegistration(self)

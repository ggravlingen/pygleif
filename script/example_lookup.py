"""Example."""

import logging

from pygleif import PyGleif

logging.basicConfig(level=logging.INFO)


LOGGER = logging.getLogger(__name__)

for lei_code in [
    "549300MLUDYVRQOOXS22",
    "M312WZV08Y7LYUC71685",
    "IGJSJL3JD5P30I6NJZ34",
    "3C7474T6CDKPR9K6YT90",
]:
    gleif: PyGleif = PyGleif(lei_code)
    message = (
        f"LEI: {lei_code} | Registration date: "
        f"{gleif.response.data.attributes.registration.initial_registration_date} | "
        f"Name: {gleif.response.data.attributes.entity.legal_name.name}"
    )

    LOGGER.info(message)

"""Example."""

# Hack to allow relative import above top level package
import os
import sys

folder = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(f"{folder}/.."))
from pygleif import PyGleif  # noqa: E402

for entity in [
    "549300MLUDYVRQOOXS22",
    "M312WZV08Y7LYUC71685",
    "IGJSJL3JD5P30I6NJZ34",
    "3C7474T6CDKPR9K6YT90",
]:
    gleif: PyGleif = PyGleif(entity)
    print(  # noqa: T201
        gleif.response.data.attributes.registration.initial_registration_date
    )

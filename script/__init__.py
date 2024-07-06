"""Init."""
from pygleif import PyGleif

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

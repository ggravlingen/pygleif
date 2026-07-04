[![PyPI version](https://badge.fury.io/py/pygleif.svg)](https://badge.fury.io/py/pygleif)

This library uses Python to query the GLEIF.org's API.

#### Documentation

Full documentation, including the complete API reference, is available at
[pygleif.readthedocs.io](https://pygleif.readthedocs.io/).

> [!NOTE]
> `pygleif.v1` (`PyGleif`, `Search`) is deprecated. New code should use
> `pygleif.v2` (`GleifClient`), shown below.

#### Installing the library
`pip install pygleif`

#### Example: fetching data for a specific LEI:

```python
from pygleif import GleifClient

client = GleifClient()
response = client.get_lei_record("549300MLUDYVRQOOXS22")

# Print the name of the company with the LEI above
print(response.data.attributes.entity.legal_name.name)
# prints UK EQUITY FUND (OFFSHORE)
```

#### Example: search for a LEI using organisation number:

```python
from pygleif import GleifClient

client = GleifClient()
response = client.search_fulltext("5560142720")

# Print the LEI of the company with the LEI above
print(response.data[0].attributes.lei)

# prints 213800T8PC8Q4FYJZR07
```

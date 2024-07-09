[![PyPI version](https://badge.fury.io/py/pygleif.svg)](https://badge.fury.io/py/pygleif)

This library uses Python to query the GLEIF.org's API. Currently, the library supports:
- Fetching data for a specific API
- Searching for a LEI using an organisation number

The library is strictly typed using [`Pydantic`](https://github.com/pydantic/pydantic).

#### Installing the library
`pip install pygleif`

#### Example: fetching data for a specific LEI:

```python
from pygleif import PyGleif

gleif_response = PyGleif("549300MLUDYVRQOOXS22")

# Print the name of the company with the LEI above
print(gleif_response.response.data.attributes.entity.legal_name.name)
# prints UK EQUITY FUND (OFFSHORE)
```

#### Example: search for a LEI using organisation number:

```python
from pygleif import Search

gleif_response = Search("5560142720")

# Print the LEI of the company with the LEI above
print(response.data[0].attributes.lei)

# prints 213800T8PC8Q4FYJZR07
```

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

To install the latest in-development version from `main` (may be ahead of the
last PyPI release):
`pip install git+https://github.com/ggravlingen/pygleif.git@main`

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

#### Example: iterating over a full result set

`iter_search` follows the API's pagination for you (async: `aiter_search`):

```python
from pygleif import GleifClient

client = GleifClient(retries=2)
for record in client.iter_search(
    filters={"entity.legalAddress.country": "SE"},
    max_records=500,
):
    print(record.attributes.lei, record.attributes.entity.legal_name.name)
```

#### Command line

The package also installs a `pygleif` console command:

```console
$ pygleif get 5493001KJTIIGC8Y1R12
$ pygleif search "bank" --page-size 5
```

#### Async usage

Every `GleifClient` method has an `a`-prefixed async counterpart (e.g.
`search_fulltext` / `asearch_fulltext`), backed by `httpx2`:

```python
import asyncio

from pygleif import GleifClient


async def main() -> None:
    async with GleifClient() as client:
        response = await client.aget_lei_record("549300MLUDYVRQOOXS22")
        print(response.data.attributes.entity.legal_name.name)


asyncio.run(main())
```

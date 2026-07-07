# Usage

All v2 functionality is exposed through {class}`~pygleif.v2.client.GleifClient`,
importable as `pygleif.GleifClient` or `pygleif.v2.GleifClient`.

```python
from pygleif import GleifClient

client = GleifClient()
```

Every method has an async counterpart prefixed with `a` (e.g. `search` /
`asearch`, `get_lei` / `aget_lei`, `fields` / `afields`). Both share the same
[`httpx2`](https://github.com/pydantic/httpx2/)-based
{class}`~pygleif.v2.base.Transport`, so you can freely mix sync and async
usage against the same client. See "Async usage" below.

## Fetching a single LEI record

```python
response = client.get_lei_record("549300MLUDYVRQOOXS22")

print(response.data.attributes.entity.legal_name.name)
# prints UK EQUITY FUND (OFFSHORE)
```

For a normalized, generation-agnostic view (a {class}`~pygleif.compat.interfaces.RecordLike`),
use `get_lei` instead:

```python
record = client.get_lei("549300MLUDYVRQOOXS22")

print(record.lei, record.legal_name, record.country)
```

## Searching

```python
results = client.search_fulltext("Deutsche Bank")

for item in results.data:
    print(item.attributes.lei, item.attributes.entity.legal_name.name)
```

Look up records by BIC or ISIN:

```python
client.by_bic("DEUTDEFFXXX")
client.by_isin("DE0005140008")
```

Or run an arbitrary filtered search with sorting and pagination:

```python
from pygleif import SearchType

client.search(
    filters={SearchType.LEGAL_NAME: "Deutsche Bank"},
    sort="entity.legalName",
    page_number=1,
    page_size=15,
)
```

### Iterating over all results

`iter_search` (and its async counterpart `aiter_search`) follows the
response pagination for you and yields one
{class}`~pygleif.v2.api.models.LeiRecord` at a time:

```python
for record in client.iter_search(
    filters={"entity.legalAddress.country": "SE"},
    max_records=500,
):
    print(record.attributes.lei, record.attributes.entity.legal_name.name)
```

The API caps `page_size` at 200 (the iterator defaults to 100) and the
service is rate limited to 60 requests/minute, so prefer large page sizes
and `max_records` when you only need the first part of a big result set.

### Filter operators

Filter values are passed through verbatim, so the API's documented search
operators work directly:

```python
client.search(filters={"entity.legalAddress.country": "!GB"})       # NOT
client.search(filters={"entity.legalName": "facebook,twitter"})     # IN
client.search(filters={"entity.expiration.date": "19900101..19950101"})  # range
client.search(filters={"entity.expiration.date": ">=20190723"})     # comparison
```

Multiple filters combine as a logical AND. To find relationship data via
search, use the `owns` ("who owns X?" — returns parents) and `ownedBy`
("who is owned by X?" — returns children) filters:

```python
client.search(filters={"owns": "549300MLUDYVRQOOXS22"})
client.search(filters={"ownedBy": "549300MLUDYVRQOOXS22"})
```

## Level 2 relationship data

Fetch parent and child LEI records through the dedicated relationship
endpoints:

```python
client.direct_parent("549300MLUDYVRQOOXS22")      # single LEI record
client.ultimate_parent("549300MLUDYVRQOOXS22")    # single LEI record
client.direct_children("549300MLUDYVRQOOXS22")    # paginated LEI records
client.ultimate_children("549300MLUDYVRQOOXS22")  # paginated LEI records
```

The relationship records themselves (reporting periods, corroboration,
relationship status) are available too:

```python
client.direct_parent_relationship("549300MLUDYVRQOOXS22")
client.ultimate_parent_relationship("549300MLUDYVRQOOXS22")
client.direct_child_relationships("549300MLUDYVRQOOXS22")
client.ultimate_child_relationships("549300MLUDYVRQOOXS22")
```

When an entity reports no parent, the parent lookups raise
{class}`~pygleif.v2.error.PyGLEIFNotFoundError` and the reason is available
as a reporting exception:

```python
from pygleif.v2.error import PyGLEIFNotFoundError

try:
    client.direct_parent("9845001B2AD43E664E58")
except PyGLEIFNotFoundError:
    exception = client.direct_parent_reporting_exception("9845001B2AD43E664E58")
    print(exception.data.attributes.reason)  # e.g. NON_CONSOLIDATING
```

`ultimate_parent_reporting_exception` works the same way for the ultimate
parent.

## Related records

```python
client.lei_issuer("549300MLUDYVRQOOXS22")         # the issuer (LOU) record
client.managing_lou("549300MLUDYVRQOOXS22")       # the LOU's own LEI record
client.associated_entity("549300MLUDYVRQOOXS22")  # fund manager, if any
client.successor_entity("549300MLUDYVRQOOXS22")   # successor, if any
```

## ISIN mappings

```python
client.isins("549300MLUDYVRQOOXS22")
```

## Field modifications (record history)

Retrieve the historical changes of an LEI record, optionally filtered:

```python
client.field_modifications("549300MLUDYVRQOOXS22")
client.field_modifications(
    "549300MLUDYVRQOOXS22",
    modification_type="UPDATE",
    record_type="RR",
    page_size=50,
)
```

## Completions and field metadata

```python
client.fuzzy_completions("Deutche Bank")  # approximate matches, typo-tolerant
client.autocompletions("Deutsche")        # suggested search terms
client.fields()                           # technical metadata about API fields
client.get_field("LEIREC_FULLTEXT")       # metadata for one field
```

Both completion endpoints accept a `field` argument (`fulltext`,
`entity.legalName`, `owns`, `ownedBy` — see
{class}`~pygleif.v2.client.SearchType`).

## LEI and vLEI issuers

```python
client.lei_issuers()                                  # accredited LOUs
client.get_lei_issuer("5299000J2N45DDNE4Y28")         # one LOU by its LEI
client.lei_issuer_jurisdictions("5299000J2N45DDNE4Y28")
client.vlei_issuers()                                 # qualified vLEI issuers
client.get_vlei_issuer("549300O897ZC5H7CY412")
```

## Reference data

Each code list has a paginated list method and a `get_*` detail lookup:

```python
client.countries()                                # ISO 3166 country codes
client.get_country("US")
client.entity_legal_forms()                       # ISO 20275 ELF codes
client.get_entity_legal_form("10UR")
client.official_organizational_roles()            # ISO 5009 OOR codes
client.get_official_organizational_role("01D0O4")
client.jurisdictions()                            # legal jurisdictions
client.get_jurisdiction("US-DE")
client.regions()                                  # ISO 3166 sub-regions
client.get_region("AD-07")
client.registration_authorities()                 # GLEIF RA code list
client.get_registration_authority("RA000001")
client.registration_agents()
client.get_registration_agent("5d10d4dc929ab6.72309473")
```

## Exporting LEI records

Download up to 5000 LEI records as a file (`csv`, `xlsx` or `json`),
narrowed by the same filters as `search`:

```python
from pygleif import ExportFormat

payload = client.export_lei_records(
    export_format=ExportFormat.CSV,
    filters={"entity.legalAddress.country": "SE"},
)
with open("lei-records.csv", "wb") as handle:
    handle.write(payload)
```

## Health check

```python
if not client.healthcheck():
    ...  # API is unreachable
```

## Async usage

Every method described above has an `a`-prefixed async counterpart that
takes the same arguments and returns the same response model:

```python
import asyncio

from pygleif import GleifClient


async def main() -> None:
    async with GleifClient() as client:
        record = await client.aget_lei("549300MLUDYVRQOOXS22")
        results = await client.asearch_fulltext("Deutsche Bank")
        print(record.legal_name, len(results.data))


asyncio.run(main())
```

Using `async with` (or `with` for sync-only code) ensures the underlying
`httpx2` connection pool is closed when you're done. Without a context
manager, call `client.close()` or `await client.aclose()` explicitly:

```python
client = GleifClient()
try:
    client.search_fulltext("Deutsche Bank")
finally:
    client.close()
```

## Configuring the client

The request timeout (seconds) and the number of retries for transient
failures (HTTP 429 and 5xx) are configurable; retries honor the server's
`Retry-After` header with the delay capped at 30 seconds:

```python
client = GleifClient(timeout=30, retries=2)
```

For full control (e.g. a custom base URL), build the
{class}`~pygleif.v2.base.Transport` yourself; the keyword arguments above
are ignored when a transport is injected:

```python
from pygleif import GleifClient, Transport

client = GleifClient(transport=Transport(timeout=30, retries=2))
```

## Error handling

All v2 errors derive from {class}`~pygleif.v2.error.PyGLEIFError` and are
importable from `pygleif.v2`. API failures carry their request context:
`status_code` (`None` for network-level failures), the requested `url`, a
`body` excerpt, and — for rate limits — the server-suggested `retry_after`
in seconds:

```python
from pygleif.v2 import PyGLEIFApiError, PyGLEIFNotFoundError, PyGLEIFRateLimitError

try:
    client.get_lei_record("does-not-exist")
except PyGLEIFNotFoundError:
    ...  # HTTP 404
except PyGLEIFRateLimitError as exc:
    ...  # HTTP 429 - 60 requests/minute limit exceeded
    print(exc.retry_after)
except PyGLEIFApiError as exc:
    print(exc.status_code, exc.url, exc.body)
```

## Command line

The package installs a `pygleif` console command (also available as
`python -m pygleif`) built on the v2 client:

```console
$ pygleif get 5493001KJTIIGC8Y1R12
$ pygleif --summary get 5493001KJTIIGC8Y1R12
$ pygleif search "bank" --field fulltext --page-size 5
$ pygleif owners 315700WQBDF1ZVVE0T64
$ pygleif isins 5493001KJTIIGC8Y1R12
```

Run `pygleif --help` for the full command list.

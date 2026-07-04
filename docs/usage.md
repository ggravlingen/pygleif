# Usage

All v2 functionality is exposed through {class}`~pygleif.v2.client.GleifClient`,
importable as `pygleif.GleifClient` or `pygleif.v2.GleifClient`.

```python
from pygleif import GleifClient

client = GleifClient()
```

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

## Relationships

```python
client.owners("549300MLUDYVRQOOXS22")    # parent entities that own this LEI
client.children("549300MLUDYVRQOOXS22")  # child entities owned by this LEI
```

## ISIN mappings

```python
client.isins("549300MLUDYVRQOOXS22")
```

## Fuzzy completions and field metadata

```python
client.fuzzy_completions("Deutche Bank")  # tolerant of typos
client.fields()                           # technical metadata about API fields
```

## Health check

```python
if not client.healthcheck():
    ...  # API is unreachable
```

## Error handling

All v2 errors derive from {class}`~pygleif.v2.error.PyGLEIFError`:

```python
from pygleif.v2.error import PyGLEIFNotFoundError, PyGLEIFRateLimitError

try:
    client.get_lei_record("does-not-exist")
except PyGLEIFNotFoundError:
    ...  # HTTP 404
except PyGLEIFRateLimitError:
    ...  # HTTP 429 - 60 requests/minute limit exceeded
```

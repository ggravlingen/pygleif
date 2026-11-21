# Best practices and upgrade guide

This page states how pygleif v2 is meant to be used today. It is written as
short rules ("do X, not Y") so it works both for people and as context for an
AI coding assistant that is upgrading or writing code against this library.
It ships inside the installed package as `pygleif/AGENTS.md`; print it with
`pygleif guide`.

**The one thing to remember:** GLEIF allows 60 requests per minute, and the
client paces itself to that. Wall-clock time is therefore almost entirely
*number of requests*. Prefer calls that fetch many records per request.

## Imports

Use the v2 client. `PyGleif` and `Search` are the frozen, deprecated v1 API,
kept only so old code keeps working; do not add new uses.

```python
from pygleif import GleifClient  # v2: use this
# from pygleif import PyGleif, Search   # v1: deprecated
```

## Migrating from v1

| v1 (deprecated)                  | v2 equivalent                                            |
| -------------------------------- | -------------------------------------------------------- |
| `PyGleif(lei).response`          | `client.get_lei_record(lei)`                             |
| `Search(text).response`          | `client.search_fulltext(text)`                           |
| `Search(text, SearchType.LEGAL_NAME)` | `client.search(filters={"entity.legalName": text})` |
| hand-written paging loop         | `client.iter_search(filters=...)` / `aiter_search`       |

v1 and v2 models are different classes. Do not mix them; migrate a code path
completely.

## Create one client and close it

One `GleifClient` owns one connection pool and one rate-limit quota. Reuse it
and close it with a context manager.

% notest
```python
# Good
with GleifClient() as client:
    ...

# Bad: a new client (new pool, new quota) per call
GleifClient().get_lei_record(lei)
```

% notest
```python
async with GleifClient() as client:
    record = await client.aget_lei_record("9845001B2AD43E664E58")
```

## Spend as few requests as possible

### Many LEIs: batch them

`get_lei_records` sends up to 100 LEIs per request using the `filter[lei]`
any-of operator: N LEIs cost `ceil(N / 100)` requests instead of N.

```python
records = client.get_lei_records(leis)  # 1 request for <= 100 LEIs
by_lei = {record.id: record for record in records}
```

% notest
```python
# Bad: one request per LEI (about a minute for 60 LEIs)
records = [client.get_lei_record(lei).data for lei in leis]
```

LEIs that do not exist are absent from the result, and result order is the
API's, so index by `record.id` as above. Duplicates and blanks are dropped.

### Many results: iterate, with full-size pages

`iter_search` and `aiter_search` follow pagination for you and default to the
maximum page size (200). Do not write your own paging loop, and do not lower
`page_size` for bulk work.

```python
for record in client.iter_search(
    filters={"entity.legalAddress.country": "SE"}, max_records=500
):
    print(record.attributes.entity.legal_name.name)
```

### Very large result sets: export

For up to 5,000 records, one `export_lei_records` call beats dozens of pages.

```python
data = client.export_lei_records(
    export_format="csv", filters={"entity.legalAddress.country": "SE"}
)
```

## Leave rate limiting and retries to the client

The defaults (`requests_per_minute=60`, `retries=3`) are right for almost
everyone. Retries honour `Retry-After` and use jittered backoff.

- Do not wrap calls in your own `time.sleep` or retry loop.
- Only set `requests_per_minute=None` if something else already enforces the
  quota across all your processes.
- A `PyGLEIFRateLimitError` reaching your code means retries were exhausted;
  `error.retry_after` says how long the server asked you to wait.

## Async

Use the `a`-prefixed methods (`asearch`, `aget_lei_records`, `aiter_search`)
and share one client across tasks, so they share one rate-limit quota.
`aiter_search` requests the next page in the background while you process the
current one.

```python
import asyncio


async def names() -> list[str | None]:
    return [
        record.attributes.entity.legal_name.name
        async for record in client.aiter_search(
            filters={"fulltext": "bank"},
            max_records=50,
        )
    ]


print(asyncio.run(names()))
```

Breaking out of an `async for` early cancels the background request; wrap the
iterator in `contextlib.aclosing` if you want that to happen deterministically.

## Handle errors by type

Catch the pygleif hierarchy, not `httpx2` or pydantic exceptions.

| Exception                | Meaning                                                    |
| ------------------------ | ---------------------------------------------------------- |
| `PyGLEIFNotFoundError`   | 404, e.g. no parent reported                               |
| `PyGLEIFRateLimitError`  | 429 after retries; has `.retry_after`                      |
| `PyGLEIFResponseError`   | body was not JSON, or did not match the expected schema    |
| `PyGLEIFApiError`        | any other HTTP or network failure (parent of the above)    |
| `PyGLEIFError`           | catch-all base class                                       |

A missing parent is normal data, not a bug: fall back to the reporting
exception, which says *why* there is none.

```python
from pygleif.v2 import PyGLEIFNotFoundError

lei = "9845001B2AD43E664E58"
try:
    parent = client.direct_parent(lei)
except PyGLEIFNotFoundError:
    exception = client.direct_parent_reporting_exception(lei)
```

## Filters and search operators

Filter values are passed through to the API verbatim, so use its operators
instead of filtering client-side: `!abc` (not), `abc,def` (any of),
`20240101..20241231` (range), `>=`, `>`, `<=`, `<`.

```python
client.search(
    filters={"entity.status": "ACTIVE", "registration.lastUpdateDate": ">=20240101"}
)
```

## Testing your code

Never call the live API from unit tests. Either inject a fake that satisfies
`TransportLike` (`get`, `aget`, `get_raw`, `aget_raw`, `close`, `aclose`;
`get_json_bytes`/`aget_json_bytes` are optional and used when present), or run
the real `Transport` against `httpx2.MockTransport`.

```python
import httpx2
from pygleif.v2 import GleifClient, Transport


def handler(request: httpx2.Request) -> httpx2.Response:
    return httpx2.Response(200, json={"meta": {}, "data": []})


transport = Transport(
    requests_per_minute=None, httpx_transport=httpx2.MockTransport(handler)
)
assert GleifClient(transport=transport).search_fulltext("x").data == []
```

## Anti-patterns checklist

- A new `GleifClient` per request.
- `get_lei_record` (or any `get_*`) inside a loop over many LEIs.
- Hand-written paging, or `page_size` far below 200 for bulk reads.
- `time.sleep` / custom retry around client calls.
- Catching `Exception`, `httpx2.HTTPError` or `pydantic.ValidationError`
  instead of `PyGLEIFError` subclasses.
- Using `PyGleif`/`Search` or mixing v1 and v2 models.
- Hitting the live API in unit tests.

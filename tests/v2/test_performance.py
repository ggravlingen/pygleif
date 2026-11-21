"""Tests for the v2 request-count and parsing optimizations (offline)."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx2
import pytest

from pygleif.v2 import GleifClient, Transport
from pygleif.v2.base import _user_agent
from pygleif.v2.client import LEI_BATCH_SIZE, MAX_PAGE_SIZE
from pygleif.v2.error import PyGLEIFResponseError

from .conftest import FakeTransport, PagedFakeTransport, load_fixture
from .test_client import _page_payload

ISSUED = load_fixture("9845001B2AD43E664E58_issued")["data"]


def _record(lei: str) -> dict[str, Any]:
    """Return a fixture record re-labelled with ``lei``."""
    record = json.loads(json.dumps(ISSUED))
    record["id"] = lei
    record["attributes"]["lei"] = lei
    return record


def _lei(n: int) -> str:
    """Return a distinct 20-character pseudo LEI."""
    return f"{n:020d}"


class _DictOnlyTransport(FakeTransport):
    """A transport exposing only the minimal ``get``/``aget`` surface."""

    get_json_bytes = None  # type: ignore[assignment]
    aget_json_bytes = None  # type: ignore[assignment]


# -- batch lookup ---------------------------------------------------------
def test_get_lei_records_batches_requests() -> None:
    """N LEIs should cost ceil(N / LEI_BATCH_SIZE) requests, not N."""
    leis = [_lei(n) for n in range(LEI_BATCH_SIZE * 2 + 5)]
    pages = [
        _page_payload(
            [_record(lei) for lei in chunk],
            current_page=1,
            last_page=1,
            total=len(chunk),
        )
        for chunk in (
            leis[:LEI_BATCH_SIZE],
            leis[LEI_BATCH_SIZE : 2 * LEI_BATCH_SIZE],
            leis[2 * LEI_BATCH_SIZE :],
        )
    ]
    transport = PagedFakeTransport({"lei-records": pages})
    client = GleifClient(transport=transport)

    records = client.get_lei_records(leis)

    assert [r.id for r in records] == leis
    assert len(transport.calls) == 3
    first_params = transport.calls[0][1]
    assert first_params is not None
    assert first_params["filter[lei]"] == ",".join(leis[:LEI_BATCH_SIZE])
    assert first_params["page[size]"] == LEI_BATCH_SIZE
    last_params = transport.calls[2][1]
    assert last_params is not None
    assert last_params["page[size]"] == 5


def test_get_lei_records_dedupes_and_skips_blanks() -> None:
    """Duplicates and blank entries must not inflate the request."""
    page = _page_payload([_record("A" * 20)], current_page=1, last_page=1, total=1)
    transport = PagedFakeTransport({"lei-records": [page]})
    client = GleifClient(transport=transport)

    client.get_lei_records(["A" * 20, " ", "A" * 20, ""])

    params = transport.calls[0][1]
    assert params is not None
    assert params["filter[lei]"] == "A" * 20
    assert params["page[size]"] == 1


def test_get_lei_records_empty_makes_no_request() -> None:
    """No LEIs means no HTTP call."""
    transport = PagedFakeTransport({"lei-records": []})
    assert GleifClient(transport=transport).get_lei_records([]) == []
    assert transport.calls == []


def test_aget_lei_records_matches_sync() -> None:
    """The async batch lookup should return the same records."""
    leis = [_lei(1), _lei(2)]
    page = _page_payload(
        [_record(lei) for lei in leis],
        current_page=1,
        last_page=1,
        total=2,
    )
    client = GleifClient(transport=PagedFakeTransport({"lei-records": [page]}))
    records = asyncio.run(client.aget_lei_records(leis))
    assert [r.id for r in records] == leis


# -- default page size ----------------------------------------------------
def test_iter_search_defaults_to_max_page_size() -> None:
    """Bulk iteration should ask for the largest page the API allows."""
    page = _page_payload([_record(_lei(1))], current_page=1, last_page=1, total=1)
    transport = PagedFakeTransport({"lei-records": [page]})
    list(GleifClient(transport=transport).iter_search())
    params = transport.calls[0][1]
    assert params is not None
    assert params["page[size]"] == MAX_PAGE_SIZE


# -- single-pass JSON validation -------------------------------------------
def test_bytes_path_matches_dict_path() -> None:
    """Validating raw bytes and a decoded dict must yield equal models."""
    lei = "9845001B2AD43E664E58"
    payload = load_fixture(f"{lei}_issued")
    via_bytes = GleifClient(
        transport=FakeTransport({f"lei-records/{lei}": payload}),
    ).get_lei_record(lei)
    via_dict = GleifClient(
        transport=_DictOnlyTransport({f"lei-records/{lei}": payload}),
    ).get_lei_record(lei)
    assert via_bytes == via_dict


def test_invalid_json_bytes_raise_response_error() -> None:
    """A non-JSON body on the bytes path is still a PyGLEIFResponseError."""

    class _BadBody(FakeTransport):
        def get_json_bytes(self, path: str, params: Any = None) -> bytes:  # noqa: ARG002
            return b"<html>gateway</html>"

    with pytest.raises(PyGLEIFResponseError):
        GleifClient(transport=_BadBody()).get_lei_record("X")


def test_schema_mismatch_on_bytes_path_raises_response_error() -> None:
    """Schema drift on the bytes path is wrapped like the dict path."""
    client = GleifClient(transport=FakeTransport({"lei-records/X": {"data": {}}}))
    with pytest.raises(PyGLEIFResponseError):
        client.get_lei_record("X")


def test_real_transport_exposes_undecoded_bytes() -> None:
    """Transport.get_json_bytes should return the raw body, JSON Accept set."""
    seen: dict[str, str] = {}

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen["accept"] = request.headers["Accept"]
        return httpx2.Response(200, content=b'{"ok": true}')

    transport = Transport(
        requests_per_minute=None,
        httpx_transport=httpx2.MockTransport(handler),
        httpx_async_transport=httpx2.MockTransport(handler),
    )
    assert transport.get_json_bytes("x") == b'{"ok": true}'
    assert asyncio.run(transport.aget_json_bytes("x")) == b'{"ok": true}'
    assert seen["accept"] == "application/vnd.api+json"


def test_user_agent_is_cached() -> None:
    """The metadata lookup should happen once, not per client."""
    assert _user_agent() is _user_agent()


# -- async prefetch --------------------------------------------------------
class _TrackingTransport(FakeTransport):
    """Async transport recording which pages were requested and cancelled."""

    def __init__(self, last_page: int) -> None:
        super().__init__()
        self.last_page = last_page
        self.requested: list[int] = []
        self.cancelled: list[int] = []

    async def aget_json_bytes(self, path: str, params: Any = None) -> bytes:  # noqa: ARG002
        number = params["page[number]"]
        self.requested.append(number)
        if number > 1:
            try:
                await asyncio.sleep(0.05)
            except asyncio.CancelledError:
                self.cancelled.append(number)
                raise
        page = _page_payload(
            [_record(_lei(number * 10 + i)) for i in range(2)],
            current_page=number,
            last_page=self.last_page,
            total=self.last_page * 2,
        )
        return json.dumps(page).encode()


def test_aiter_search_prefetches_next_page() -> None:
    """Page n+1 is requested while page n's records are being consumed."""
    transport = _TrackingTransport(last_page=3)
    client = GleifClient(transport=transport)

    async def run() -> list[str]:
        seen: list[str] = []
        async for record in client.aiter_search(page_size=2):
            if len(seen) == 0:
                # Still on page 1's first record: page 2 must already be in flight.
                await asyncio.sleep(0)
                assert 2 in transport.requested
            seen.append(record.id)
        return seen

    assert len(asyncio.run(run())) == 6
    assert transport.requested == [1, 2, 3]


def test_aiter_search_cancels_prefetch_on_early_exit() -> None:
    """Breaking out early must cancel the in-flight prefetch."""
    transport = _TrackingTransport(last_page=5)
    client = GleifClient(transport=transport)

    async def run() -> None:
        iterator = client.aiter_search(page_size=2)
        async for _ in iterator:
            break
        await asyncio.sleep(0.01)  # let the prefetch start
        await iterator.aclose()

    asyncio.run(run())
    assert transport.requested == [1, 2]
    assert transport.cancelled == [2]


def test_aiter_search_skips_prefetch_when_max_records_satisfied() -> None:
    """No wasted request when the first page already covers max_records."""
    transport = _TrackingTransport(last_page=5)
    client = GleifClient(transport=transport)

    async def run() -> int:
        return len(
            [r async for r in client.aiter_search(page_size=2, max_records=2)],
        )

    assert asyncio.run(run()) == 2
    assert transport.requested == [1]

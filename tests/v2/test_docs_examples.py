"""Run the Python examples in pygleif/AGENTS.md so the guide can't drift.

Blocks run against an offline fake transport with ``client`` and ``leis``
predefined. A block preceded by a ``% notest`` line (a MyST comment, invisible
in the rendered docs) is skipped: those show construction or anti-patterns.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

import pytest

from pygleif.v2 import GleifClient
from pygleif.v2.error import PyGLEIFNotFoundError

from .conftest import FakeTransport, load_fixture
from .test_client import _page_payload

GUIDE = Path(__file__).parents[2] / "pygleif" / "AGENTS.md"
LEI = "9845001B2AD43E664E58"
BLOCK = re.compile(r"(?P<marker>^% notest\n)?```python\n(?P<code>.*?)```", re.M | re.S)


def _blocks() -> list[tuple[int, str]]:
    """Return (index, code) for every runnable python block in the guide."""
    return [
        (index, match["code"])
        for index, match in enumerate(BLOCK.finditer(GUIDE.read_text()))
        if not match["marker"]
    ]


class _GuideTransport(FakeTransport):
    """Canned data for the guide's examples; a missing parent is a 404."""

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if path.endswith("/direct-parent"):
            raise PyGLEIFNotFoundError("no parent", status_code=404, url=path)
        return super().get(path, params)


def _namespace() -> dict[str, Any]:
    record = load_fixture(f"{LEI}_issued")
    page = _page_payload(
        [record["data"]],
        current_page=1,
        last_page=1,
        total=1,
    )
    exception = {
        "data": {"type": "reporting-exceptions", "id": "x", "attributes": {}},
    }
    transport = _GuideTransport(
        {
            "lei-records": page,
            f"lei-records/{LEI}": record,
            f"lei-records/{LEI}/direct-parent-reporting-exception": exception,
        },
        {"lei-records.csv": b"lei\n"},
    )
    return {"client": GleifClient(transport=transport), "leis": [LEI] * 3}


def test_guide_has_runnable_examples() -> None:
    """Guard against the extraction regex silently matching nothing."""
    assert len(_blocks()) >= 8  # noqa: PLR2004


@pytest.mark.parametrize(("index", "code"), _blocks())
def test_guide_example_runs(index: int, code: str) -> None:
    """Each documented example must execute against the current API."""
    exec(compile(code, f"AGENTS.md[block {index}]", "exec"), _namespace())  # noqa: S102

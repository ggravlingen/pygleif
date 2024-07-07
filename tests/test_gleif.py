"""Tests."""

from typing import Any
import pytest

from pygleif import PyGleif
import json
from unittest.mock import patch, PropertyMock
from collections.abc import Generator


def load_mock_data(file_name: str) -> dict[Any, Any]:
    """Load mock data from file."""
    with open(f"tests/fixtures/{file_name}.json") as file:
        return json.load(file)


@pytest.fixture
def fixture_response(request) -> Generator[Any, Any, Any]:
    """Mock data for the security service endpoint."""
    with patch(
        "pygleif.base.PyGleifBase.json_response", new_callable=PropertyMock
    ) as mock_response:
        mock_response.return_value = load_mock_data(request.param)
        yield request.param


@pytest.mark.parametrize(
    "fixture_response",
    ["9845001B2AD43E664E58_issued", "549300LBI3LRIZ2V8V66_lapsed"],
    indirect=True,
)
def test_pygleif(fixture_response) -> None:
    """Test Pygleif-class."""
    lei = fixture_response.split("_")[0]
    data = PyGleif(lei)
    assert data.response.data.attributes.lei == lei

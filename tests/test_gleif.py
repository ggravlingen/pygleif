"""Tests."""

from typing import Any
import pytest

from pygleif import PyGleif
import json
from unittest.mock import patch
from collections.abc import Generator


def load_mock_data(file_name: str) -> dict[Any, Any]:
    """Load mock data from file."""
    with open(f"tests/fixtures/{file_name}.json") as file:
        return json.load(file)


@pytest.fixture
def fixture_response_a() -> Generator[Any, Any, Any]:
    """Mock data for the security service endpoint."""
    with patch(
        "pygleif.gleif.load_json",
    ) as mock_response:
        mock_response.return_value = load_mock_data("9845001B2AD43E664E58")
        yield


def test_pygleif(fixture_response_a) -> None:
    """Test Pygleif-class."""
    data = PyGleif("9845001B2AD43E664E58")
    assert data.response.data.attributes.lei == "9845001B2AD43E664E58"

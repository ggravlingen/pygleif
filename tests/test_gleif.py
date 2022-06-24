"""Tests."""
import pytest

from pygleif import PyGleif


@pytest.fixture(scope="module")
def gleif_fixture_1() -> PyGleif:
    """Fixture."""
    return PyGleif("549300MLUDYVRQOOXS22")


def test_lei(gleif_fixture_1: PyGleif):
    """Test LEI attribute."""
    assert gleif_fixture_1.response.data.attributes.lei, "549300MLUDYVRQOOXS22"


def test_id(gleif_fixture_1: PyGleif):
    """Test ID attribute."""
    assert gleif_fixture_1.response.data.id, "549300MLUDYVRQOOXS22"

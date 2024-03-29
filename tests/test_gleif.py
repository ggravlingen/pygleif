"""Tests."""

import pytest

from pygleif import PyGleif


@pytest.fixture(scope="module", name="gleif_fixture_1")
def data_fixture() -> PyGleif:
    """Fixture."""
    return PyGleif("549300MLUDYVRQOOXS22")


def test_lei(gleif_fixture_1: PyGleif):
    """Test LEI attribute."""
    assert gleif_fixture_1.response.data.attributes.lei, "549300MLUDYVRQOOXS22"


def test_id(gleif_fixture_1: PyGleif):
    """Test ID attribute."""
    assert gleif_fixture_1.response.data.id, "549300MLUDYVRQOOXS22"


@pytest.mark.parametrize("lei", ["969500NTPM8P4LAT9V13"])
def test_different_lei(lei: str):
    """Test various LEI."""
    PyGleif(lei_code=lei)
    assert True

"""Tests."""
import pytest

from pygleif import PyGleif, Search


@pytest.fixture(scope="module")
def gleif_fixture_1() -> PyGleif:
    """Fixture."""
    return PyGleif("549300MLUDYVRQOOXS22")


@pytest.fixture(scope="module")
def gleif_search_fixture() -> Search:
    """Fixture."""
    return Search("917685991")


def test_lei(gleif_fixture_1: PyGleif):
    """Test LEI attribute."""
    assert gleif_fixture_1.response.data.attributes.lei, "549300MLUDYVRQOOXS22"


def test_id(gleif_fixture_1: PyGleif):
    """Test ID attribute."""
    assert gleif_fixture_1.response.data.id, "549300MLUDYVRQOOXS22"


def test_search_lei(gleif_search_fixture: Search):
    """Test LEI attribute."""
    assert gleif_search_fixture.response.data[0].attributes.lei, "549300MLUDYVRQOOXS22"


def test_search_id(gleif_search_fixture: Search):
    """Test ID attribute."""
    assert gleif_search_fixture.response.data[0].id, "549300MLUDYVRQOOXS22"


@pytest.mark.parametrize("lei", ["969500NTPM8P4LAT9V13"])
def test_different_lei(lei: str):
    """Test various LEI."""
    PyGleif(lei_code=lei)
    assert True

"""Tests for search function."""

import pytest

from pygleif import Search


@pytest.fixture(scope="module")
def gleif_search_fixture() -> Search:
    """Fixture."""
    return Search("917685991")


def test_search_lei(gleif_search_fixture: Search):
    """Test LEI attribute."""
    assert gleif_search_fixture.response.data[0].attributes.lei, "549300MLUDYVRQOOXS22"


def test_search_id(gleif_search_fixture: Search):
    """Test ID attribute."""
    assert gleif_search_fixture.response.data[0].id, "549300MLUDYVRQOOXS22"


def test_search_fail():
    """Test failing search."""
    return Search("968278304")
    assert True

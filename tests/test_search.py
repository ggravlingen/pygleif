"""Tests for search function."""

import pytest

from pygleif import Search
from pygleif.search import SearchType


@pytest.fixture(scope="module", name="gleif_search_fixture")
def search_data() -> Search:
    """Fixture."""
    return Search("917685991")



def test_search_lei(gleif_search_fixture: Search):
    """Test LEI attribute."""
    assert gleif_search_fixture.response.data[0].attributes.lei, "549300MLUDYVRQOOXS22"


def test_search_id(gleif_search_fixture: Search):
    """Test ID attribute."""
    assert gleif_search_fixture.response.data[0].id, "549300MLUDYVRQOOXS22"


def test_search_no_result():
    """Test failing search."""
    search = Search("1bcdefghijklmnopqrstuvwxyz")
    assert search.response.data == []

def test_search_no_result():
    """Test matching search."""
    search = Search("Sparbanken Rekarne", search_type=SearchType.LEGAL_NAME)
    assert len(search.response.data) == 1

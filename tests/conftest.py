"""Shared pytest fixtures for the v1/v2/compat matrix."""

from __future__ import annotations

import pytest

from pygleif.compat.pydantic_support import get_namespace


@pytest.fixture(scope="session")
def namespace_info():
    """Return the active pydantic namespace metadata."""
    return get_namespace()

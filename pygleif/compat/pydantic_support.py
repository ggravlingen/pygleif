"""Helpers for working across pydantic namespaces during migration.

The v2 work targets pydantic v2, while v1 must keep constructing models
under either the ``pydantic.v1`` compatibility shim (when pydantic v2 is
installed) or a genuine pydantic v1 install. This module reports which
namespace is active so the test matrix can assert behavior in both.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

PYDANTIC_V2_MAJOR = 2


class PydanticNamespace(StrEnum):
    """Supported pydantic namespaces under test."""

    V1 = "pydantic.v1"
    V2 = "pydantic"


@dataclass(frozen=True)
class NamespaceInfo:
    """Resolved namespace metadata."""

    name: PydanticNamespace
    major: int


def get_namespace() -> NamespaceInfo:
    """Return the active pydantic namespace metadata."""
    import pydantic  # noqa: PLC0415 - deferred so import stays optional

    major = int(pydantic.VERSION.split(".", maxsplit=1)[0])
    if major >= PYDANTIC_V2_MAJOR:
        return NamespaceInfo(name=PydanticNamespace.V2, major=major)
    return NamespaceInfo(name=PydanticNamespace.V1, major=major)

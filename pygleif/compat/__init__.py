"""Shared compatibility surface.

This package must not depend on implementation details from v1 or v2.
It defines the stable contract (interfaces), normalization helpers
(adapters), and pydantic-namespace detection used by the test matrix.
"""

from .interfaces import BaseApiClient, RecordLike
from .pydantic_support import PydanticNamespace, get_namespace

__all__ = ["BaseApiClient", "PydanticNamespace", "RecordLike", "get_namespace"]

"""Module-level pydantic pinning for v2.

Only import pydantic from this shim inside ``pygleif.v2``. v2 targets the
modern pydantic v2 API.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from pydantic.alias_generators import to_camel

__all__ = ["BaseModel", "ConfigDict", "Field", "ValidationError", "to_camel"]

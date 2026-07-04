"""Module-level pydantic pinning for v1.

Only import pydantic from this shim inside ``pygleif.v1``. During the
migration the v1 models are pinned to the pydantic v1 namespace: when
pydantic v2 is installed this resolves to ``pydantic.v1`` (the built-in
compatibility shim); when a genuine pydantic v1 is installed it resolves
to the top-level ``pydantic`` package.
"""

from __future__ import annotations

try:  # pydantic v2 exposes the v1 API under ``pydantic.v1``.
    from pydantic.v1 import BaseModel, Field
except ImportError:  # genuine pydantic v1 install.
    from pydantic import BaseModel, Field

__all__ = ["BaseModel", "Field"]

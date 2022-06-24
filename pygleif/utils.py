"""Utility functions."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Union, cast
import urllib.request as url

from .const import URL_API


def load_json(lei_code: str) -> list[Any] | dict[Any, Any]:
    """Download data as JSON."""
    with url.urlopen(f"{URL_API}{lei_code}") as fdesc:
        return cast(Union[Dict[Any, Any], List[Any]], json.loads(fdesc.read()))

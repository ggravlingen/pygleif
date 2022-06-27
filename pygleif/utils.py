"""Utility functions."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Union, cast
from urllib import request


def load_json(search_url: str, search_string: str) -> list[Any] | dict[Any, Any]:
    """Download data as JSON."""
    with request.urlopen(f"{search_url}{request.quote(search_string)}") as fdesc:
        return cast(Union[Dict[Any, Any], List[Any]], json.loads(fdesc.read()))

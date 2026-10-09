from __future__ import annotations

import re
from typing import Any

_FIRST_CAP = re.compile(r"(.)([A-Z][a-z]+)")
_ALL_CAP = re.compile(r"([a-z0-9])([A-Z])")


def camel_to_snake(name: str) -> str:
    """Convert camelCase / PascalCase to snake_case.

    "currentLocation" -> "current_location"
    "lastUpdate"       -> "last_update"
    "routeId"          -> "route_id"
    "id"               -> "id"
    """
    s1 = _FIRST_CAP.sub(r"\1_\2", name)
    return _ALL_CAP.sub(r"\1_\2", s1).lower()


def normalize_keys(value: Any) -> Any:
    """Recursively convert all dict keys to snake_case.

    Lists and nested dicts are traversed; scalars are returned unchanged.
    """
    if isinstance(value, dict):
        return {camel_to_snake(k): normalize_keys(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize_keys(v) for v in value]
    return value

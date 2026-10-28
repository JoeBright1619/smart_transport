"""Shared error helpers producing the API's canonical error envelope.

Every service, router, and dependency that raises an HTTP error should use
``_raise_error`` (or, rarely, ``_error_detail`` directly when building a
response that is not an ``HTTPException``). The envelope shape is what
``main.py``'s ``_is_error_envelope`` recognises:

    {"data": None, "meta": None, "error": {"code": str, "message": str}}

The shape is intentionally rigid. Do not inline dict literals elsewhere —
the whole point of these helpers living here is that the wire shape cannot
drift between call sites.
"""

from __future__ import annotations

from typing import Any, NoReturn

from fastapi import HTTPException


def _error_detail(code: str, message: str) -> dict[str, Any]:
    return {
        "data": None,
        "meta": None,
        "error": {
            "code": code,
            "message": message,
        },
    }


def _raise_error(status_code: int, code: str, message: str) -> NoReturn:
    raise HTTPException(
        status_code=status_code,
        detail=_error_detail(code, message),
    )

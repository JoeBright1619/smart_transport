"""Tests for CORS-safe error responses.

A raw/unhandled exception produces a 500 in Starlette's ServerErrorMiddleware, which
sits outside CORSMiddleware. Without help, that 500 carries no Access-Control-Allow-Origin
header and the browser mislabels a genuine server error as a CORS failure — exactly how
the vehicle-registration 500 hid its real cause. These tests lock the header behaviour.
"""

from __future__ import annotations

from fastapi.responses import JSONResponse
from starlette.requests import Request

from app.core.config import settings
from main import _apply_cors_headers


def _request_with_origin(origin: str | None) -> Request:
    headers = [(b"origin", origin.encode())] if origin else []
    return Request({"type": "http", "method": "POST", "path": "/", "headers": headers})


def test_error_response_gets_cors_headers_for_allowed_origin():
    origin = list(settings.CORS_ORIGINS)[0]
    resp = _apply_cors_headers(
        _request_with_origin(origin), JSONResponse(status_code=500, content={})
    )
    assert resp.headers["access-control-allow-origin"] == origin
    assert resp.headers["access-control-allow-credentials"] == "true"


def test_error_response_omits_cors_headers_for_unknown_origin():
    resp = _apply_cors_headers(
        _request_with_origin("http://evil.example"),
        JSONResponse(status_code=500, content={}),
    )
    assert "access-control-allow-origin" not in resp.headers


def test_error_response_omits_cors_headers_without_origin():
    resp = _apply_cors_headers(
        _request_with_origin(None), JSONResponse(status_code=500, content={})
    )
    assert "access-control-allow-origin" not in resp.headers

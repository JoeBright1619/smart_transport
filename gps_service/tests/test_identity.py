from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from gps_service.vehicle_tracker.identity import resolve_tenant_id


async def _start_server(handler) -> TestServer:
    app = web.Application()
    app.router.add_get("/api/v1/service/whoami", handler)
    server = TestServer(app)
    await server.start_server()
    return server


@pytest.mark.asyncio
async def test_resolve_tenant_id_happy_path():
    async def handler(request: web.Request) -> web.Response:
        assert request.headers["X-Service-Token"] == "secret"
        return web.json_response(
            {
                "data": {"tenant_id": "ten-abc", "tenant_name": "Test"},
                "meta": None,
                "error": None,
            }
        )

    server = await _start_server(handler)
    try:
        tenant_id = await resolve_tenant_id(
            base_url=str(server.make_url("")).rstrip("/"),
            service_token="secret",
        )
    finally:
        await server.close()

    assert tenant_id == "ten-abc"


@pytest.mark.asyncio
async def test_resolve_tenant_id_raises_on_401():
    async def handler(request: web.Request) -> web.Response:
        return web.json_response({"error": "nope"}, status=401)

    server = await _start_server(handler)
    try:
        with pytest.raises(RuntimeError, match="401"):
            await resolve_tenant_id(
                base_url=str(server.make_url("")).rstrip("/"),
                service_token="bad",
            )
    finally:
        await server.close()


@pytest.mark.asyncio
async def test_resolve_tenant_id_raises_on_missing_field():
    async def handler(request: web.Request) -> web.Response:
        return web.json_response(
            {"data": {"tenant_name": "Test"}, "meta": None, "error": None}
        )

    server = await _start_server(handler)
    try:
        with pytest.raises(RuntimeError, match="tenant_id"):
            await resolve_tenant_id(
                base_url=str(server.make_url("")).rstrip("/"),
                service_token="secret",
            )
    finally:
        await server.close()


def test_resolve_tenant_id_requires_token(monkeypatch):
    monkeypatch.setattr("gps_service.config.settings.BACKEND_SERVICE_TOKEN", "")
    with pytest.raises(RuntimeError, match="BACKEND_SERVICE_TOKEN"):
        import asyncio

        asyncio.run(resolve_tenant_id())

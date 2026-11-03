"""Tests for /api/v1/service/routes — universal-token, tenant-agnostic."""

from __future__ import annotations

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.service_token_service import issue_token
from tests.conftest import auth_headers


async def _universal_token(
    db: AsyncSession, scopes: str = "vehicles:read_universal"
) -> str:
    _, plaintext = await issue_token(
        db, universal=True, scopes=scopes, name="pool-test"
    )
    await db.flush()
    return plaintext


async def test_service_route_superadmin_returns_200(
    client: AsyncClient, superadmin, route
) -> None:
    resp = await client.get(
        f"/api/v1/service/routes/{route.id}",
        headers=auth_headers(superadmin),
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == route.id


async def test_service_route_universal_token_returns_200(
    client: AsyncClient, db: AsyncSession, route
) -> None:
    plaintext = await _universal_token(db)
    resp = await client.get(
        f"/api/v1/service/routes/{route.id}",
        headers={"X-Service-Token": plaintext},
    )
    assert resp.status_code == 200


async def test_service_route_universal_without_scope_returns_403(
    client: AsyncClient, db: AsyncSession, route
) -> None:
    plaintext = await _universal_token(db, scopes="passengers:read_universal")
    resp = await client.get(
        f"/api/v1/service/routes/{route.id}",
        headers={"X-Service-Token": plaintext},
    )
    assert resp.status_code == 403


async def test_service_route_tenant_bound_token_returns_403(
    client: AsyncClient, db: AsyncSession, tenant, route
) -> None:
    _, plaintext = await issue_token(
        db,
        tenant_id=tenant.id,
        scopes="vehicles:read_universal",
        name="bound-test",
    )
    await db.flush()
    resp = await client.get(
        f"/api/v1/service/routes/{route.id}",
        headers={"X-Service-Token": plaintext},
    )
    assert resp.status_code == 403


async def test_service_route_no_auth_returns_401(client: AsyncClient, route) -> None:
    resp = await client.get(f"/api/v1/service/routes/{route.id}")
    assert resp.status_code == 401


async def test_service_route_404_unknown_id(
    client: AsyncClient, db: AsyncSession
) -> None:
    plaintext = await _universal_token(db)
    resp = await client.get(
        f"/api/v1/service/routes/route-{uuid.uuid4()}",
        headers={"X-Service-Token": plaintext},
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "route_not_found"


async def test_service_route_cross_tenant(
    client: AsyncClient,
    db: AsyncSession,
    make_tenant,
    make_route,
) -> None:
    plaintext = await _universal_token(db)
    tenant_a = await make_tenant()
    tenant_b = await make_tenant()
    route_a = await make_route(tenant_id=tenant_a.id)
    route_b = await make_route(tenant_id=tenant_b.id)

    for route in (route_a, route_b):
        resp = await client.get(
            f"/api/v1/service/routes/{route.id}",
            headers={"X-Service-Token": plaintext},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == route.id

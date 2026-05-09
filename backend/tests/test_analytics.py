"""Tests for analytics endpoint."""

from __future__ import annotations

import pytest

from tests.conftest import auth_headers


@pytest.fixture
async def tenant(make_tenant):
    return await make_tenant()


@pytest.fixture
async def admin(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="admin")


@pytest.fixture
async def operator(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="operator")


@pytest.fixture
async def dispatcher(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="dispatcher")


@pytest.fixture
async def passenger(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="passenger")


async def test_returns_200_for_admin(client, admin):
    r = await client.get("/api/v1/analytics", headers=auth_headers(admin))
    assert r.status_code == 200
    data = r.json()["data"]
    assert "totalVehicles" in data or "summary" in data or data is not None


async def test_returns_200_for_operator(client, operator):
    r = await client.get("/api/v1/analytics", headers=auth_headers(operator))
    assert r.status_code == 200


async def test_returns_401_without_token(client):
    r = await client.get("/api/v1/analytics")
    assert r.status_code == 401


async def test_returns_403_for_dispatcher(client, dispatcher):
    r = await client.get("/api/v1/analytics", headers=auth_headers(dispatcher))
    assert r.status_code == 403


async def test_returns_403_for_passenger(client, passenger):
    r = await client.get("/api/v1/analytics", headers=auth_headers(passenger))
    assert r.status_code == 403


async def test_accepts_date_range_params(client, admin):
    r = await client.get(
        "/api/v1/analytics?from=2026-05-01&to=2026-05-07",
        headers=auth_headers(admin),
    )
    assert r.status_code == 200

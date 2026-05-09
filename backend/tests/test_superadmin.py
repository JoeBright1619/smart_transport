"""Tests for superadmin portal endpoints."""

from __future__ import annotations

import pytest

from tests.conftest import auth_headers


@pytest.fixture
async def superadmin(make_user):
    return await make_user(tenant_id=None, role="superadmin")


@pytest.fixture
async def demo_tenant(make_tenant):
    return await make_tenant(name="Demo Company")


@pytest.fixture
async def tenant_admin(make_user, demo_tenant):
    return await make_user(tenant_id=demo_tenant.id, role="admin")


# ---------------------------------------------------------------------------
# GET /superadmin/tenants
# ---------------------------------------------------------------------------


async def test_list_tenants_returns_200(client, superadmin, demo_tenant):
    r = await client.get("/superadmin/tenants", headers=auth_headers(superadmin))
    assert r.status_code == 200
    ids = [t["id"] for t in r.json()["data"]]
    assert demo_tenant.id in ids


async def test_list_tenants_returns_401_without_token(client):
    r = await client.get("/superadmin/tenants")
    assert r.status_code == 401


async def test_list_tenants_returns_403_for_admin(client, tenant_admin):
    r = await client.get("/superadmin/tenants", headers=auth_headers(tenant_admin))
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# GET /superadmin/tenants/{id}
# ---------------------------------------------------------------------------


async def test_get_tenant_returns_200(client, superadmin, demo_tenant):
    r = await client.get(
        f"/superadmin/tenants/{demo_tenant.id}", headers=auth_headers(superadmin)
    )
    assert r.status_code == 200
    assert r.json()["data"]["id"] == demo_tenant.id


async def test_get_tenant_returns_401_without_token(client, demo_tenant):
    r = await client.get(f"/superadmin/tenants/{demo_tenant.id}")
    assert r.status_code == 401


async def test_get_tenant_returns_403_for_admin(client, tenant_admin, demo_tenant):
    r = await client.get(
        f"/superadmin/tenants/{demo_tenant.id}", headers=auth_headers(tenant_admin)
    )
    assert r.status_code == 403


async def test_get_tenant_returns_404_unknown(client, superadmin):
    r = await client.get(
        "/superadmin/tenants/ten-does-not-exist", headers=auth_headers(superadmin)
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /superadmin/tenants/{id} — suspend / reactivate
# ---------------------------------------------------------------------------


async def test_suspend_tenant(client, superadmin, demo_tenant):
    r = await client.patch(
        f"/superadmin/tenants/{demo_tenant.id}",
        json={"is_active": False},
        headers=auth_headers(superadmin),
    )
    assert r.status_code == 200
    assert r.json()["data"]["isActive"] is False


async def test_reactivate_tenant(client, superadmin, demo_tenant):
    await client.patch(
        f"/superadmin/tenants/{demo_tenant.id}",
        json={"is_active": False},
        headers=auth_headers(superadmin),
    )
    r = await client.patch(
        f"/superadmin/tenants/{demo_tenant.id}",
        json={"is_active": True},
        headers=auth_headers(superadmin),
    )
    assert r.status_code == 200
    assert r.json()["data"]["isActive"] is True


async def test_patch_tenant_returns_401_without_token(client, demo_tenant):
    r = await client.patch(
        f"/superadmin/tenants/{demo_tenant.id}", json={"is_active": False}
    )
    assert r.status_code == 401


async def test_patch_tenant_returns_403_for_admin(client, tenant_admin, demo_tenant):
    r = await client.patch(
        f"/superadmin/tenants/{demo_tenant.id}",
        json={"is_active": False},
        headers=auth_headers(tenant_admin),
    )
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# POST /superadmin/tenants/{id}/impersonate
# ---------------------------------------------------------------------------


async def test_impersonate_returns_token(client, superadmin, demo_tenant, tenant_admin):
    r = await client.post(
        f"/superadmin/tenants/{demo_tenant.id}/impersonate",
        headers=auth_headers(superadmin),
    )
    assert r.status_code == 200
    assert r.json()["data"]["accessToken"]


async def test_impersonate_returns_401_without_token(client, demo_tenant):
    r = await client.post(f"/superadmin/tenants/{demo_tenant.id}/impersonate")
    assert r.status_code == 401


async def test_impersonate_returns_403_for_admin(client, tenant_admin, demo_tenant):
    r = await client.post(
        f"/superadmin/tenants/{demo_tenant.id}/impersonate",
        headers=auth_headers(tenant_admin),
    )
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# GET /superadmin/analytics
# ---------------------------------------------------------------------------


async def test_platform_analytics_returns_200(client, superadmin):
    r = await client.get("/superadmin/analytics", headers=auth_headers(superadmin))
    assert r.status_code == 200
    assert r.json()["data"] is not None


async def test_platform_analytics_returns_401_without_token(client):
    r = await client.get("/superadmin/analytics")
    assert r.status_code == 401


async def test_platform_analytics_returns_403_for_admin(client, tenant_admin):
    r = await client.get("/superadmin/analytics", headers=auth_headers(tenant_admin))
    assert r.status_code == 403

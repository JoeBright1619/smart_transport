"""Tests for superadmin passenger management endpoints."""

from __future__ import annotations

import pytest

from tests.conftest import auth_headers


@pytest.fixture
async def superadmin(make_user):
    return await make_user(tenant_id=None, role="superadmin")


@pytest.fixture
async def tenant(make_tenant):
    return await make_tenant()


@pytest.fixture
async def passenger_a(make_user):
    return await make_user(tenant_id=None, role="passenger")


@pytest.fixture
async def passenger_b(make_user):
    return await make_user(tenant_id=None, role="passenger")


@pytest.fixture
async def tenant_admin(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="admin")


# ---------------------------------------------------------------------------
# GET /superadmin/passengers
# ---------------------------------------------------------------------------


async def test_list_passengers_returns_only_passenger_role_users(
    client, superadmin, passenger_a, passenger_b, tenant_admin
):
    r = await client.get("/superadmin/passengers", headers=auth_headers(superadmin))
    assert r.status_code == 200
    ids = [u["id"] for u in r.json()["data"]]
    assert passenger_a.id in ids
    assert passenger_b.id in ids
    assert (
        tenant_admin.id not in ids
    ), "Non-passenger user must not appear in passenger list"


async def test_list_passengers_requires_superadmin(client, tenant_admin):
    r = await client.get("/superadmin/passengers", headers=auth_headers(tenant_admin))
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# POST /superadmin/passengers/{id}/suspend
# POST /superadmin/passengers/{id}/reactivate
# ---------------------------------------------------------------------------


async def test_suspend_non_passenger_returns_403(client, superadmin, tenant_admin):
    r = await client.post(
        f"/superadmin/passengers/{tenant_admin.id}/suspend",
        headers=auth_headers(superadmin),
    )
    assert r.status_code == 403


async def test_suspend_and_reactivate_passenger(client, superadmin, passenger_a):
    r = await client.post(
        f"/superadmin/passengers/{passenger_a.id}/suspend",
        headers=auth_headers(superadmin),
    )
    assert r.status_code == 200
    assert r.json()["data"]["isDeleted"] is True

    r = await client.post(
        f"/superadmin/passengers/{passenger_a.id}/reactivate",
        headers=auth_headers(superadmin),
    )
    assert r.status_code == 200
    assert r.json()["data"]["isDeleted"] is False

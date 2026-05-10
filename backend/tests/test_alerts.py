"""Tests for alerts endpoints."""

from __future__ import annotations

import pytest

from app.models.alert import Alert
from tests.conftest import auth_headers


@pytest.fixture
async def tenant(make_tenant):
    return await make_tenant()


@pytest.fixture
async def admin(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="admin")


@pytest.fixture
async def dispatcher(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="dispatcher")


@pytest.fixture
async def passenger(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="passenger")


@pytest.fixture
async def vehicle(make_vehicle, tenant):
    return await make_vehicle(tenant_id=tenant.id)


@pytest.fixture
async def alert(db, tenant, vehicle):
    a = Alert(
        tenant_id=tenant.id,
        type="speeding",
        severity="high",
        title="Speeding Alert",
        message="Vehicle exceeding speed limit.",
        vehicle_id=vehicle.id,
        is_acknowledged=False,
    )
    db.add(a)
    await db.commit()
    return a


# ---------------------------------------------------------------------------
# GET /alerts
# ---------------------------------------------------------------------------


async def test_list_returns_200_and_includes_alert(client, admin, alert):
    r = await client.get("/api/v1/alerts", headers=auth_headers(admin))
    assert r.status_code == 200
    ids = [a["id"] for a in r.json()["data"]]
    assert alert.id in ids


async def test_list_returns_401_without_token(client):
    r = await client.get("/api/v1/alerts")
    assert r.status_code == 401


async def test_list_returns_403_for_passenger(client, passenger):
    r = await client.get("/api/v1/alerts", headers=auth_headers(passenger))
    assert r.status_code == 403


async def test_list_filter_by_severity(client, admin, alert):
    r = await client.get("/api/v1/alerts?severity=high", headers=auth_headers(admin))
    assert r.status_code == 200
    assert all(a["severity"] == "high" for a in r.json()["data"])


# ---------------------------------------------------------------------------
# POST /alerts/{id}/acknowledge
# ---------------------------------------------------------------------------


async def test_acknowledge_happy_path(client, admin, alert):
    r = await client.post(
        f"/api/v1/alerts/{alert.id}/acknowledge", headers=auth_headers(admin)
    )
    assert r.status_code == 200
    assert r.json()["data"]["isAcknowledged"] is True


async def test_acknowledge_returns_401_without_token(client, alert):
    r = await client.post(f"/api/v1/alerts/{alert.id}/acknowledge")
    assert r.status_code == 401


async def test_acknowledge_returns_404_unknown(client, admin):
    r = await client.post(
        "/api/v1/alerts/alert-does-not-exist/acknowledge",
        headers=auth_headers(admin),
    )
    assert r.status_code == 404

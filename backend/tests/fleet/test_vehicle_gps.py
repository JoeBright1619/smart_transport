"""Tests for Task 6.2 — vehicles always retain a last-known GPS position.

Policy: every vehicle carries a GPS position for every status, including ``offline``
(last-known position for safety/security). GPS is anchored near a bus stop on create
and is never cleared by a status change. When a tenant has no stops there is no position
to anchor to, so GPS stays unset (covered in test_vehicles.py).
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import patch

from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import auth_headers

_CREATE = {"registration_number": "RAD 777 G", "model": "Test Bus"}


async def test_created_vehicle_gets_gps_when_stops_exist(client, admin_user, stop):
    r = await client.post(
        "/api/v1/vehicles", json=_CREATE, headers=auth_headers(admin_user)
    )
    assert r.status_code == 201
    loc = r.json()["data"]["currentLocation"]
    assert loc is not None
    # Anchored near the tenant's stop (within jitter).
    assert abs(loc["lat"] - stop.lat) < 0.01
    assert abs(loc["lng"] - stop.lng) < 0.01


async def test_created_offline_vehicle_still_gets_gps(client, admin_user, stop):
    r = await client.post(
        "/api/v1/vehicles",
        json={**_CREATE, "status": "offline"},
        headers=auth_headers(admin_user),
    )
    assert r.status_code == 201
    data = r.json()["data"]
    assert data["status"] == "offline"
    # Offline = last-known position, not "no position".
    assert data["currentLocation"] is not None


async def test_setting_vehicle_offline_retains_gps(
    client, admin_user, make_vehicle, tenant
):
    active = await make_vehicle(
        tenant_id=tenant.id, status="active", lat=-1.95, lng=30.06
    )
    r = await client.patch(
        f"/api/v1/vehicles/{active.id}",
        json={"status": "offline"},
        headers=auth_headers(admin_user),
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["status"] == "offline"
    assert data["currentLocation"] == {"lat": -1.95, "lng": 30.06}


async def test_simulation_does_not_move_idle_vehicle(
    db: AsyncSession, make_vehicle, tenant
):
    idle = await make_vehicle(tenant_id=tenant.id, status="idle", lat=-1.95, lng=30.06)
    from app.services import simulation_runner

    @asynccontextmanager
    async def _fake_session():
        yield db

    with patch.object(simulation_runner, "AsyncSessionLocal", _fake_session):
        await simulation_runner.simulate_active_vehicles()

    assert idle.lat == -1.95
    assert idle.lng == 30.06

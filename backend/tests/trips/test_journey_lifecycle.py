"""Tests for Task 7.1 — a single guarded journey start; active requires driver+route+GPS.

A vehicle can only become ``active`` by starting a journey (which creates and activates a
trip). Setting ``status=active`` on a vehicle with no driver/route is rejected, and a
journey cannot be double-started from either the Fleet or the Dispatch path.
"""

from __future__ import annotations


from tests.conftest import auth_headers


async def _driver_status(client, admin_user, did):
    r = await client.get(f"/api/v1/drivers/{did}", headers=auth_headers(admin_user))
    return r.json()["data"]["status"]


async def test_set_active_without_driver_route_rejected(
    client, admin_user, make_vehicle, tenant
):
    vehicle = await make_vehicle(tenant_id=tenant.id, status="idle")
    r = await client.patch(
        f"/api/v1/vehicles/{vehicle.id}",
        json={"status": "active"},
        headers=auth_headers(admin_user),
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "JOURNEY_REQUIRES_DRIVER_ROUTE"
    # Vehicle stayed idle — no half-started journey.
    r2 = await client.get(
        f"/api/v1/vehicles/{vehicle.id}", headers=auth_headers(admin_user)
    )
    assert r2.json()["data"]["status"] == "idle"


async def test_set_active_with_driver_route_starts_journey(
    client, admin_user, make_vehicle, driver_user, route, tenant
):
    vehicle = await make_vehicle(
        tenant_id=tenant.id,
        status="idle",
        driver_id=driver_user.id,
        route_id=route.id,
        lat=-1.95,
        lng=30.06,
    )
    r = await client.patch(
        f"/api/v1/vehicles/{vehicle.id}",
        json={"status": "active"},
        headers=auth_headers(admin_user),
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["status"] == "active"
    assert data["currentLocation"] is not None
    # Activation put the driver on-trip — proof a trip was created and activated.
    assert await _driver_status(client, admin_user, driver_user.id) == "on-trip"


async def test_double_start_via_fleet_rejected(
    client, admin_user, make_vehicle, driver_user, route, tenant
):
    vehicle = await make_vehicle(
        tenant_id=tenant.id,
        status="idle",
        driver_id=driver_user.id,
        route_id=route.id,
        lat=-1.95,
        lng=30.06,
    )
    body = {"status": "active"}
    r1 = await client.patch(
        f"/api/v1/vehicles/{vehicle.id}", json=body, headers=auth_headers(admin_user)
    )
    assert r1.status_code == 200
    r2 = await client.patch(
        f"/api/v1/vehicles/{vehicle.id}", json=body, headers=auth_headers(admin_user)
    )
    assert r2.status_code == 409


async def test_fleet_start_blocks_dispatch_trip(
    client, admin_user, make_vehicle, driver_user, route, tenant
):
    vehicle = await make_vehicle(
        tenant_id=tenant.id,
        status="idle",
        driver_id=driver_user.id,
        route_id=route.id,
        lat=-1.95,
        lng=30.06,
    )
    r1 = await client.patch(
        f"/api/v1/vehicles/{vehicle.id}",
        json={"status": "active"},
        headers=auth_headers(admin_user),
    )
    assert r1.status_code == 200

    # Dispatch can no longer open a second trip for the now-running vehicle.
    r2 = await client.post(
        "/api/v1/trips",
        json={
            "vehicle_id": vehicle.id,
            "route_id": route.id,
            "driver_id": driver_user.id,
            "scheduled_start": "2026-06-01T08:00:00Z",
            "scheduled_end": "2026-06-01T10:00:00Z",
        },
        headers=auth_headers(admin_user),
    )
    assert r2.status_code == 409


async def test_dispatch_start_blocks_fleet_activate(
    client, admin_user, make_vehicle, driver_user, route, tenant
):
    vehicle = await make_vehicle(
        tenant_id=tenant.id, status="idle", lat=-1.95, lng=30.06
    )
    create = await client.post(
        "/api/v1/trips",
        json={
            "vehicle_id": vehicle.id,
            "route_id": route.id,
            "driver_id": driver_user.id,
            "scheduled_start": "2026-06-01T08:00:00Z",
            "scheduled_end": "2026-06-01T10:00:00Z",
        },
        headers=auth_headers(admin_user),
    )
    assert create.status_code == 201
    trip_id = create.json()["data"]["id"]
    activate = await client.patch(
        f"/api/v1/trips/{trip_id}",
        json={"status": "active"},
        headers=auth_headers(admin_user),
    )
    assert activate.status_code == 200

    # Fleet cannot independently re-activate the vehicle that's already on a trip.
    r = await client.patch(
        f"/api/v1/vehicles/{vehicle.id}",
        json={"status": "active"},
        headers=auth_headers(admin_user),
    )
    assert r.status_code == 409

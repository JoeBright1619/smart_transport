"""Tests for Task 7.3 — a disabled route can't be assigned, dispatched, or listed as active.

`route.is_active` is now enforced everywhere a route is put to work: vehicle route
assignment, trip dispatch, journey start, and the active-routes list used by the map.
"""

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
async def driver(make_driver, tenant):
    return await make_driver(tenant_id=tenant.id)


async def test_assign_inactive_route_to_vehicle_rejected(
    client, admin, make_vehicle, make_route, tenant
):
    route = await make_route(tenant_id=tenant.id, is_active=False)
    vehicle = await make_vehicle(tenant_id=tenant.id)
    r = await client.patch(
        f"/api/v1/vehicles/{vehicle.id}",
        json={"routeId": route.id},
        headers=auth_headers(admin),
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "ROUTE_INACTIVE"


async def test_assign_active_route_to_vehicle_ok(
    client, admin, make_vehicle, make_route, tenant
):
    route = await make_route(tenant_id=tenant.id, is_active=True)
    vehicle = await make_vehicle(tenant_id=tenant.id)
    r = await client.patch(
        f"/api/v1/vehicles/{vehicle.id}",
        json={"routeId": route.id},
        headers=auth_headers(admin),
    )
    assert r.status_code == 200
    assert r.json()["data"]["routeId"] == route.id


async def test_create_trip_on_inactive_route_rejected(
    client, admin, make_vehicle, make_route, driver, tenant
):
    route = await make_route(tenant_id=tenant.id, is_active=False)
    vehicle = await make_vehicle(tenant_id=tenant.id)
    r = await client.post(
        "/api/v1/trips",
        json={
            "vehicle_id": vehicle.id,
            "route_id": route.id,
            "driver_id": driver.id,
            "scheduled_start": "2026-06-01T08:00:00Z",
            "scheduled_end": "2026-06-01T10:00:00Z",
        },
        headers=auth_headers(admin),
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "ROUTE_INACTIVE"


async def test_start_journey_on_inactive_route_rejected(
    client, admin, make_vehicle, make_route, driver, tenant
):
    # Route was disabled after being assigned to the vehicle.
    route = await make_route(tenant_id=tenant.id, is_active=False)
    vehicle = await make_vehicle(
        tenant_id=tenant.id,
        status="idle",
        driver_id=driver.id,
        route_id=route.id,
        lat=-1.95,
        lng=30.06,
    )
    r = await client.patch(
        f"/api/v1/vehicles/{vehicle.id}",
        json={"status": "active"},
        headers=auth_headers(admin),
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "ROUTE_INACTIVE"


async def test_routes_list_excludes_inactive_with_filter(
    client, admin, make_route, tenant
):
    active = await make_route(tenant_id=tenant.id, is_active=True)
    disabled = await make_route(tenant_id=tenant.id, is_active=False)
    r = await client.get("/api/v1/routes?isActive=true", headers=auth_headers(admin))
    assert r.status_code == 200
    ids = [route["id"] for route in r.json()["data"]]
    assert active.id in ids
    assert disabled.id not in ids


# ---------------------------------------------------------------------------
# Disabling a route that is in use
# ---------------------------------------------------------------------------


async def test_disable_route_with_active_trip_rejected(
    client, admin, make_route, make_vehicle, make_driver, make_trip, tenant
):
    route = await make_route(tenant_id=tenant.id, is_active=True)
    vehicle = await make_vehicle(
        tenant_id=tenant.id, status="active", route_id=route.id
    )
    driver = await make_driver(tenant_id=tenant.id, status="on-trip")
    await make_trip(
        tenant_id=tenant.id,
        vehicle_id=vehicle.id,
        route_id=route.id,
        driver_id=driver.id,
        status="active",
    )
    r = await client.patch(
        f"/api/v1/routes/{route.id}",
        json={"isActive": False},
        headers=auth_headers(admin),
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "ROUTE_IN_USE"


async def test_disable_route_with_active_vehicle_rejected(
    client, admin, make_route, make_vehicle, tenant
):
    route = await make_route(tenant_id=tenant.id, is_active=True)
    await make_vehicle(tenant_id=tenant.id, status="active", route_id=route.id)
    r = await client.patch(
        f"/api/v1/routes/{route.id}",
        json={"isActive": False},
        headers=auth_headers(admin),
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "ROUTE_IN_USE"


async def test_disable_unused_route_ok(client, admin, make_route, tenant):
    route = await make_route(tenant_id=tenant.id, is_active=True)
    r = await client.patch(
        f"/api/v1/routes/{route.id}",
        json={"isActive": False},
        headers=auth_headers(admin),
    )
    assert r.status_code == 200
    assert r.json()["data"]["isActive"] is False

"""Tests that a maintenance record's status drives the vehicle's status.

Starting a job takes the vehicle into ``maintenance`` (guarded like a Fleet change, so it
can't strand a trip); completing it returns the vehicle to ``idle`` once no other job is
still open on it.
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


async def _create_record(client, admin, vehicle_id):
    r = await client.post(
        "/api/v1/maintenance",
        json={
            "vehicleId": vehicle_id,
            "type": "repair",
            "description": "Brake check",
            "scheduledDate": "2026-07-20",
            "cost": 50000,
        },
        headers=auth_headers(admin),
    )
    assert r.status_code == 201
    return r.json()["data"]


async def _set_status(client, admin, record_id, status):
    return await client.patch(
        f"/api/v1/maintenance/{record_id}",
        json={"status": status},
        headers=auth_headers(admin),
    )


async def _vehicle_status(client, admin, vehicle_id):
    r = await client.get(f"/api/v1/vehicles/{vehicle_id}", headers=auth_headers(admin))
    return r.json()["data"]["status"]


async def test_starting_maintenance_takes_vehicle_off_road(
    client, admin, make_vehicle, tenant
):
    vehicle = await make_vehicle(tenant_id=tenant.id, status="idle")
    record = await _create_record(client, admin, vehicle.id)

    r = await _set_status(client, admin, record["id"], "in-progress")
    assert r.status_code == 200
    assert await _vehicle_status(client, admin, vehicle.id) == "maintenance"


async def test_completing_maintenance_returns_vehicle_to_idle(
    client, admin, make_vehicle, tenant
):
    vehicle = await make_vehicle(tenant_id=tenant.id, status="idle")
    record = await _create_record(client, admin, vehicle.id)

    await _set_status(client, admin, record["id"], "in-progress")
    assert await _vehicle_status(client, admin, vehicle.id) == "maintenance"

    r = await _set_status(client, admin, record["id"], "completed")
    assert r.status_code == 200
    assert await _vehicle_status(client, admin, vehicle.id) == "idle"


async def test_completing_one_job_keeps_maintenance_while_another_open(
    client, admin, make_vehicle, tenant
):
    vehicle = await make_vehicle(tenant_id=tenant.id, status="idle")
    job_a = await _create_record(client, admin, vehicle.id)
    job_b = await _create_record(client, admin, vehicle.id)

    await _set_status(client, admin, job_a["id"], "in-progress")
    await _set_status(client, admin, job_b["id"], "in-progress")

    # Completing A leaves the vehicle in maintenance because B is still open.
    await _set_status(client, admin, job_a["id"], "completed")
    assert await _vehicle_status(client, admin, vehicle.id) == "maintenance"

    # Completing B (the last open job) frees the vehicle.
    await _set_status(client, admin, job_b["id"], "completed")
    assert await _vehicle_status(client, admin, vehicle.id) == "idle"


async def test_starting_maintenance_blocked_with_scheduled_trip(
    client, admin, make_vehicle, make_route, make_driver, make_trip, tenant
):
    vehicle = await make_vehicle(tenant_id=tenant.id, status="idle")
    route = await make_route(tenant_id=tenant.id)
    driver = await make_driver(tenant_id=tenant.id)
    await make_trip(
        tenant_id=tenant.id,
        vehicle_id=vehicle.id,
        route_id=route.id,
        driver_id=driver.id,
        status="scheduled",
    )
    record = await _create_record(client, admin, vehicle.id)

    r = await _set_status(client, admin, record["id"], "in-progress")
    assert r.status_code == 409
    # Neither the vehicle nor the record changed.
    assert await _vehicle_status(client, admin, vehicle.id) == "idle"
    rr = await client.get(
        f"/api/v1/maintenance/{record['id']}", headers=auth_headers(admin)
    )
    assert rr.json()["data"]["status"] == "scheduled"


async def test_starting_maintenance_blocked_with_active_trip(
    client, admin, make_vehicle, make_route, make_driver, make_trip, tenant
):
    vehicle = await make_vehicle(tenant_id=tenant.id, status="active")
    route = await make_route(tenant_id=tenant.id)
    driver = await make_driver(tenant_id=tenant.id)
    await make_trip(
        tenant_id=tenant.id,
        vehicle_id=vehicle.id,
        route_id=route.id,
        driver_id=driver.id,
        status="active",
    )
    record = await _create_record(client, admin, vehicle.id)

    r = await _set_status(client, admin, record["id"], "in-progress")
    assert r.status_code == 409

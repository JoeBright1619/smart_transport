"""Tests for Task 6.3 — a driver can be bound to only one vehicle at a time.

Both assignment paths (PATCH /vehicles with driverId, PATCH /drivers with vehicleId) go
through one centralised writer that keeps both FK sides in sync and rejects binding a
driver who is already assigned to another vehicle.
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


@pytest.fixture
async def vehicle(make_vehicle, tenant):
    return await make_vehicle(tenant_id=tenant.id)


async def _vehicle(client, admin, vid):
    r = await client.get(f"/api/v1/vehicles/{vid}", headers=auth_headers(admin))
    return r.json()["data"]


async def _driver(client, admin, did):
    r = await client.get(f"/api/v1/drivers/{did}", headers=auth_headers(admin))
    return r.json()["data"]


# ---------------------------------------------------------------------------
# Assignment via the vehicle path (PATCH /vehicles {driverId})
# ---------------------------------------------------------------------------


async def test_assign_driver_via_vehicle_sets_both_sides(
    client, admin, driver, vehicle
):
    r = await client.patch(
        f"/api/v1/vehicles/{vehicle.id}",
        json={"driverId": driver.id},
        headers=auth_headers(admin),
    )
    assert r.status_code == 200
    assert r.json()["data"]["driverId"] == driver.id
    # The reciprocal side is set too.
    assert (await _driver(client, admin, driver.id))["vehicleId"] == vehicle.id


async def test_assign_same_pairing_is_idempotent(client, admin, driver, vehicle):
    body = {"driverId": driver.id}
    r1 = await client.patch(
        f"/api/v1/vehicles/{vehicle.id}", json=body, headers=auth_headers(admin)
    )
    r2 = await client.patch(
        f"/api/v1/vehicles/{vehicle.id}", json=body, headers=auth_headers(admin)
    )
    assert r1.status_code == 200
    assert r2.status_code == 200


async def test_assign_already_bound_driver_returns_409(
    client, admin, driver, make_vehicle, tenant
):
    veh_a = await make_vehicle(tenant_id=tenant.id)
    veh_b = await make_vehicle(tenant_id=tenant.id)

    r1 = await client.patch(
        f"/api/v1/vehicles/{veh_a.id}",
        json={"driverId": driver.id},
        headers=auth_headers(admin),
    )
    assert r1.status_code == 200

    r2 = await client.patch(
        f"/api/v1/vehicles/{veh_b.id}",
        json={"driverId": driver.id},
        headers=auth_headers(admin),
    )
    assert r2.status_code == 409
    assert r2.json()["error"]["code"] == "DRIVER_ALREADY_ASSIGNED"
    # veh_b was left untouched.
    assert (await _vehicle(client, admin, veh_b.id))["driverId"] is None


async def test_unassign_driver_clears_both_sides(client, admin, driver, vehicle):
    await client.patch(
        f"/api/v1/vehicles/{vehicle.id}",
        json={"driverId": driver.id},
        headers=auth_headers(admin),
    )
    r = await client.patch(
        f"/api/v1/vehicles/{vehicle.id}",
        json={"driverId": None},
        headers=auth_headers(admin),
    )
    assert r.status_code == 200
    assert r.json()["data"]["driverId"] is None
    assert (await _driver(client, admin, driver.id))["vehicleId"] is None


async def test_assign_unknown_driver_returns_404(client, admin, vehicle):
    r = await client.patch(
        f"/api/v1/vehicles/{vehicle.id}",
        json={"driverId": "drv-does-not-exist"},
        headers=auth_headers(admin),
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Assignment via the driver path (PATCH /drivers {vehicleId})
# ---------------------------------------------------------------------------


async def test_assign_via_driver_path_sets_both_sides(client, admin, driver, vehicle):
    r = await client.patch(
        f"/api/v1/drivers/{driver.id}",
        json={"vehicleId": vehicle.id},
        headers=auth_headers(admin),
    )
    assert r.status_code == 200
    assert r.json()["data"]["vehicleId"] == vehicle.id
    assert (await _vehicle(client, admin, vehicle.id))["driverId"] == driver.id


async def test_driver_path_rejects_second_vehicle(
    client, admin, driver, make_vehicle, tenant
):
    veh_a = await make_vehicle(tenant_id=tenant.id)
    veh_b = await make_vehicle(tenant_id=tenant.id)

    r1 = await client.patch(
        f"/api/v1/drivers/{driver.id}",
        json={"vehicleId": veh_a.id},
        headers=auth_headers(admin),
    )
    assert r1.status_code == 200

    r2 = await client.patch(
        f"/api/v1/drivers/{driver.id}",
        json={"vehicleId": veh_b.id},
        headers=auth_headers(admin),
    )
    assert r2.status_code == 409

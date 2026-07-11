"""Tests for driver <-> vehicle assignment (Tasks 6.3 + follow-up).

Reassignment moves a driver freely (no manual unassign). The only hard block is an
*active* vehicle: you can't move a driver off / onto / away from a vehicle that is on a
journey. Both FK sides are always kept in sync.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

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
# Basic assign / idempotency / sync
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


async def test_assign_unknown_driver_returns_404(client, admin, vehicle):
    r = await client.patch(
        f"/api/v1/vehicles/{vehicle.id}",
        json={"driverId": "drv-does-not-exist"},
        headers=auth_headers(admin),
    )
    assert r.status_code == 404


async def test_assign_via_driver_path_sets_both_sides(client, admin, driver, vehicle):
    r = await client.patch(
        f"/api/v1/drivers/{driver.id}",
        json={"vehicleId": vehicle.id},
        headers=auth_headers(admin),
    )
    assert r.status_code == 200
    assert r.json()["data"]["vehicleId"] == vehicle.id
    assert (await _vehicle(client, admin, vehicle.id))["driverId"] == driver.id


# ---------------------------------------------------------------------------
# Reassignment moves freely when nothing is active
# ---------------------------------------------------------------------------


async def test_reassign_idle_driver_moves_to_new_vehicle(
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

    # No manual unassign needed — moving the (idle) driver just works.
    r2 = await client.patch(
        f"/api/v1/vehicles/{veh_b.id}",
        json={"driverId": driver.id},
        headers=auth_headers(admin),
    )
    assert r2.status_code == 200
    assert (await _vehicle(client, admin, veh_b.id))["driverId"] == driver.id
    # The old vehicle was released.
    assert (await _vehicle(client, admin, veh_a.id))["driverId"] is None
    assert (await _driver(client, admin, driver.id))["vehicleId"] == veh_b.id


async def test_replace_idle_target_driver(
    client, admin, make_driver, make_vehicle, tenant
):
    driver_a = await make_driver(tenant_id=tenant.id)
    driver_b = await make_driver(tenant_id=tenant.id)
    veh = await make_vehicle(tenant_id=tenant.id)

    await client.patch(
        f"/api/v1/vehicles/{veh.id}",
        json={"driverId": driver_a.id},
        headers=auth_headers(admin),
    )
    r = await client.patch(
        f"/api/v1/vehicles/{veh.id}",
        json={"driverId": driver_b.id},
        headers=auth_headers(admin),
    )
    assert r.status_code == 200
    assert (await _vehicle(client, admin, veh.id))["driverId"] == driver_b.id
    # The replaced driver was released.
    assert (await _driver(client, admin, driver_a.id))["vehicleId"] is None


async def test_driver_path_reassign_moves_when_idle(
    client, admin, driver, make_vehicle, tenant
):
    veh_a = await make_vehicle(tenant_id=tenant.id)
    veh_b = await make_vehicle(tenant_id=tenant.id)
    await client.patch(
        f"/api/v1/drivers/{driver.id}",
        json={"vehicleId": veh_a.id},
        headers=auth_headers(admin),
    )
    r = await client.patch(
        f"/api/v1/drivers/{driver.id}",
        json={"vehicleId": veh_b.id},
        headers=auth_headers(admin),
    )
    assert r.status_code == 200
    assert (await _driver(client, admin, driver.id))["vehicleId"] == veh_b.id


# ---------------------------------------------------------------------------
# Active vehicles are locked
# ---------------------------------------------------------------------------


async def test_reassign_blocked_when_old_vehicle_active(
    db: AsyncSession, client, admin, make_driver, make_vehicle, tenant
):
    veh_a = await make_vehicle(
        tenant_id=tenant.id, status="active", lat=-1.95, lng=30.06
    )
    driver = await make_driver(tenant_id=tenant.id, vehicle_id=veh_a.id)
    veh_a.driver_id = driver.id
    await db.commit()
    veh_b = await make_vehicle(tenant_id=tenant.id)

    r = await client.patch(
        f"/api/v1/vehicles/{veh_b.id}",
        json={"driverId": driver.id},
        headers=auth_headers(admin),
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "DRIVER_ON_ACTIVE_JOURNEY"


async def test_swap_blocked_when_target_vehicle_active(
    db: AsyncSession, client, admin, make_driver, make_vehicle, tenant
):
    driver_a = await make_driver(tenant_id=tenant.id)
    veh = await make_vehicle(
        tenant_id=tenant.id,
        status="active",
        driver_id=driver_a.id,
        lat=-1.95,
        lng=30.06,
    )
    driver_a.vehicle_id = veh.id
    await db.commit()
    driver_b = await make_driver(tenant_id=tenant.id)

    r = await client.patch(
        f"/api/v1/vehicles/{veh.id}",
        json={"driverId": driver_b.id},
        headers=auth_headers(admin),
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "VEHICLE_ON_ACTIVE_JOURNEY"


# ---------------------------------------------------------------------------
# Unassignment
# ---------------------------------------------------------------------------


async def test_unassign_driver_clears_both_sides_when_idle(
    client, admin, driver, vehicle
):
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


async def test_unassign_blocked_when_vehicle_active(
    db: AsyncSession, client, admin, make_driver, make_vehicle, tenant
):
    driver = await make_driver(tenant_id=tenant.id)
    veh = await make_vehicle(
        tenant_id=tenant.id, status="active", driver_id=driver.id, lat=-1.95, lng=30.06
    )
    driver.vehicle_id = veh.id
    await db.commit()

    r = await client.patch(
        f"/api/v1/vehicles/{veh.id}",
        json={"driverId": None},
        headers=auth_headers(admin),
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "VEHICLE_ON_ACTIVE_JOURNEY"


async def test_driver_path_unassign_blocked_when_active(
    db: AsyncSession, client, admin, make_driver, make_vehicle, tenant
):
    driver = await make_driver(tenant_id=tenant.id)
    veh = await make_vehicle(
        tenant_id=tenant.id, status="active", driver_id=driver.id, lat=-1.95, lng=30.06
    )
    driver.vehicle_id = veh.id
    await db.commit()

    r = await client.patch(
        f"/api/v1/drivers/{driver.id}",
        json={"vehicleId": None},
        headers=auth_headers(admin),
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "VEHICLE_ON_ACTIVE_JOURNEY"

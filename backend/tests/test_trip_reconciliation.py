"""Tests for Task 6.4 — orphaned trips no longer block a driver from going off-duty.

An "orphaned" trip is one marked active/scheduled whose vehicle no longer backs it
(deactivated, unassigned, or lost on a process restart). Reconciliation cancels such
trips and frees any driver left stuck on-trip, and the off-duty endpoint self-heals by
reconciling before it checks.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.trip_reconciliation import reconcile_orphaned_trips
from tests.conftest import auth_headers


@pytest.fixture
async def tenant(make_tenant):
    return await make_tenant()


@pytest.fixture
async def admin(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="admin")


@pytest.fixture
async def route(make_route, tenant):
    return await make_route(tenant_id=tenant.id)


# ---------------------------------------------------------------------------
# Off-duty endpoint behaviour
# ---------------------------------------------------------------------------


async def test_off_duty_allowed_after_reconciling_orphan(
    client, admin, make_vehicle, make_driver, make_trip, tenant, route
):
    driver = await make_driver(tenant_id=tenant.id, status="on-trip")
    # Vehicle is idle (not running) — the active trip below is therefore an orphan.
    vehicle = await make_vehicle(tenant_id=tenant.id, status="idle")
    await make_trip(
        tenant_id=tenant.id,
        vehicle_id=vehicle.id,
        route_id=route.id,
        driver_id=driver.id,
        status="active",
    )

    r = await client.patch(
        f"/api/v1/drivers/{driver.id}",
        json={"status": "off-duty"},
        headers=auth_headers(admin),
    )
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "off-duty"


async def test_off_duty_blocked_for_genuinely_running_trip(
    client, admin, make_vehicle, make_driver, make_trip, tenant, route
):
    driver = await make_driver(tenant_id=tenant.id, status="on-trip")
    # Vehicle is active and still linked to this driver + route → the trip is live.
    vehicle = await make_vehicle(
        tenant_id=tenant.id,
        status="active",
        route_id=route.id,
        driver_id=driver.id,
    )
    await make_trip(
        tenant_id=tenant.id,
        vehicle_id=vehicle.id,
        route_id=route.id,
        driver_id=driver.id,
        status="active",
    )

    r = await client.patch(
        f"/api/v1/drivers/{driver.id}",
        json={"status": "off-duty"},
        headers=auth_headers(admin),
    )
    assert r.status_code == 409


async def test_off_duty_blocked_by_live_scheduled_trip(
    client, admin, make_vehicle, make_driver, make_trip, tenant, route
):
    driver = await make_driver(tenant_id=tenant.id, status="available")
    # Idle vehicle still reserving this driver + route → scheduled trip is legitimate.
    vehicle = await make_vehicle(
        tenant_id=tenant.id,
        status="idle",
        route_id=route.id,
        driver_id=driver.id,
    )
    await make_trip(
        tenant_id=tenant.id,
        vehicle_id=vehicle.id,
        route_id=route.id,
        driver_id=driver.id,
        status="scheduled",
    )

    r = await client.patch(
        f"/api/v1/drivers/{driver.id}",
        json={"status": "off-duty"},
        headers=auth_headers(admin),
    )
    assert r.status_code == 409


# ---------------------------------------------------------------------------
# reconcile_orphaned_trips directly
# ---------------------------------------------------------------------------


async def test_reconcile_cancels_orphan_and_frees_driver(
    db: AsyncSession, make_vehicle, make_driver, make_trip, tenant, route
):
    driver = await make_driver(tenant_id=tenant.id, status="on-trip")
    vehicle = await make_vehicle(tenant_id=tenant.id, status="idle")
    trip = await make_trip(
        tenant_id=tenant.id,
        vehicle_id=vehicle.id,
        route_id=route.id,
        driver_id=driver.id,
        status="active",
    )

    count = await reconcile_orphaned_trips(db, tenant_id=tenant.id)
    assert count == 1
    await db.refresh(trip)
    await db.refresh(driver)
    assert trip.status == "cancelled"
    assert driver.status == "available"


async def test_reconcile_keeps_live_trip(
    db: AsyncSession, make_vehicle, make_driver, make_trip, tenant, route
):
    driver = await make_driver(tenant_id=tenant.id, status="on-trip")
    vehicle = await make_vehicle(
        tenant_id=tenant.id,
        status="active",
        route_id=route.id,
        driver_id=driver.id,
    )
    trip = await make_trip(
        tenant_id=tenant.id,
        vehicle_id=vehicle.id,
        route_id=route.id,
        driver_id=driver.id,
        status="active",
    )

    count = await reconcile_orphaned_trips(db, tenant_id=tenant.id)
    assert count == 0
    await db.refresh(trip)
    await db.refresh(driver)
    assert trip.status == "active"
    assert driver.status == "on-trip"

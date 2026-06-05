"""Tests for vehicle seating capacity and occupancy fields (Task 13.1).

Covers:
  - seating_capacity stored on create (default 45)
  - seatingCapacity / currentOccupancy / remainingSeats in GET response
  - PATCH /vehicles/{id} can update seating_capacity
  - current_occupancy cannot be set via API (ignored silently)
  - Trip completion resets current_occupancy to 0
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import auth_headers

_VEHICLE_BASE = {
    "registration_number": "CAP 001 A",
    "model": "Capacity Test Bus",
    "capacity": 60,
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def tenant(make_tenant):
    return await make_tenant()


@pytest.fixture
async def admin(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="admin")


@pytest.fixture
async def vehicle(make_vehicle, tenant):
    return await make_vehicle(tenant_id=tenant.id)


# ---------------------------------------------------------------------------
# CREATE tests
# ---------------------------------------------------------------------------


async def test_create_vehicle_with_explicit_seating_capacity(client, admin, tenant):
    r = await client.post(
        "/api/v1/vehicles",
        json={**_VEHICLE_BASE, "seating_capacity": 55},
        headers=auth_headers(admin),
    )
    assert r.status_code == 201
    data = r.json()["data"]
    assert data["seatingCapacity"] == 55
    assert data["currentOccupancy"] == 0
    assert data["remainingSeats"] == 55


async def test_create_vehicle_defaults_seating_capacity_to_45(client, admin, tenant):
    r = await client.post(
        "/api/v1/vehicles",
        json={**_VEHICLE_BASE, "registration_number": "CAP 002 A"},
        headers=auth_headers(admin),
    )
    assert r.status_code == 201
    assert r.json()["data"]["seatingCapacity"] == 45


# ---------------------------------------------------------------------------
# GET tests
# ---------------------------------------------------------------------------


async def test_list_vehicles_includes_capacity_fields(client, admin, vehicle):
    r = await client.get("/api/v1/vehicles", headers=auth_headers(admin))
    assert r.status_code == 200
    items = r.json()["data"]
    assert len(items) >= 1
    first = next(v for v in items if v["id"] == vehicle.id)
    assert "seatingCapacity" in first
    assert "currentOccupancy" in first
    assert "remainingSeats" in first


async def test_remaining_seats_computed_correctly(
    client, admin, tenant, db: AsyncSession
):
    from app.models.vehicle import Vehicle
    from sqlalchemy import select

    r = await client.post(
        "/api/v1/vehicles",
        json={
            **_VEHICLE_BASE,
            "registration_number": "CAP 003 A",
            "seating_capacity": 30,
        },
        headers=auth_headers(admin),
    )
    assert r.status_code == 201
    vid = r.json()["data"]["id"]

    # Simulate occupancy directly in DB
    v = await db.scalar(select(Vehicle).where(Vehicle.id == vid))
    assert v is not None
    v.current_occupancy = 12
    await db.commit()

    r2 = await client.get(f"/api/v1/vehicles/{vid}", headers=auth_headers(admin))
    assert r2.status_code == 200
    data = r2.json()["data"]
    assert data["currentOccupancy"] == 12
    assert data["remainingSeats"] == 18  # 30 - 12


# ---------------------------------------------------------------------------
# PATCH tests
# ---------------------------------------------------------------------------


async def test_patch_seating_capacity(client, admin, vehicle):
    r = await client.patch(
        f"/api/v1/vehicles/{vehicle.id}",
        json={"seating_capacity": 50},
        headers=auth_headers(admin),
    )
    assert r.status_code == 200
    assert r.json()["data"]["seatingCapacity"] == 50


async def test_patch_current_occupancy_is_ignored(
    client, admin, vehicle, db: AsyncSession
):
    from app.models.vehicle import Vehicle
    from sqlalchemy import select

    # Attempt to set occupancy via API — should be silently ignored
    r = await client.patch(
        f"/api/v1/vehicles/{vehicle.id}",
        json={"current_occupancy": 99},
        headers=auth_headers(admin),
    )
    assert r.status_code == 200

    v = await db.scalar(select(Vehicle).where(Vehicle.id == vehicle.id))
    assert v is not None
    assert v.current_occupancy == 0  # unchanged


# ---------------------------------------------------------------------------
# Trip completion resets occupancy
# ---------------------------------------------------------------------------


async def test_trip_completion_resets_current_occupancy(
    db: AsyncSession, tenant, make_vehicle, make_driver, make_route
):
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import select

    from app.models.vehicle import Vehicle
    from app.schemas.trip import TripCreate
    from app.services import trip_service

    route = await make_route(tenant_id=tenant.id)
    vehicle = await make_vehicle(tenant_id=tenant.id, route_id=route.id)
    driver = await make_driver(tenant_id=tenant.id, vehicle_id=vehicle.id)

    now = datetime.now(timezone.utc)
    trip = await trip_service.create_trip(
        db,
        TripCreate(
            vehicle_id=vehicle.id,
            route_id=route.id,
            driver_id=driver.id,
            scheduled_start=now,
            scheduled_end=now + timedelta(hours=1),
        ),
        tenant.id,
        "user-test",
    )
    await db.commit()

    # Activate trip
    from app.schemas.trip import TripUpdate

    await trip_service.update_trip(
        db, trip.id, TripUpdate(status="active"), tenant.id, "user-test"
    )
    await db.commit()

    # Set occupancy to simulate passengers on board
    v = await db.scalar(select(Vehicle).where(Vehicle.id == vehicle.id))
    assert v is not None
    v.current_occupancy = 15
    await db.commit()

    # Complete the trip
    await trip_service.update_trip(
        db, trip.id, TripUpdate(status="completed"), tenant.id, "user-test"
    )
    await db.commit()

    await db.refresh(v)
    assert v.current_occupancy == 0

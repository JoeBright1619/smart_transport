"""Tests for passenger journey statistics (Task 12.3).

Covers:
  - GET /api/v1/passengers/me/stats
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.boarding_record import BoardingRecord
from app.models.passenger_profile import PassengerProfile
from tests.conftest import auth_headers


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def passenger(make_user):
    return await make_user(tenant_id=None, role="passenger", email="stats@test.local")


@pytest.fixture
async def admin(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="admin")


@pytest.fixture
async def tenant(make_tenant):
    return await make_tenant()


@pytest.fixture
async def stop(tenant, db: AsyncSession):
    from app.models.route import Stop

    s = Stop(
        id="stop-stats-test",
        tenant_id=tenant.id,
        name="Central Station",
        lat=0.0,
        lng=0.0,
        is_deleted=False,
    )
    db.add(s)
    await db.commit()
    return s


async def _add_boardings(
    db: AsyncSession,
    passenger_id: str,
    stop_id: str,
    tenant_id: str,
    count: int,
) -> None:
    for _ in range(count):
        db.add(
            BoardingRecord(
                stop_id=stop_id,
                passenger_id=passenger_id,
                event_type="boarded",
                count=1,
                recorded_at=datetime.now(timezone.utc),
                occupancy_after=1,
                tenant_id=tenant_id,
            )
        )
    await db.commit()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


async def test_stats_requires_auth(client):
    r = await client.get("/api/v1/passengers/me/stats")
    assert r.status_code == 401


async def test_stats_forbidden_for_admin(client, admin):
    r = await client.get("/api/v1/passengers/me/stats", headers=auth_headers(admin))
    assert r.status_code == 403


async def test_stats_empty_when_no_boardings(client, passenger):
    r = await client.get("/api/v1/passengers/me/stats", headers=auth_headers(passenger))
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["totalTrips"] == 0
    assert data["hasEnoughData"] is False
    assert data["routesUsed"] == []


async def test_stats_has_enough_data_false_below_threshold(
    client, passenger, stop, tenant, db: AsyncSession
):
    await _add_boardings(db, passenger.id, stop.id, tenant.id, 2)
    r = await client.get("/api/v1/passengers/me/stats", headers=auth_headers(passenger))
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["totalTrips"] == 2
    assert data["hasEnoughData"] is False


async def test_stats_has_enough_data_true_at_threshold(
    client, passenger, stop, tenant, db: AsyncSession
):
    await _add_boardings(db, passenger.id, stop.id, tenant.id, 3)
    r = await client.get("/api/v1/passengers/me/stats", headers=auth_headers(passenger))
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["totalTrips"] == 3
    assert data["hasEnoughData"] is True


async def test_stats_counts_only_own_boardings(
    client, passenger, make_user, stop, tenant, db: AsyncSession
):
    other = await make_user(tenant_id=None, role="passenger", email="other@stats.local")
    await _add_boardings(db, other.id, stop.id, tenant.id, 5)
    await _add_boardings(db, passenger.id, stop.id, tenant.id, 3)

    r = await client.get("/api/v1/passengers/me/stats", headers=auth_headers(passenger))
    assert r.status_code == 200
    assert r.json()["data"]["totalTrips"] == 3


async def test_stats_favourite_stop_identified(
    client, passenger, stop, tenant, db: AsyncSession
):
    from app.models.route import Stop

    stop2 = Stop(
        id="stop-stats-b",
        tenant_id=tenant.id,
        name="Bus Terminal",
        lat=1.0,
        lng=1.0,
        is_deleted=False,
    )
    db.add(stop2)
    await db.commit()

    # 4 boardings at Central Station, 2 at Bus Terminal
    await _add_boardings(db, passenger.id, stop.id, tenant.id, 4)
    await _add_boardings(db, passenger.id, stop2.id, tenant.id, 2)

    r = await client.get("/api/v1/passengers/me/stats", headers=auth_headers(passenger))
    assert r.status_code == 200
    assert r.json()["data"]["favouriteStop"] == "Central Station"


async def test_stats_weekly_trips_this_week(
    client, passenger, stop, tenant, db: AsyncSession
):
    await _add_boardings(db, passenger.id, stop.id, tenant.id, 3)

    r = await client.get("/api/v1/passengers/me/stats", headers=auth_headers(passenger))
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["thisWeekTrips"] == 3
    assert len(data["weeklyTrips"]) == 4


async def test_stats_increments_profile_on_boarding(
    db: AsyncSession, passenger, stop, tenant
):
    """record_stop_events should increment total_trips_recorded when passenger_id is set."""
    from datetime import datetime, timezone

    from app.models.vehicle import Vehicle
    from app.services.boarding_service import record_stop_events

    vehicle = Vehicle(
        id="veh-stats-test",
        tenant_id=tenant.id,
        registration_number="ST 0001",
        model="Bus",
        seating_capacity=40,
        status="active",
        engine_status="good",
        is_deleted=False,
    )
    db.add(vehicle)
    db.add(PassengerProfile(user_id=passenger.id, total_trips_recorded=0))
    await db.commit()

    from sqlalchemy import select

    now = datetime.now(timezone.utc)
    await record_stop_events(
        db, vehicle, stop.id, 1, 0, 1, now, passenger_id=passenger.id
    )
    await db.commit()

    profile = await db.scalar(
        select(PassengerProfile).where(PassengerProfile.user_id == passenger.id)
    )
    assert profile is not None
    assert profile.total_trips_recorded == 1

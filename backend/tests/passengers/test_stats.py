"""Tests for passenger journey statistics (Task 12.3).

Covers:
  - GET /api/v1/passengers/me/stats
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.boarding_record import BoardingRecord
from tests.conftest import auth_headers


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def stop(make_stop, tenant):
    return await make_stop(
        tenant_id=tenant.id, name="Central Station", lat=0.0, lng=0.0
    )


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
    await db.flush()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


async def test_stats_requires_auth(client):
    r = await client.get("/api/v1/passengers/me/stats")
    assert r.status_code == 401


async def test_stats_forbidden_for_admin(client, admin_user):
    r = await client.get(
        "/api/v1/passengers/me/stats", headers=auth_headers(admin_user)
    )
    assert r.status_code == 403


async def test_stats_empty_when_no_boardings(client, passenger_user):
    r = await client.get(
        "/api/v1/passengers/me/stats", headers=auth_headers(passenger_user)
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["totalTrips"] == 0
    assert data["hasEnoughData"] is False
    assert data["routesUsed"] == []


async def test_stats_has_enough_data_false_below_threshold(
    client, passenger_user, stop, tenant, db: AsyncSession
):
    await _add_boardings(db, passenger_user.id, stop.id, tenant.id, 2)
    r = await client.get(
        "/api/v1/passengers/me/stats", headers=auth_headers(passenger_user)
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["totalTrips"] == 2
    assert data["hasEnoughData"] is False


async def test_stats_has_enough_data_true_at_threshold(
    client, passenger_user, stop, tenant, db: AsyncSession
):
    await _add_boardings(db, passenger_user.id, stop.id, tenant.id, 3)
    r = await client.get(
        "/api/v1/passengers/me/stats", headers=auth_headers(passenger_user)
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["totalTrips"] == 3
    assert data["hasEnoughData"] is True


async def test_stats_counts_only_own_boardings(
    client, passenger_user, make_user, stop, tenant, db: AsyncSession
):
    other = await make_user(tenant_id=None, role="passenger", email="other@stats.local")
    await _add_boardings(db, other.id, stop.id, tenant.id, 5)
    await _add_boardings(db, passenger_user.id, stop.id, tenant.id, 3)

    r = await client.get(
        "/api/v1/passengers/me/stats", headers=auth_headers(passenger_user)
    )
    assert r.status_code == 200
    assert r.json()["data"]["totalTrips"] == 3


async def test_stats_favourite_stop_identified(
    client, passenger_user, stop, tenant, db: AsyncSession
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
    await db.flush()

    # 4 boardings at Central Station, 2 at Bus Terminal
    await _add_boardings(db, passenger_user.id, stop.id, tenant.id, 4)
    await _add_boardings(db, passenger_user.id, stop2.id, tenant.id, 2)

    r = await client.get(
        "/api/v1/passengers/me/stats", headers=auth_headers(passenger_user)
    )
    assert r.status_code == 200
    assert r.json()["data"]["favouriteStop"] == "Central Station"


async def test_stats_weekly_trips_this_week(
    client, passenger_user, stop, tenant, db: AsyncSession
):
    await _add_boardings(db, passenger_user.id, stop.id, tenant.id, 3)

    r = await client.get(
        "/api/v1/passengers/me/stats", headers=auth_headers(passenger_user)
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["thisWeekTrips"] == 3
    assert len(data["weeklyTrips"]) == 4

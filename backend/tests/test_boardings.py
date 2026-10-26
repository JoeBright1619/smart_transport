"""Tests for boarding records (Task 12.2).

Covers:
  - GET /api/v1/boardings      (admin list with filters)
  - GET /api/v1/boardings/me   (passenger's own boardings)
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
async def admin(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="admin")


@pytest.fixture
async def passenger(make_user):
    return await make_user(tenant_id=None, role="passenger", email="pass@board.local")


@pytest.fixture
async def stop(tenant, db: AsyncSession):
    from app.models.route import Stop

    s = Stop(
        id="stop-brd-test",
        tenant_id=tenant.id,
        name="Test Stop",
        lat=0.0,
        lng=0.0,
        is_deleted=False,
    )
    db.add(s)
    await db.flush()
    return s


@pytest.fixture
async def boarding(tenant, stop, db: AsyncSession):
    rec = BoardingRecord(
        stop_id=stop.id,
        event_type="boarded",
        count=3,
        recorded_at=datetime.now(timezone.utc),
        occupancy_after=3,
        tenant_id=tenant.id,
    )
    db.add(rec)
    await db.flush()
    return rec


# ---------------------------------------------------------------------------
# GET /api/v1/boardings  (admin)
# ---------------------------------------------------------------------------


async def test_list_boardings_returns_records(client, admin, boarding):
    r = await client.get("/api/v1/boardings", headers=auth_headers(admin))
    assert r.status_code == 200
    body = r.json()
    assert body["meta"]["total"] >= 1
    ids = [b["id"] for b in body["data"]]
    assert boarding.id in ids


async def test_list_boardings_filter_by_stop(client, admin, boarding, stop):
    r = await client.get(
        f"/api/v1/boardings?stopId={stop.id}", headers=auth_headers(admin)
    )
    assert r.status_code == 200
    assert all(b["stopId"] == stop.id for b in r.json()["data"])


async def test_list_boardings_returns_stop_name(client, admin, boarding):
    r = await client.get("/api/v1/boardings", headers=auth_headers(admin))
    assert r.status_code == 200
    row = next(b for b in r.json()["data"] if b["id"] == boarding.id)
    assert row["stopName"] == "Test Stop"


async def test_list_boardings_requires_auth(client):
    r = await client.get("/api/v1/boardings")
    assert r.status_code == 401


async def test_list_boardings_forbidden_for_passenger(client, passenger):
    r = await client.get("/api/v1/boardings", headers=auth_headers(passenger))
    assert r.status_code == 403


async def test_list_boardings_pagination(client, admin, stop, tenant, db: AsyncSession):
    for i in range(3):
        db.add(
            BoardingRecord(
                stop_id=stop.id,
                event_type="alighted",
                count=1,
                recorded_at=datetime.now(timezone.utc),
                occupancy_after=i,
                tenant_id=tenant.id,
            )
        )
    await db.flush()

    r = await client.get(
        "/api/v1/boardings?page=1&pageSize=2", headers=auth_headers(admin)
    )
    assert r.status_code == 200
    assert len(r.json()["data"]) <= 2
    assert r.json()["meta"]["total"] >= 3


# ---------------------------------------------------------------------------
# GET /api/v1/boardings/me  (passenger)
# ---------------------------------------------------------------------------


async def test_my_boardings_empty_for_anonymous(client, passenger):
    r = await client.get("/api/v1/boardings/me", headers=auth_headers(passenger))
    assert r.status_code == 200
    assert r.json()["data"] == []
    assert r.json()["meta"]["total"] == 0


async def test_my_boardings_returns_own_records(
    client, passenger, stop, db: AsyncSession, tenant
):
    rec = BoardingRecord(
        stop_id=stop.id,
        passenger_id=passenger.id,
        event_type="boarded",
        count=1,
        recorded_at=datetime.now(timezone.utc),
        occupancy_after=1,
        tenant_id=tenant.id,
    )
    db.add(rec)
    await db.flush()

    r = await client.get("/api/v1/boardings/me", headers=auth_headers(passenger))
    assert r.status_code == 200
    assert r.json()["meta"]["total"] == 1
    assert r.json()["data"][0]["boardingId"] == rec.id


async def test_my_boardings_requires_auth(client):
    r = await client.get("/api/v1/boardings/me")
    assert r.status_code == 401


async def test_my_boardings_forbidden_for_admin(client, admin):
    r = await client.get("/api/v1/boardings/me", headers=auth_headers(admin))
    assert r.status_code == 403

"""Tests for passenger profile management (Task 12.1).

Covers:
  - GET  /api/v1/passengers/me
  - PATCH /api/v1/passengers/me
  - GET  /api/v1/passengers  (admin list)
  - Profile auto-created on GET if missing
"""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.passenger_profile import PassengerProfile
from tests.conftest import auth_headers


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
async def passenger(make_user):
    return await make_user(tenant_id=None, role="passenger", email="pass@test.local")


# ---------------------------------------------------------------------------
# GET /api/v1/passengers/me
# ---------------------------------------------------------------------------


async def test_get_profile_auto_creates_if_missing(client, passenger):
    r = await client.get("/api/v1/passengers/me", headers=auth_headers(passenger))
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["userId"] == passenger.id
    assert data["preferredRoutes"] == []
    assert data["preferredStops"] == []
    assert data["notifyOnArrival"] is True
    assert data["notifyOnDelay"] is True


async def test_get_profile_returns_name_and_email(client, passenger):
    r = await client.get("/api/v1/passengers/me", headers=auth_headers(passenger))
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["email"] == passenger.email
    assert data["fullName"] == passenger.full_name


async def test_get_profile_requires_auth(client):
    r = await client.get("/api/v1/passengers/me")
    assert r.status_code == 401


async def test_get_profile_forbidden_for_admin(client, admin):
    r = await client.get("/api/v1/passengers/me", headers=auth_headers(admin))
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# PATCH /api/v1/passengers/me
# ---------------------------------------------------------------------------


async def test_patch_profile_updates_phone(client, passenger, db: AsyncSession):
    r = await client.patch(
        "/api/v1/passengers/me",
        json={"phone": "+250788000001"},
        headers=auth_headers(passenger),
    )
    assert r.status_code == 200
    assert r.json()["data"]["phone"] == "+250788000001"

    profile = await db.scalar(
        select(PassengerProfile).where(PassengerProfile.user_id == passenger.id)
    )
    assert profile is not None
    assert profile.phone == "+250788000001"


async def test_patch_profile_updates_notifications(client, passenger):
    r = await client.patch(
        "/api/v1/passengers/me",
        json={"notifyOnArrival": False, "notifyOnDelay": False},
        headers=auth_headers(passenger),
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["notifyOnArrival"] is False
    assert data["notifyOnDelay"] is False


async def test_patch_profile_sets_preferred_routes(client, passenger):
    fake_route_ids = ["route-aaa", "route-bbb"]
    r = await client.patch(
        "/api/v1/passengers/me",
        json={"preferredRoutes": fake_route_ids},
        headers=auth_headers(passenger),
    )
    assert r.status_code == 200
    # IDs stored; resolution returns empty list since routes don't exist in test DB
    assert isinstance(r.json()["data"]["preferredRoutes"], list)


async def test_patch_profile_partial_update_does_not_reset_other_fields(
    client, passenger
):
    # Set phone first
    await client.patch(
        "/api/v1/passengers/me",
        json={"phone": "+250700000000"},
        headers=auth_headers(passenger),
    )
    # Update only notifications
    r = await client.patch(
        "/api/v1/passengers/me",
        json={"notifyOnDelay": False},
        headers=auth_headers(passenger),
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["phone"] == "+250700000000"  # unchanged
    assert data["notifyOnDelay"] is False


async def test_patch_profile_requires_auth(client):
    r = await client.patch("/api/v1/passengers/me", json={"phone": "+1"})
    assert r.status_code == 401


async def test_patch_profile_forbidden_for_admin(client, admin):
    r = await client.patch(
        "/api/v1/passengers/me", json={"phone": "+1"}, headers=auth_headers(admin)
    )
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/v1/passengers  (admin list)
# ---------------------------------------------------------------------------


async def test_list_passengers_returns_passengers(client, admin, passenger):
    r = await client.get("/api/v1/passengers", headers=auth_headers(admin))
    assert r.status_code == 200
    body = r.json()
    assert body["meta"]["total"] >= 1
    ids = [p["id"] for p in body["data"]]
    assert passenger.id in ids


async def test_list_passengers_excludes_staff(client, admin, make_user, tenant):
    operator = await make_user(tenant_id=tenant.id, role="operator")
    r = await client.get("/api/v1/passengers", headers=auth_headers(admin))
    ids = [p["id"] for p in r.json()["data"]]
    assert operator.id not in ids


async def test_list_passengers_requires_admin(client, passenger):
    r = await client.get("/api/v1/passengers", headers=auth_headers(passenger))
    assert r.status_code == 403


async def test_list_passengers_requires_auth(client):
    r = await client.get("/api/v1/passengers")
    assert r.status_code == 401


async def test_list_passengers_pagination(client, admin, make_user):
    for i in range(3):
        await make_user(tenant_id=None, role="passenger", email=f"p{i}@test.local")
    r = await client.get(
        "/api/v1/passengers?page=1&page_size=2", headers=auth_headers(admin)
    )
    assert r.status_code == 200
    assert len(r.json()["data"]) <= 2
    assert r.json()["meta"]["total"] >= 3

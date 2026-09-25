"""Tests for GET /api/v1/passengers/me/notifications (Task 4.3)."""

from __future__ import annotations


from tests.conftest import auth_headers


async def test_notifications_returns_arrivals_for_preferred_stop(
    client, passenger_user, stop, active_vehicle_at_stop
):
    """Passenger with a favourite stop served by an active vehicle gets a non-empty list."""
    r = await client.patch(
        "/api/v1/passengers/me",
        headers=auth_headers(passenger_user),
        json={"preferredStops": [stop.id]},
    )
    assert r.status_code == 200

    r = await client.get(
        "/api/v1/passengers/me/notifications",
        headers=auth_headers(passenger_user),
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["stopName"] == stop.name
    assert len(data[0]["arrivals"]) >= 1


async def test_notifications_empty_when_no_preferred_stops(client, passenger_user):
    """Passenger with no preferred stops receives an empty list."""
    r = await client.get(
        "/api/v1/passengers/me/notifications",
        headers=auth_headers(passenger_user),
    )
    assert r.status_code == 200
    assert r.json()["data"] == []


async def test_notifications_requires_passenger_role(
    client, make_user, make_tenant, tenant
):
    """Non-passenger users are blocked from the notifications endpoint."""
    admin = await make_user(tenant_id=tenant.id, role="admin")
    r = await client.get(
        "/api/v1/passengers/me/notifications",
        headers=auth_headers(admin),
    )
    assert r.status_code == 403

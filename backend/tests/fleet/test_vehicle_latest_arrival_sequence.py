"""Tests for GET /api/v1/vehicles/{id}/latest-arrival-sequence."""

from __future__ import annotations

from tests.conftest import auth_headers


async def test_returns_max_arrival_sequence(
    client, admin_user, vehicle, make_occupancy_event
):
    # Insert out of order so max is meaningful (not first or last).
    for seq in (5, 2, 11, 7):
        await make_occupancy_event(
            tenant_id=vehicle.tenant_id,
            vehicle_id=vehicle.id,
            arrival_sequence=seq,
        )

    r = await client.get(
        f"/api/v1/vehicles/{vehicle.id}/latest-arrival-sequence",
        headers=auth_headers(admin_user),
    )
    assert r.status_code == 200
    print("RESPONSE:", r.json())  # temporary
    assert r.json()["data"]["arrivalSequence"] == 11


async def test_returns_404_vehicle_not_found_unknown(client, admin_user):
    r = await client.get(
        "/api/v1/vehicles/veh-does-not-exist/latest-arrival-sequence",
        headers=auth_headers(admin_user),
    )
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "vehicle_not_found"


async def test_returns_404_vehicle_not_found_cross_tenant(
    client, admin_user, make_tenant, make_vehicle
):
    other_tenant = await make_tenant(name="Other Co")
    other_vehicle = await make_vehicle(tenant_id=other_tenant.id)

    r = await client.get(
        f"/api/v1/vehicles/{other_vehicle.id}/latest-arrival-sequence",
        headers=auth_headers(admin_user),
    )
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "vehicle_not_found"


async def test_returns_404_no_arrival_records(client, admin_user, vehicle):
    # Known vehicle, zero occupancy_events rows.
    r = await client.get(
        f"/api/v1/vehicles/{vehicle.id}/latest-arrival-sequence",
        headers=auth_headers(admin_user),
    )
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "no_arrival_records"

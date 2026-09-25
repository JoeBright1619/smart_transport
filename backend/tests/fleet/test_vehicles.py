"""Tests for vehicles CRUD endpoints."""

from __future__ import annotations


from tests.conftest import auth_headers

_CREATE = {
    "registration_number": "RAD 999 Z",
    "model": "Test Bus",
}


# ---------------------------------------------------------------------------
# GET /vehicles
# ---------------------------------------------------------------------------


async def test_list_returns_200_for_admin(client, admin_user, vehicle):
    r = await client.get("/api/v1/vehicles", headers=auth_headers(admin_user))
    assert r.status_code == 200
    ids = [v["id"] for v in r.json()["data"]]
    assert vehicle.id in ids


async def test_list_returns_401_without_token(client):
    r = await client.get("/api/v1/vehicles")
    assert r.status_code == 401


async def test_list_returns_403_for_passenger(client, passenger_user):
    r = await client.get("/api/v1/vehicles", headers=auth_headers(passenger_user))
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# POST /vehicles
# ---------------------------------------------------------------------------


async def test_create_happy_path(client, admin_user):
    r = await client.post(
        "/api/v1/vehicles", json=_CREATE, headers=auth_headers(admin_user)
    )
    assert r.status_code == 201
    assert r.json()["data"]["registrationNumber"] == "RAD 999 Z"


async def test_create_active_vehicle_rejected(client, admin_user):
    # A new vehicle has no trip/driver/route, so it can't be created as active.
    r = await client.post(
        "/api/v1/vehicles",
        json={**_CREATE, "status": "active"},
        headers=auth_headers(admin_user),
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "CANNOT_CREATE_ACTIVE"


async def test_create_without_stops_has_no_gps(client, admin_user):
    # This tenant has no stops, so there is no position to anchor to → GPS stays unset.
    # (GPS assignment when stops exist is covered in test_vehicle_gps.py.)
    r = await client.post(
        "/api/v1/vehicles", json=_CREATE, headers=auth_headers(admin_user)
    )
    assert r.status_code == 201
    data = r.json()["data"]
    assert data["status"] == "idle"
    assert data["currentLocation"] is None


async def test_create_duplicate_within_tenant_returns_409(client, admin_user):
    r1 = await client.post(
        "/api/v1/vehicles", json=_CREATE, headers=auth_headers(admin_user)
    )
    assert r1.status_code == 201
    r2 = await client.post(
        "/api/v1/vehicles", json=_CREATE, headers=auth_headers(admin_user)
    )
    assert r2.status_code == 409


async def test_create_same_registration_different_tenant_allowed(
    client, admin_user, make_tenant, make_user
):
    r1 = await client.post(
        "/api/v1/vehicles", json=_CREATE, headers=auth_headers(admin_user)
    )
    assert r1.status_code == 201

    other_tenant = await make_tenant(name="Other Co")
    other_admin = await make_user(tenant_id=other_tenant.id, role="admin")
    r2 = await client.post(
        "/api/v1/vehicles", json=_CREATE, headers=auth_headers(other_admin)
    )
    assert r2.status_code == 201


async def test_create_returns_401_without_token(client):
    r = await client.post("/api/v1/vehicles", json=_CREATE)
    assert r.status_code == 401


async def test_create_returns_403_for_dispatcher(client, dispatcher_user):
    r = await client.post(
        "/api/v1/vehicles", json=_CREATE, headers=auth_headers(dispatcher_user)
    )
    assert r.status_code == 403


async def test_create_returns_422_missing_field(client, admin_user):
    r = await client.post(
        "/api/v1/vehicles", json={"model": "Bus"}, headers=auth_headers(admin_user)
    )
    assert r.status_code == 422


async def test_create_returns_422_invalid_seating_capacity(client, admin_user):
    r = await client.post(
        "/api/v1/vehicles",
        json={**_CREATE, "seating_capacity": 0},
        headers=auth_headers(admin_user),
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# GET /vehicles/{id}
# ---------------------------------------------------------------------------


async def test_get_returns_200(client, admin_user, vehicle):
    r = await client.get(
        f"/api/v1/vehicles/{vehicle.id}", headers=auth_headers(admin_user)
    )
    assert r.status_code == 200
    assert r.json()["data"]["id"] == vehicle.id


async def test_get_returns_401_without_token(client, vehicle):
    r = await client.get(f"/api/v1/vehicles/{vehicle.id}")
    assert r.status_code == 401


async def test_get_returns_404_unknown_id(client, admin_user):
    r = await client.get(
        "/api/v1/vehicles/veh-does-not-exist", headers=auth_headers(admin_user)
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /vehicles/{id}
# ---------------------------------------------------------------------------


async def test_patch_happy_path(client, admin_user, vehicle):
    r = await client.patch(
        f"/api/v1/vehicles/{vehicle.id}",
        json={"fuel": 75},
        headers=auth_headers(admin_user),
    )
    assert r.status_code == 200
    assert r.json()["data"]["fuel"] == 75


async def test_patch_returns_401_without_token(client, vehicle):
    r = await client.patch(f"/api/v1/vehicles/{vehicle.id}", json={"fuel": 50})
    assert r.status_code == 401


async def test_patch_returns_403_for_dispatcher(client, dispatcher_user, vehicle):
    r = await client.patch(
        f"/api/v1/vehicles/{vehicle.id}",
        json={"fuel": 50},
        headers=auth_headers(dispatcher_user),
    )
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /vehicles/{id}
# ---------------------------------------------------------------------------


async def test_delete_happy_path(client, admin_user, vehicle):
    r = await client.delete(
        f"/api/v1/vehicles/{vehicle.id}", headers=auth_headers(admin_user)
    )
    assert r.status_code == 204
    r2 = await client.get(
        f"/api/v1/vehicles/{vehicle.id}", headers=auth_headers(admin_user)
    )
    assert r2.status_code == 404


async def test_delete_returns_401_without_token(client, vehicle):
    r = await client.delete(f"/api/v1/vehicles/{vehicle.id}")
    assert r.status_code == 401


async def test_delete_returns_403_for_operator(client, operator_user, vehicle):
    r = await client.delete(
        f"/api/v1/vehicles/{vehicle.id}", headers=auth_headers(operator_user)
    )
    assert r.status_code == 403


async def test_delete_active_vehicle_returns_409(
    client, admin_user, make_vehicle, tenant
):
    active = await make_vehicle(tenant_id=tenant.id, status="active")
    r = await client.delete(
        f"/api/v1/vehicles/{active.id}", headers=auth_headers(admin_user)
    )
    assert r.status_code == 409

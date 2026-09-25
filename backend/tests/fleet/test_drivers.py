"""Tests for drivers CRUD endpoints."""

from __future__ import annotations


from tests.conftest import auth_headers

_CREATE = {
    "name": "Test Driver",
    "license_number": "DL-TEST-001",
    "phone": "+250700000099",
    "certification_expiry": "2028-12-31",
}


# ---------------------------------------------------------------------------
# GET /drivers
# ---------------------------------------------------------------------------


async def test_list_returns_200(client, admin_user, driver_user):
    r = await client.get("/api/v1/drivers", headers=auth_headers(admin_user))
    assert r.status_code == 200
    ids = [d["id"] for d in r.json()["data"]]
    assert driver_user.id in ids


async def test_list_returns_401_without_token(client):
    r = await client.get("/api/v1/drivers")
    assert r.status_code == 401


async def test_list_returns_403_for_passenger(client, passenger_user):
    r = await client.get("/api/v1/drivers", headers=auth_headers(passenger_user))
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# POST /drivers
# ---------------------------------------------------------------------------


async def test_create_happy_path(client, admin_user):
    r = await client.post(
        "/api/v1/drivers", json=_CREATE, headers=auth_headers(admin_user)
    )
    assert r.status_code == 201
    assert r.json()["data"]["name"] == "Test Driver"


async def test_create_returns_401_without_token(client):
    r = await client.post("/api/v1/drivers", json=_CREATE)
    assert r.status_code == 401


async def test_create_returns_403_for_dispatcher(client, dispatcher_user):
    r = await client.post(
        "/api/v1/drivers", json=_CREATE, headers=auth_headers(dispatcher_user)
    )
    assert r.status_code == 403


async def test_create_returns_422_missing_expiry(client, admin_user):
    payload = {k: v for k, v in _CREATE.items() if k != "certification_expiry"}
    r = await client.post(
        "/api/v1/drivers", json=payload, headers=auth_headers(admin_user)
    )
    assert r.status_code == 422


async def test_create_returns_422_invalid_phone(client, admin_user):
    r = await client.post(
        "/api/v1/drivers",
        json={**_CREATE, "phone": "not-a-phone"},
        headers=auth_headers(admin_user),
    )
    assert r.status_code == 422


async def test_create_returns_422_blank_name(client, admin_user):
    r = await client.post(
        "/api/v1/drivers",
        json={**_CREATE, "name": " "},
        headers=auth_headers(admin_user),
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# GET /drivers/{id}
# ---------------------------------------------------------------------------


async def test_get_returns_200(client, admin_user, driver_user):
    r = await client.get(
        f"/api/v1/drivers/{driver_user.id}", headers=auth_headers(admin_user)
    )
    assert r.status_code == 200
    assert r.json()["data"]["id"] == driver_user.id


async def test_get_returns_401_without_token(client, driver_user):
    r = await client.get(f"/api/v1/drivers/{driver_user.id}")
    assert r.status_code == 401


async def test_get_returns_404_unknown(client, admin_user):
    r = await client.get(
        "/api/v1/drivers/drv-does-not-exist", headers=auth_headers(admin_user)
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /drivers/{id}
# ---------------------------------------------------------------------------


async def test_patch_happy_path(client, admin_user, driver_user):
    r = await client.patch(
        f"/api/v1/drivers/{driver_user.id}",
        json={"status": "off-duty"},
        headers=auth_headers(admin_user),
    )
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "off-duty"


async def test_patch_returns_401_without_token(client, driver_user):
    r = await client.patch(
        f"/api/v1/drivers/{driver_user.id}", json={"status": "off-duty"}
    )
    assert r.status_code == 401


async def test_patch_returns_403_for_dispatcher(client, dispatcher_user, driver_user):
    r = await client.patch(
        f"/api/v1/drivers/{driver_user.id}",
        json={"status": "off-duty"},
        headers=auth_headers(dispatcher_user),
    )
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /drivers/{id}
# ---------------------------------------------------------------------------


async def test_delete_happy_path(client, admin_user, driver_user):
    r = await client.delete(
        f"/api/v1/drivers/{driver_user.id}", headers=auth_headers(admin_user)
    )
    assert r.status_code == 204


async def test_delete_returns_401_without_token(client, driver_user):
    r = await client.delete(f"/api/v1/drivers/{driver_user.id}")
    assert r.status_code == 401


async def test_delete_returns_403_for_operator(client, operator_user, driver_user):
    r = await client.delete(
        f"/api/v1/drivers/{driver_user.id}", headers=auth_headers(operator_user)
    )
    assert r.status_code == 403


async def test_delete_on_trip_driver_returns_400(
    client, admin_user, make_driver, tenant
):
    busy = await make_driver(tenant_id=tenant.id, status="on-trip")
    r = await client.delete(
        f"/api/v1/drivers/{busy.id}", headers=auth_headers(admin_user)
    )
    assert r.status_code == 400

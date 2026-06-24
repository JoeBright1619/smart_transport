"""Tests for drivers CRUD endpoints."""

from __future__ import annotations

import pytest

from tests.conftest import auth_headers

_CREATE = {
    "name": "Test Driver",
    "license_number": "DL-TEST-001",
    "phone": "+250700000099",
    "certification_expiry": "2028-12-31",
}


@pytest.fixture
async def tenant(make_tenant):
    return await make_tenant()


@pytest.fixture
async def admin(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="admin")


@pytest.fixture
async def operator(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="operator")


@pytest.fixture
async def dispatcher(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="dispatcher")


@pytest.fixture
async def passenger(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="passenger")


@pytest.fixture
async def driver(make_driver, tenant):
    return await make_driver(tenant_id=tenant.id)


# ---------------------------------------------------------------------------
# GET /drivers
# ---------------------------------------------------------------------------


async def test_list_returns_200(client, admin, driver):
    r = await client.get("/api/v1/drivers", headers=auth_headers(admin))
    assert r.status_code == 200
    ids = [d["id"] for d in r.json()["data"]]
    assert driver.id in ids


async def test_list_returns_401_without_token(client):
    r = await client.get("/api/v1/drivers")
    assert r.status_code == 401


async def test_list_returns_403_for_passenger(client, passenger):
    r = await client.get("/api/v1/drivers", headers=auth_headers(passenger))
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# POST /drivers
# ---------------------------------------------------------------------------


async def test_create_happy_path(client, admin):
    r = await client.post("/api/v1/drivers", json=_CREATE, headers=auth_headers(admin))
    assert r.status_code == 201
    assert r.json()["data"]["name"] == "Test Driver"


async def test_create_returns_401_without_token(client):
    r = await client.post("/api/v1/drivers", json=_CREATE)
    assert r.status_code == 401


async def test_create_returns_403_for_dispatcher(client, dispatcher):
    r = await client.post(
        "/api/v1/drivers", json=_CREATE, headers=auth_headers(dispatcher)
    )
    assert r.status_code == 403


async def test_create_returns_422_missing_expiry(client, admin):
    payload = {k: v for k, v in _CREATE.items() if k != "certification_expiry"}
    r = await client.post("/api/v1/drivers", json=payload, headers=auth_headers(admin))
    assert r.status_code == 422


async def test_create_returns_422_invalid_phone(client, admin):
    r = await client.post(
        "/api/v1/drivers",
        json={**_CREATE, "phone": "not-a-phone"},
        headers=auth_headers(admin),
    )
    assert r.status_code == 422


async def test_create_returns_422_blank_name(client, admin):
    r = await client.post(
        "/api/v1/drivers",
        json={**_CREATE, "name": " "},
        headers=auth_headers(admin),
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# GET /drivers/{id}
# ---------------------------------------------------------------------------


async def test_get_returns_200(client, admin, driver):
    r = await client.get(f"/api/v1/drivers/{driver.id}", headers=auth_headers(admin))
    assert r.status_code == 200
    assert r.json()["data"]["id"] == driver.id


async def test_get_returns_401_without_token(client, driver):
    r = await client.get(f"/api/v1/drivers/{driver.id}")
    assert r.status_code == 401


async def test_get_returns_404_unknown(client, admin):
    r = await client.get(
        "/api/v1/drivers/drv-does-not-exist", headers=auth_headers(admin)
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /drivers/{id}
# ---------------------------------------------------------------------------


async def test_patch_happy_path(client, admin, driver):
    r = await client.patch(
        f"/api/v1/drivers/{driver.id}",
        json={"status": "off-duty"},
        headers=auth_headers(admin),
    )
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "off-duty"


async def test_patch_returns_401_without_token(client, driver):
    r = await client.patch(f"/api/v1/drivers/{driver.id}", json={"status": "off-duty"})
    assert r.status_code == 401


async def test_patch_returns_403_for_dispatcher(client, dispatcher, driver):
    r = await client.patch(
        f"/api/v1/drivers/{driver.id}",
        json={"status": "off-duty"},
        headers=auth_headers(dispatcher),
    )
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /drivers/{id}
# ---------------------------------------------------------------------------


async def test_delete_happy_path(client, admin, driver):
    r = await client.delete(f"/api/v1/drivers/{driver.id}", headers=auth_headers(admin))
    assert r.status_code == 204


async def test_delete_returns_401_without_token(client, driver):
    r = await client.delete(f"/api/v1/drivers/{driver.id}")
    assert r.status_code == 401


async def test_delete_returns_403_for_operator(client, operator, driver):
    r = await client.delete(
        f"/api/v1/drivers/{driver.id}", headers=auth_headers(operator)
    )
    assert r.status_code == 403


async def test_delete_on_trip_driver_returns_400(client, admin, make_driver, tenant):
    busy = await make_driver(tenant_id=tenant.id, status="on-trip")
    r = await client.delete(f"/api/v1/drivers/{busy.id}", headers=auth_headers(admin))
    assert r.status_code == 400

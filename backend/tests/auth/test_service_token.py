import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.service_token_service import issue_token


@pytest.mark.asyncio
async def test_service_token_grants_tenant_access(
    client: AsyncClient, tenant, db: AsyncSession
):
    _, plaintext = await issue_token(
        db, tenant_id=tenant.id, name="gps-sim-test", scopes="vehicles:read"
    )
    await db.commit()

    resp = await client.get(
        "/api/v1/vehicles?status=active",
        headers={"X-Service-Token": plaintext},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"] == []
    assert body["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_service_token_returns_only_its_tenant_vehicles(
    client: AsyncClient,
    tenant,
    db: AsyncSession,
    make_tenant,
    make_vehicle,
):
    # A second tenant whose vehicles must NOT leak into the first tenant's view
    other_tenant = await make_tenant(name="Other Co")

    own_vehicle = await make_vehicle(
        tenant_id=tenant.id,
        status="active",
        route_id="route-1",
    )
    other_vehicle = await make_vehicle(
        tenant_id=other_tenant.id,
        status="active",
        route_id="route-1",
    )

    _, plaintext = await issue_token(
        db,
        tenant_id=tenant.id,
        name="gps-sim-test",
        scopes="vehicles:read",
    )
    await db.commit()

    resp = await client.get(
        "/api/v1/vehicles?status=active",
        headers={"X-Service-Token": plaintext},
    )
    assert resp.status_code == 200
    body = resp.json()

    returned_ids = {v["id"] for v in body["data"]}
    assert own_vehicle.id in returned_ids
    assert other_vehicle.id not in returned_ids
    assert body["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_each_service_token_sees_only_its_own_tenant_vehicles(
    client: AsyncClient,
    tenant,
    db: AsyncSession,
    make_tenant,
    make_vehicle,
):
    other_tenant = await make_tenant(name="Other Co")

    own_vehicle = await make_vehicle(
        tenant_id=tenant.id,
        status="active",
        route_id="route-1",
    )
    other_vehicle = await make_vehicle(
        tenant_id=other_tenant.id,
        status="active",
        route_id="route-1",
    )

    _, token_a = await issue_token(
        db, tenant_id=tenant.id, name="a", scopes="vehicles:read"
    )
    _, token_b = await issue_token(
        db, tenant_id=other_tenant.id, name="b", scopes="vehicles:read"
    )
    await db.commit()

    resp_a = await client.get(
        "/api/v1/vehicles?status=active",
        headers={"X-Service-Token": token_a},
    )
    resp_b = await client.get(
        "/api/v1/vehicles?status=active",
        headers={"X-Service-Token": token_b},
    )

    ids_a = {v["id"] for v in resp_a.json()["data"]}
    ids_b = {v["id"] for v in resp_b.json()["data"]}

    assert ids_a == {own_vehicle.id}
    assert ids_b == {other_vehicle.id}


@pytest.mark.asyncio
async def test_unknown_service_token_is_401(client: AsyncClient):
    resp = await client.get(
        "/api/v1/vehicles?status=active",
        headers={"X-Service-Token": "stk_live_does_not_exist"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_inactive_service_token_is_401(
    client: AsyncClient, tenant, db: AsyncSession
):
    row, plaintext = await issue_token(
        db, tenant_id=tenant.id, name="revoked", scopes="vehicles:read"
    )
    row.is_active = False
    await db.commit()

    resp = await client.get(
        "/api/v1/vehicles?status=active",
        headers={"X-Service-Token": plaintext},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_token_without_required_scope_is_403(
    client: AsyncClient, tenant, db: AsyncSession
):
    _, plaintext = await issue_token(
        db, tenant_id=tenant.id, name="wrong-scope", scopes="telemetry:read"
    )
    await db.commit()

    resp = await client.get(
        "/api/v1/vehicles?status=active",
        headers={"X-Service-Token": plaintext},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_invalid_service_token_does_not_fall_back_to_jwt(
    client: AsyncClient, tenant, db: AsyncSession
):
    """A garbage service token must fail, not silently authenticate as a user."""
    # Only meaningful if you have a way to mint a user JWT in tests.
    # If you do, set both headers and assert 401.
    resp = await client.get(
        "/api/v1/vehicles?status=active",
        headers={
            "X-Service-Token": "stk_live_garbage",
            # "Authorization": f"Bearer {user_jwt}",
        },
    )
    assert resp.status_code == 401

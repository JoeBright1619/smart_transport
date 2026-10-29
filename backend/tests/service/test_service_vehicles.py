from __future__ import annotations

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.service_token_service import issue_token
from tests.conftest import auth_headers


async def _universal_token(
    db: AsyncSession, scopes: str = "vehicles:read_universal"
) -> str:
    _, plaintext = await issue_token(
        db, universal=True, scopes=scopes, name="pool-test"
    )
    await db.flush()
    return plaintext


# ---------------------------------------------------------------------------
# List endpoint
# ---------------------------------------------------------------------------


async def test_service_list_superadmin_returns_200(
    client: AsyncClient, db: AsyncSession, superadmin, make_tenant, make_vehicle
) -> None:
    tenant = await make_tenant()
    await make_vehicle(tenant_id=tenant.id, status="active")

    resp = await client.get(
        "/api/v1/service/vehicles",
        headers=auth_headers(superadmin),
    )
    assert resp.status_code == 200
    assert resp.json()["data"]


async def test_service_list_universal_token_returns_200(
    client: AsyncClient, db: AsyncSession, make_tenant, make_vehicle
) -> None:
    plaintext = await _universal_token(db)
    tenant = await make_tenant()
    await make_vehicle(tenant_id=tenant.id, status="active")

    resp = await client.get(
        "/api/v1/service/vehicles",
        headers={"X-Service-Token": plaintext},
    )
    assert resp.status_code == 200


async def test_service_list_universal_token_without_scope_returns_403(
    client: AsyncClient, db: AsyncSession
) -> None:
    plaintext = await _universal_token(db, scopes="passengers:read_universal")

    resp = await client.get(
        "/api/v1/service/vehicles",
        headers={"X-Service-Token": plaintext},
    )
    assert resp.status_code == 403


async def test_service_list_tenant_bound_token_returns_403(
    client: AsyncClient, db: AsyncSession, tenant
) -> None:
    _, plaintext = await issue_token(
        db,
        tenant_id=tenant.id,
        scopes="vehicles:read_universal",
        name="bound-test",
    )
    await db.flush()

    resp = await client.get(
        "/api/v1/service/vehicles",
        headers={"X-Service-Token": plaintext},
    )
    assert resp.status_code == 403


async def test_service_list_no_auth_returns_401(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/service/vehicles")
    assert resp.status_code == 401


async def test_service_list_returns_cross_tenant(
    client: AsyncClient, db: AsyncSession, make_tenant, make_vehicle
) -> None:
    plaintext = await _universal_token(db)
    tenant_a = await make_tenant()
    tenant_b = await make_tenant()
    veh_a = await make_vehicle(tenant_id=tenant_a.id, status="active")
    veh_b = await make_vehicle(tenant_id=tenant_b.id, status="active")

    resp = await client.get(
        "/api/v1/service/vehicles?status=active",
        headers={"X-Service-Token": plaintext},
    )
    assert resp.status_code == 200
    ids = {v["id"] for v in resp.json()["data"]}
    assert veh_a.id in ids
    assert veh_b.id in ids


# ---------------------------------------------------------------------------
# Detail endpoint
# ---------------------------------------------------------------------------


async def test_service_detail_returns_tenant_id(
    client: AsyncClient, db: AsyncSession, make_tenant, make_vehicle
) -> None:
    plaintext = await _universal_token(db)
    tenant = await make_tenant()
    vehicle = await make_vehicle(tenant_id=tenant.id)

    resp = await client.get(
        f"/api/v1/service/vehicles/{vehicle.id}",
        headers={"X-Service-Token": plaintext},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["id"] == vehicle.id
    assert body["data"]["tenantId"] == tenant.id


async def test_service_detail_404(client: AsyncClient, db: AsyncSession) -> None:
    plaintext = await _universal_token(db)

    resp = await client.get(
        f"/api/v1/service/vehicles/veh-{uuid.uuid4()}",
        headers={"X-Service-Token": plaintext},
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "vehicle_not_found"


async def test_service_detail_scope_gate(
    client: AsyncClient, db: AsyncSession, make_tenant, make_vehicle
) -> None:
    plaintext = await _universal_token(db, scopes="passengers:read_universal")
    tenant = await make_tenant()
    vehicle = await make_vehicle(tenant_id=tenant.id)

    resp = await client.get(
        f"/api/v1/service/vehicles/{vehicle.id}",
        headers={"X-Service-Token": plaintext},
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Sequence endpoint
# ---------------------------------------------------------------------------


async def test_service_sequence_returns_value(
    client: AsyncClient, db: AsyncSession, make_tenant, make_vehicle
) -> None:
    from app.models.occupancy_event import OccupancyEvent

    plaintext = await _universal_token(db)
    tenant = await make_tenant()
    vehicle = await make_vehicle(tenant_id=tenant.id)

    db.add(
        OccupancyEvent(
            id=f"occ-{uuid.uuid4()}",
            vehicle_id=vehicle.id,
            tenant_id=tenant.id,
            stop_id="stp-1",
            route_id="rt-1",
            onboard=1,
            boardings=1,
            alightings=0,
            arrival_sequence=4,
            position_timestamp=vehicle.updated_at,
            service_timestamp=vehicle.updated_at,
            idempotency_key=f"idem-{uuid.uuid4()}",
        )
    )
    await db.flush()

    resp = await client.get(
        f"/api/v1/service/vehicles/{vehicle.id}/latest-arrival-sequence",
        headers={"X-Service-Token": plaintext},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["arrivalSequence"] == 4


async def test_service_sequence_vehicle_not_found(
    client: AsyncClient, db: AsyncSession
) -> None:
    plaintext = await _universal_token(db)

    resp = await client.get(
        f"/api/v1/service/vehicles/veh-{uuid.uuid4()}/latest-arrival-sequence",
        headers={"X-Service-Token": plaintext},
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "vehicle_not_found"


async def test_service_sequence_no_arrival_records(
    client: AsyncClient, db: AsyncSession, make_tenant, make_vehicle
) -> None:
    plaintext = await _universal_token(db)
    tenant = await make_tenant()
    vehicle = await make_vehicle(tenant_id=tenant.id)

    resp = await client.get(
        f"/api/v1/service/vehicles/{vehicle.id}/latest-arrival-sequence",
        headers={"X-Service-Token": plaintext},
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "no_arrival_records"


async def test_service_sequence_scope_gate(
    client: AsyncClient, db: AsyncSession, make_tenant, make_vehicle
) -> None:
    plaintext = await _universal_token(db, scopes="passengers:read_universal")
    tenant = await make_tenant()
    vehicle = await make_vehicle(tenant_id=tenant.id)

    resp = await client.get(
        f"/api/v1/service/vehicles/{vehicle.id}/latest-arrival-sequence",
        headers={"X-Service-Token": plaintext},
    )
    assert resp.status_code == 403

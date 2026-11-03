from __future__ import annotations

import uuid

import pytest
from fastapi import HTTPException

from app.services import vehicle_service


async def test_get_all_active_vehicles_returns_cross_tenant(
    db, make_tenant, make_vehicle
) -> None:
    tenant_a = await make_tenant()
    tenant_b = await make_tenant()
    veh_a = await make_vehicle(tenant_id=tenant_a.id, status="active")
    veh_b = await make_vehicle(tenant_id=tenant_b.id, status="active")

    vehicles, total = await vehicle_service.get_all_active_vehicles(
        db, "active", page=1, page_size=100
    )
    ids = {v.id for v in vehicles}
    assert veh_a.id in ids
    assert veh_b.id in ids
    assert total >= 2


async def test_get_all_active_vehicles_filters_by_status(
    db, make_tenant, make_vehicle
) -> None:
    tenant = await make_tenant()
    active = await make_vehicle(tenant_id=tenant.id, status="active")
    idle = await make_vehicle(tenant_id=tenant.id, status="idle")

    vehicles, total = await vehicle_service.get_all_active_vehicles(
        db, "active", page=1, page_size=100
    )
    ids = {v.id for v in vehicles}
    assert active.id in ids
    assert idle.id not in ids
    assert total >= 1


async def test_get_all_active_vehicles_excludes_deleted(
    db, make_tenant, make_vehicle
) -> None:
    tenant = await make_tenant()
    alive = await make_vehicle(tenant_id=tenant.id, status="active")
    gone = await make_vehicle(tenant_id=tenant.id, status="active")
    gone.is_deleted = True
    await db.flush()

    vehicles, _ = await vehicle_service.get_all_active_vehicles(
        db, "active", page=1, page_size=100
    )
    ids = {v.id for v in vehicles}
    assert alive.id in ids
    assert gone.id not in ids


async def test_get_vehicle_by_id_any_tenant_returns_vehicle(
    db, make_tenant, make_vehicle
) -> None:
    tenant = await make_tenant()
    vehicle = await make_vehicle(tenant_id=tenant.id)

    got = await vehicle_service.get_vehicle_by_id_any_tenant(db, vehicle.id)
    assert got.id == vehicle.id
    assert got.tenant_id == tenant.id


async def test_get_vehicle_by_id_any_tenant_404(db, make_tenant) -> None:
    # Ensure a tenant exists (some test setups require it for FK integrity,
    # though we don't use it here).
    await make_tenant()

    with pytest.raises(HTTPException) as exc:
        await vehicle_service.get_vehicle_by_id_any_tenant(db, f"veh-{uuid.uuid4()}")
    assert exc.value.status_code == 404
    detail = exc.value.detail
    assert detail["error"]["code"] == "vehicle_not_found"


async def test_get_latest_arrival_sequence_any_tenant_returns_max(
    db, make_tenant, make_vehicle
) -> None:
    """Cross-tenant: seed two occupancy_events for the same vehicle."""
    from app.models.occupancy_event import OccupancyEvent

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
            arrival_sequence=3,
            position_timestamp=vehicle.updated_at,
            service_timestamp=vehicle.updated_at,
            idempotency_key=f"idem-{uuid.uuid4()}",
        )
    )
    db.add(
        OccupancyEvent(
            id=f"occ-{uuid.uuid4()}",
            vehicle_id=vehicle.id,
            tenant_id=tenant.id,
            stop_id="stp-2",
            route_id="rt-1",
            onboard=1,
            boardings=1,
            alightings=0,
            arrival_sequence=7,
            position_timestamp=vehicle.updated_at,
            service_timestamp=vehicle.updated_at,
            idempotency_key=f"idem-{uuid.uuid4()}",
        )
    )
    await db.flush()

    seq = await vehicle_service.get_latest_arrival_sequence_any_tenant(db, vehicle.id)
    assert seq == 7


async def test_get_latest_arrival_sequence_any_tenant_vehicle_not_found(
    db, make_tenant
) -> None:
    await make_tenant()

    with pytest.raises(HTTPException) as exc:
        await vehicle_service.get_latest_arrival_sequence_any_tenant(
            db, f"veh-{uuid.uuid4()}"
        )
    assert exc.value.status_code == 404
    assert exc.value.detail["error"]["code"] == "vehicle_not_found"


async def test_get_latest_arrival_sequence_any_tenant_no_records(
    db, make_tenant, make_vehicle
) -> None:
    tenant = await make_tenant()
    vehicle = await make_vehicle(tenant_id=tenant.id)

    with pytest.raises(HTTPException) as exc:
        await vehicle_service.get_latest_arrival_sequence_any_tenant(db, vehicle.id)
    assert exc.value.status_code == 404
    assert exc.value.detail["error"]["code"] == "no_arrival_records"

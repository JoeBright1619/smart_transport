from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import Principal, require_superadmin_or_universal_service
from app.schemas.common import APIResponse, Meta, PaginatedResponse
from app.schemas.vehicle import LatestArrivalSequenceRead, VehicleRead
from app.services import vehicle_service

router = APIRouter(prefix="/api/v1/service/vehicles", tags=["service"])

_UNIVERSAL_SCOPE = "vehicles:read_universal"


@router.get(
    "",
    response_model=PaginatedResponse[VehicleRead],
    summary="List all active vehicles across tenants",
    description=(
        "Returns vehicles across all tenants. Auth: superadmin JWT, or a "
        "universal service token scoped `vehicles:read_universal`."
    ),
)
async def list_service_vehicles(
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: Principal = Depends(
        require_superadmin_or_universal_service(required_scope=_UNIVERSAL_SCOPE)
    ),
) -> PaginatedResponse[VehicleRead]:
    vehicles, total = await vehicle_service.get_all_active_vehicles(
        db, status_filter, page, page_size
    )
    return PaginatedResponse(
        data=[VehicleRead.model_validate(v) for v in vehicles],
        meta=Meta(total=total, page=page, pageSize=page_size),
    )


@router.get(
    "/{id}",
    response_model=APIResponse[VehicleRead],
    summary="Get a vehicle across tenants",
    description=(
        "Returns a single vehicle regardless of tenant. Auth: superadmin "
        "JWT, or a universal service token scoped `vehicles:read_universal`."
    ),
)
async def get_service_vehicle(
    id: str,
    db: AsyncSession = Depends(get_db),
    _: Principal = Depends(
        require_superadmin_or_universal_service(required_scope=_UNIVERSAL_SCOPE)
    ),
) -> APIResponse[VehicleRead]:
    vehicle = await vehicle_service.get_vehicle_by_id_any_tenant(db, id)
    return APIResponse(data=VehicleRead.model_validate(vehicle))


@router.get(
    "/{id}/latest-arrival-sequence",
    response_model=APIResponse[LatestArrivalSequenceRead],
    summary="Get latest arrival sequence across tenants",
    description=(
        "Returns the highest arrival_sequence for a vehicle across tenants. "
        "Returns 404 with code `no_arrival_records` if the vehicle has no "
        "events yet. Auth: superadmin JWT, or a universal service token "
        "scoped `vehicles:read_universal`."
    ),
)
async def get_service_vehicle_latest_arrival_sequence(
    id: str,
    db: AsyncSession = Depends(get_db),
    _: Principal = Depends(
        require_superadmin_or_universal_service(required_scope=_UNIVERSAL_SCOPE)
    ),
) -> APIResponse[LatestArrivalSequenceRead]:
    sequence = await vehicle_service.get_latest_arrival_sequence_any_tenant(db, id)
    return APIResponse(data=LatestArrivalSequenceRead(arrival_sequence=sequence))

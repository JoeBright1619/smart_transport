from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    get_current_tenant,
    get_current_user,
    get_tenant_or_service,
    require_role,
)
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.common import PaginatedResponse, APIResponse, Meta
from app.schemas.vehicle import (
    VehicleCreate,
    VehicleOccupancyRead,
    VehicleRead,
    VehicleUpdate,
)
from app.services import vehicle_service

router = APIRouter(prefix="/api/v1/vehicles", tags=["vehicles"])


@router.get(
    "",
    response_model=PaginatedResponse[VehicleRead],
    summary="List vehicles",
    description="Returns a paginated list of fleet vehicles. Filter by `status` or `routeId`.",
)
async def list_vehicles(
    status_filter: str | None = Query(default=None, alias="status"),
    route_id: str | None = Query(default=None, alias="routeId"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_tenant_or_service),
):
    vehicles, total = await vehicle_service.get_vehicles(
        db, tenant.id, status_filter, route_id, page, page_size
    )
    return PaginatedResponse(
        data=[VehicleRead.model_validate(v) for v in vehicles],
        meta=Meta(total=total, page=page, pageSize=page_size),
    )


@router.post(
    "",
    response_model=APIResponse[VehicleRead],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "operator"))],
    summary="Create a vehicle",
    description="Adds a new vehicle to the fleet. Registration number must be unique within the tenant.",
)
async def create_vehicle(
    data: VehicleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    vehicle = await vehicle_service.create_vehicle(db, data, tenant.id, current_user.id)
    await db.commit()
    return APIResponse(data=VehicleRead.model_validate(vehicle))


@router.get(
    "/{id}/occupancy",
    response_model=APIResponse[VehicleOccupancyRead],
    dependencies=[
        Depends(require_role("admin", "operator", "dispatcher", "passenger"))
    ],
    summary="Get vehicle occupancy",
    description="Returns current seat occupancy and availability status for a vehicle.",
)
async def get_vehicle_occupancy(
    id: str,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    vehicle = await vehicle_service.get_vehicle_by_id(db, id, tenant.id)
    remaining = max(0, vehicle.seating_capacity - vehicle.current_occupancy)
    if remaining >= 10:
        occ_status = "available"
    elif remaining >= 1:
        occ_status = "nearly_full"
    else:
        occ_status = "full"
    return APIResponse(
        data=VehicleOccupancyRead(
            vehicle_id=vehicle.id,
            seating_capacity=vehicle.seating_capacity,
            current_occupancy=vehicle.current_occupancy,
            remaining_seats=remaining,
            status=occ_status,
        )
    )


@router.get(
    "/{id}",
    response_model=APIResponse[VehicleRead],
    dependencies=[Depends(require_role("admin", "operator", "dispatcher"))],
    summary="Get a vehicle",
    description="Returns a single vehicle including its current GPS location if available.",
)
async def get_vehicle(
    id: str,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    vehicle = await vehicle_service.get_vehicle_by_id(db, id, tenant.id)
    return APIResponse(data=VehicleRead.model_validate(vehicle))


@router.patch(
    "/{id}",
    response_model=APIResponse[VehicleRead],
    dependencies=[Depends(require_role("admin", "operator"))],
    summary="Update a vehicle",
    description="Partially updates vehicle fields such as status, fuel level, assigned route, or driver.",
)
async def update_vehicle(
    id: str,
    data: VehicleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    vehicle = await vehicle_service.update_vehicle(
        db, id, data, tenant.id, current_user.id
    )
    await db.commit()
    await db.refresh(vehicle)
    return APIResponse(data=VehicleRead.model_validate(vehicle))


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("admin"))],
    summary="Delete a vehicle",
    description="Removes a vehicle from the fleet. Returns 409 if the vehicle is currently active.",
)
async def delete_vehicle(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    await vehicle_service.delete_vehicle(db, id, tenant.id, current_user.id)
    await db.commit()

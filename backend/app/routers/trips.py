from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_tenant, get_current_user, require_role
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.common import PaginatedResponse, APIResponse, Meta
from app.schemas.trip import TripCreate, TripRead, TripUpdate
from app.services import trip_service

router = APIRouter(prefix="/api/v1/trips", tags=["trips"])


@router.get(
    "",
    response_model=PaginatedResponse[TripRead],
    dependencies=[Depends(require_role("admin", "operator", "dispatcher"))],
)
async def list_trips(
    status_filter: str | None = Query(default=None, alias="status"),
    vehicle_id: str | None = Query(default=None, alias="vehicleId"),
    driver_id: str | None = Query(default=None, alias="driverId"),
    route_id: str | None = Query(default=None, alias="routeId"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    trips, total = await trip_service.get_trips(
        db, tenant.id, status_filter, vehicle_id, driver_id, route_id, page, page_size
    )
    return PaginatedResponse(
        data=[TripRead.model_validate(t) for t in trips],
        meta=Meta(total=total, page=page, pageSize=page_size),
    )


@router.post(
    "",
    response_model=APIResponse[TripRead],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "dispatcher"))],
)
async def create_trip(
    data: TripCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    async with db.begin():
        trip = await trip_service.create_trip(db, data, tenant.id, current_user.id)
        return APIResponse(data=TripRead.model_validate(trip))


@router.get(
    "/{id}",
    response_model=APIResponse[TripRead],
    dependencies=[Depends(require_role("admin", "operator", "dispatcher"))],
)
async def get_trip(
    id: str,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    trip = await trip_service.get_trip_by_id(db, id, tenant.id)
    return APIResponse(data=TripRead.model_validate(trip))


@router.patch(
    "/{id}",
    response_model=APIResponse[TripRead],
    dependencies=[Depends(require_role("admin", "dispatcher"))],
)
async def update_trip(
    id: str,
    data: TripUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    async with db.begin():
        trip = await trip_service.update_trip(db, id, data, tenant.id, current_user.id)
        return APIResponse(data=TripRead.model_validate(trip))

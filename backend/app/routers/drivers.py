from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_tenant, get_current_user, require_role
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.common import PaginatedResponse, APIResponse, Meta
from app.schemas.driver import DriverCreate, DriverRead, DriverUpdate
from app.services import driver_service

router = APIRouter(prefix="/api/v1/drivers", tags=["drivers"])


@router.get(
    "",
    response_model=PaginatedResponse[DriverRead],
    dependencies=[Depends(require_role("admin", "operator", "dispatcher"))],
    summary="List drivers",
    description="Returns a paginated list of drivers. Filter by `status` (available, on-trip, off-duty).",
)
async def list_drivers(
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    drivers, total = await driver_service.get_drivers(
        db, tenant.id, status_filter, page, page_size
    )
    return PaginatedResponse(
        data=[DriverRead.model_validate(d) for d in drivers],
        meta=Meta(total=total, page=page, pageSize=page_size),
    )


@router.post(
    "",
    response_model=APIResponse[DriverRead],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "operator"))],
    summary="Create a driver",
    description="Registers a new driver with licence and certification details.",
)
async def create_driver(
    data: DriverCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    driver = await driver_service.create_driver(db, data, tenant.id, current_user.id)
    await db.commit()
    return APIResponse(data=DriverRead.model_validate(driver))


@router.get(
    "/{id}",
    response_model=APIResponse[DriverRead],
    dependencies=[Depends(require_role("admin", "operator", "dispatcher"))],
    summary="Get a driver",
    description="Returns a single driver profile including rating and trip count.",
)
async def get_driver(
    id: str,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    driver = await driver_service.get_driver_by_id(db, id, tenant.id)
    return APIResponse(data=DriverRead.model_validate(driver))


@router.patch(
    "/{id}",
    response_model=APIResponse[DriverRead],
    dependencies=[Depends(require_role("admin", "operator"))],
    summary="Update a driver",
    description="Partially updates a driver's profile, status, or assigned vehicle.",
)
async def update_driver(
    id: str,
    data: DriverUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    driver = await driver_service.update_driver(
        db, id, data, tenant.id, current_user.id
    )
    await db.commit()
    return APIResponse(data=DriverRead.model_validate(driver))


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("admin"))],
    summary="Delete a driver",
    description="Removes a driver. Returns 400 if the driver is currently on a trip.",
)
async def delete_driver(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    await driver_service.delete_driver(db, id, tenant.id, current_user.id)
    await db.commit()

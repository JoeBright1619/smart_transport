from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_tenant, get_current_user, require_role
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.common import PaginatedResponse, APIResponse, Meta
from app.schemas.maintenance import (
    MaintenanceCreate,
    MaintenanceRead,
    MaintenanceUpdate,
)
from app.services import maintenance_service

router = APIRouter(prefix="/api/v1/maintenance", tags=["maintenance"])


@router.get(
    "",
    response_model=PaginatedResponse[MaintenanceRead],
    dependencies=[Depends(require_role("admin", "operator"))],
)
async def list_maintenance_records(
    vehicle_id: str | None = Query(default=None, alias="vehicleId"),
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    records, total = await maintenance_service.get_maintenance_records(
        db, tenant.id, vehicle_id, status_filter, page, page_size
    )
    return PaginatedResponse(
        data=[MaintenanceRead.model_validate(r) for r in records],
        meta=Meta(total=total, page=page, pageSize=page_size),
    )


@router.post(
    "",
    response_model=APIResponse[MaintenanceRead],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "operator"))],
)
async def create_maintenance_record(
    data: MaintenanceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    async with db.begin():
        record = await maintenance_service.create_maintenance_record(
            db, data, tenant.id, current_user.id
        )
        return APIResponse(data=MaintenanceRead.model_validate(record))


@router.get(
    "/{id}",
    response_model=APIResponse[MaintenanceRead],
    dependencies=[Depends(require_role("admin", "operator"))],
)
async def get_maintenance_record(
    id: str,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    record = await maintenance_service.get_maintenance_record_by_id(db, id, tenant.id)
    return APIResponse(data=MaintenanceRead.model_validate(record))


@router.patch(
    "/{id}",
    response_model=APIResponse[MaintenanceRead],
    dependencies=[Depends(require_role("admin", "operator"))],
)
async def update_maintenance_record(
    id: str,
    data: MaintenanceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    async with db.begin():
        record = await maintenance_service.update_maintenance_record(
            db, id, data, tenant.id, current_user.id
        )
        return APIResponse(data=MaintenanceRead.model_validate(record))

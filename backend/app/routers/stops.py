from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_tenant, require_role
from app.models.tenant import Tenant
from app.schemas.common import APIResponse
from app.schemas.route import GlobalStopRead, StopCreate, StopUpdate
from app.services import route_service

router = APIRouter(prefix="/api/v1/stops", tags=["routes"])


@router.get(
    "/public",
    response_model=APIResponse[list[GlobalStopRead]],
    summary="List all public stops (cross-tenant)",
    description="Returns all stops across all tenants. No authentication required.",
)
async def list_public_stops(db: AsyncSession = Depends(get_db)):
    stops = await route_service.list_all_stops(db)
    return APIResponse(data=[GlobalStopRead.model_validate(stop) for stop in stops])


@router.get(
    "",
    response_model=APIResponse[list[GlobalStopRead]],
    summary="List global stops",
    description="Returns all permanent stops for the current tenant.",
)
async def list_stops(
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    stops = await route_service.list_stops(db, tenant.id)
    return APIResponse(data=[GlobalStopRead.model_validate(stop) for stop in stops])


@router.post(
    "",
    response_model=APIResponse[GlobalStopRead],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "operator"))],
    summary="Create a global stop",
    description="Creates a permanent tenant stop that can be shared across routes.",
)
async def create_stop(
    data: StopCreate,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    stop = await route_service.create_stop(db, data, tenant.id)
    await db.commit()
    return APIResponse(data=GlobalStopRead.model_validate(stop))


@router.patch(
    "/{id}",
    response_model=APIResponse[GlobalStopRead],
    dependencies=[Depends(require_role("admin", "operator"))],
    summary="Update a global stop",
    description="Renames or moves a stop. Rejects name/coordinate clashes with other stops.",
)
async def update_stop(
    id: str,
    data: StopUpdate,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    stop = await route_service.update_stop(db, id, data, tenant.id)
    await db.commit()
    return APIResponse(data=GlobalStopRead.model_validate(stop))


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("admin", "operator"))],
    summary="Delete a global stop",
    description="Soft-deletes a stop. Rejected while the stop is still used by any route.",
)
async def delete_stop(
    id: str,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    await route_service.delete_stop(db, id, tenant.id)
    await db.commit()

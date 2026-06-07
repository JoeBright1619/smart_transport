from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_tenant, get_current_user, require_role
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.route import GlobalStopRead, StopCreate
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
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    stop = await route_service.create_stop(db, data, tenant.id)
    await db.commit()
    return APIResponse(data=GlobalStopRead.model_validate(stop))

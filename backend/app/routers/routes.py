from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_tenant, get_current_user, require_role
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.common import PaginatedResponse, APIResponse, Meta
from app.schemas.route import RouteCreate, RouteRead, RouteUpdate
from app.services import route_service

router = APIRouter(prefix="/api/v1/routes", tags=["routes"])


@router.get(
    "",
    response_model=PaginatedResponse[RouteRead],
)
async def list_routes(
    is_active: bool | None = Query(default=None, alias="isActive"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    routes, total = await route_service.get_routes(
        db, tenant.id, is_active, page, page_size
    )
    return PaginatedResponse(
        data=[RouteRead.model_validate(r) for r in routes],
        meta=Meta(total=total, page=page, pageSize=page_size),
    )


@router.post(
    "",
    response_model=APIResponse[RouteRead],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "operator"))],
)
async def create_route(
    data: RouteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    async with db.begin():
        route = await route_service.create_route(db, data, tenant.id, current_user.id)
        return APIResponse(data=RouteRead.model_validate(route))


@router.get(
    "/{id}",
    response_model=APIResponse[RouteRead],
)
async def get_route(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    route = await route_service.get_route_by_id(db, id, tenant.id)
    return APIResponse(data=RouteRead.model_validate(route))


@router.patch(
    "/{id}",
    response_model=APIResponse[RouteRead],
    dependencies=[Depends(require_role("admin", "operator"))],
)
async def update_route(
    id: str,
    data: RouteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    async with db.begin():
        route = await route_service.update_route(
            db, id, data, tenant.id, current_user.id
        )
        return APIResponse(data=RouteRead.model_validate(route))


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("admin"))],
)
async def delete_route(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    async with db.begin():
        await route_service.delete_route(db, id, tenant.id, current_user.id)

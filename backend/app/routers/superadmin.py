from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.schemas.common import APIResponse, Meta, PaginatedResponse
from app.schemas.superadmin import (
    ImpersonationResponse,
    PlatformAnalytics,
    SuperadminTenantDetail,
    SuperadminTenantRead,
    SuperadminTenantUpdate,
)
from app.services import superadmin_service

router = APIRouter(tags=["superadmin"])


@router.get(
    "/tenants",
    response_model=PaginatedResponse[SuperadminTenantRead],
    dependencies=[Depends(require_role("superadmin"))],
)
async def list_tenants(
    is_active: bool | None = Query(default=None, alias="isActive"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[SuperadminTenantRead]:
    tenants, total = await superadmin_service.list_tenants(
        db, is_active, page, page_size
    )
    return PaginatedResponse(
        data=tenants,
        meta=Meta(total=total, page=page, pageSize=page_size),
    )


@router.get(
    "/tenants/{id}",
    response_model=APIResponse[SuperadminTenantDetail],
    dependencies=[Depends(require_role("superadmin"))],
)
async def get_tenant(
    id: str,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SuperadminTenantDetail]:
    tenant = await superadmin_service.get_tenant_detail(db, id)
    return APIResponse(data=tenant)


@router.patch(
    "/tenants/{id}",
    response_model=APIResponse[SuperadminTenantDetail],
    dependencies=[Depends(require_role("superadmin"))],
)
async def update_tenant(
    id: str,
    data: SuperadminTenantUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[SuperadminTenantDetail]:
    if data.is_active is None:
        tenant = await superadmin_service.get_tenant_detail(db, id)
        return APIResponse(data=tenant)

    async with db.begin():
        tenant = await superadmin_service.update_tenant_status(
            db,
            id,
            data.is_active,
            current_user.id,
        )
        return APIResponse(data=tenant)


@router.post(
    "/tenants/{id}/impersonate",
    response_model=APIResponse[ImpersonationResponse],
    dependencies=[Depends(require_role("superadmin"))],
)
async def impersonate_tenant(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[ImpersonationResponse]:
    async with db.begin():
        token = await superadmin_service.impersonate_tenant_admin(
            db,
            id,
            current_user.id,
        )
        return APIResponse(data=ImpersonationResponse(access_token=token))


@router.get(
    "/analytics",
    response_model=APIResponse[PlatformAnalytics],
    dependencies=[Depends(require_role("superadmin"))],
)
async def get_analytics(
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PlatformAnalytics]:
    if to_date is None:
        to_date = date.today()
    if from_date is None:
        from_date = to_date - timedelta(days=6)

    analytics = await superadmin_service.get_platform_analytics(
        db,
        from_date,
        to_date,
    )
    return APIResponse(data=analytics)

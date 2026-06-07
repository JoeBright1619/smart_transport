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
from app.schemas.user import UserRead
from app.schemas.analytics import PassengerUsageReport
from app.services import superadmin_service
from app.services import passenger_report_service

router = APIRouter(tags=["superadmin"])


@router.get(
    "/tenants",
    response_model=PaginatedResponse[SuperadminTenantRead],
    dependencies=[Depends(require_role("superadmin"))],
    summary="List all tenants",
    description="Returns a paginated list of every tenant on the platform. Filter by `isActive`.",
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
    summary="Get a tenant",
    description="Returns detailed information about a single tenant including user count and activity stats.",
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
    summary="Suspend or reactivate a tenant",
    description="Sets `isActive` on a tenant. Suspending blocks all users of that tenant from logging in.",
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

    tenant = await superadmin_service.update_tenant_status(
        db,
        id,
        data.is_active,
        current_user.id,
    )
    await db.commit()
    return APIResponse(data=tenant)


@router.post(
    "/tenants/{id}/impersonate",
    response_model=APIResponse[ImpersonationResponse],
    dependencies=[Depends(require_role("superadmin"))],
    summary="Impersonate a tenant admin",
    description=(
        "Issues a short-lived access token scoped to the tenant's first admin user, "
        "allowing a superadmin to act on behalf of that tenant for support purposes."
    ),
)
async def impersonate_tenant(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[ImpersonationResponse]:
    token = await superadmin_service.impersonate_tenant_admin(
        db,
        id,
        current_user.id,
    )
    await db.commit()
    return APIResponse(data=ImpersonationResponse(access_token=token))


@router.get(
    "/passengers",
    response_model=PaginatedResponse[UserRead],
    dependencies=[Depends(require_role("superadmin"))],
    summary="List all passenger accounts",
    description="Returns paginated passenger-role users platform-wide. Includes suspended users.",
)
async def list_passengers(
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[UserRead]:
    passengers, total = await superadmin_service.list_passengers(
        db, search, page, page_size
    )
    return PaginatedResponse(
        data=passengers,
        meta=Meta(total=total, page=page, pageSize=page_size),
    )


@router.post(
    "/passengers/{id}/suspend",
    response_model=APIResponse[UserRead],
    dependencies=[Depends(require_role("superadmin"))],
    summary="Suspend a passenger account",
    description="Sets is_deleted=True on the user. Returns 403 if the user is not a passenger.",
)
async def suspend_passenger(
    id: str,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UserRead]:
    user = await superadmin_service.suspend_passenger(db, id)
    await db.commit()
    return APIResponse(data=user)


@router.post(
    "/passengers/{id}/reactivate",
    response_model=APIResponse[UserRead],
    dependencies=[Depends(require_role("superadmin"))],
    summary="Reactivate a suspended passenger account",
    description="Sets is_deleted=False on the user. Returns 403 if the user is not a passenger.",
)
async def reactivate_passenger(
    id: str,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UserRead]:
    user = await superadmin_service.reactivate_passenger(db, id)
    await db.commit()
    return APIResponse(data=user)


@router.get(
    "/passengers/{id}/report",
    response_model=APIResponse[PassengerUsageReport],
    dependencies=[Depends(require_role("superadmin"))],
    summary="Get passenger transport usage report",
    description=(
        "Returns boarding history, most-used routes/stops, and a trip timeline for a "
        "passenger in the given date range. Returns totalBoardings=0 (not an error) "
        "if no data exists for the period."
    ),
)
async def get_passenger_report(
    id: str,
    date_from: date = Query(alias="date_from"),
    date_to: date = Query(alias="date_to"),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PassengerUsageReport]:
    report = await passenger_report_service.get_passenger_usage_report(
        db, id, date_from, date_to
    )
    return APIResponse(data=report)


@router.get(
    "/analytics",
    response_model=APIResponse[PlatformAnalytics],
    dependencies=[Depends(require_role("superadmin"))],
    summary="Get platform analytics",
    description=(
        "Returns platform-wide metrics: total tenants, users, vehicles, trips, and alerts "
        "across all tenants for the given date window."
    ),
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

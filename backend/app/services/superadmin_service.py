from datetime import date, datetime, time, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.tenant import Tenant
from app.models.trip import Trip
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.superadmin import (
    PlatformAnalytics,
    SuperadminTenantDetail,
    SuperadminTenantRead,
)
from app.services import audit_service


def _error_detail(code: str, message: str) -> dict:
    return {
        "data": None,
        "meta": None,
        "error": {
            "code": code,
            "message": message,
        },
    }


async def _tenant_counts(db: AsyncSession, tenant_id: str) -> tuple[int, int]:
    vehicle_count = await db.scalar(
        select(func.count())
        .select_from(Vehicle)
        .where(Vehicle.tenant_id == tenant_id, Vehicle.is_deleted.is_(False))
    )
    user_count = await db.scalar(
        select(func.count())
        .select_from(User)
        .where(User.tenant_id == tenant_id, User.is_deleted.is_(False))
    )
    return vehicle_count or 0, user_count or 0


async def list_tenants(
    db: AsyncSession,
    is_active: bool | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[SuperadminTenantRead], int]:
    query = select(Tenant)
    if is_active is not None:
        query = query.where(Tenant.is_active.is_(is_active))

    total = await db.scalar(select(func.count()).select_from(query.subquery())) or 0
    tenants = (
        await db.scalars(
            query.order_by(Tenant.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()

    data: list[SuperadminTenantRead] = []
    for tenant in tenants:
        vehicle_count, user_count = await _tenant_counts(db, tenant.id)
        data.append(
            SuperadminTenantRead(
                id=tenant.id,
                name=tenant.name,
                contact_email=tenant.contact_email,
                is_active=tenant.is_active,
                vehicle_count=vehicle_count,
                user_count=user_count,
                created_at=tenant.created_at,
            )
        )

    return data, total


async def get_tenant_detail(db: AsyncSession, tenant_id: str) -> SuperadminTenantDetail:
    tenant = await db.scalar(select(Tenant).where(Tenant.id == tenant_id))
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_error_detail("NOT_FOUND", "Tenant not found"),
        )

    vehicle_count, user_count = await _tenant_counts(db, tenant.id)
    return SuperadminTenantDetail(
        id=tenant.id,
        name=tenant.name,
        contact_email=tenant.contact_email,
        is_active=tenant.is_active,
        vehicle_count=vehicle_count,
        user_count=user_count,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
    )


async def update_tenant_status(
    db: AsyncSession,
    tenant_id: str,
    is_active: bool,
    superadmin_user_id: str,
) -> SuperadminTenantDetail:
    tenant = await db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_error_detail("NOT_FOUND", "Tenant not found"),
        )

    before = {"isActive": tenant.is_active}
    tenant.is_active = is_active
    await db.flush()
    await audit_service.log(
        db,
        superadmin_user_id,
        tenant.id,
        "Tenant",
        tenant.id,
        "update",
        metadata={"before": before, "after": {"isActive": is_active}},
    )
    return await get_tenant_detail(db, tenant_id)


async def impersonate_tenant_admin(
    db: AsyncSession,
    tenant_id: str,
    superadmin_user_id: str,
) -> str:
    tenant = await db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_error_detail("NOT_FOUND", "Tenant not found"),
        )

    admin = await db.scalar(
        select(User).where(
            User.tenant_id == tenant_id,
            User.role == "admin",
            User.is_deleted.is_(False),
        )
    )
    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_error_detail("NOT_FOUND", "Tenant admin not found"),
        )

    await audit_service.log(
        db,
        superadmin_user_id,
        tenant_id,
        "Tenant",
        tenant_id,
        "impersonate",
        metadata={"impersonatedUserId": admin.id},
    )
    return create_access_token(
        {
            "userId": admin.id,
            "tenantId": tenant_id,
            "role": "admin",
            "impersonatedBy": superadmin_user_id,
        },
        expires_delta=timedelta(hours=1),
    )


async def get_platform_analytics(
    db: AsyncSession,
    from_date: date | None = None,
    to_date: date | None = None,
) -> PlatformAnalytics:
    today = date.today()
    start_date = from_date or today
    end_date = to_date or today
    start_dt = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    end_dt = datetime.combine(
        end_date + timedelta(days=1), time.min, tzinfo=timezone.utc
    )

    total_tenants = await db.scalar(select(func.count()).select_from(Tenant)) or 0
    active_tenants = (
        await db.scalar(
            select(func.count()).select_from(Tenant).where(Tenant.is_active.is_(True))
        )
        or 0
    )
    total_vehicles = (
        await db.scalar(
            select(func.count())
            .select_from(Vehicle)
            .where(Vehicle.is_deleted.is_(False))
        )
        or 0
    )
    total_trips_today = (
        await db.scalar(
            select(func.count())
            .select_from(Trip)
            .where(
                Trip.is_deleted.is_(False),
                Trip.scheduled_start >= start_dt,
                Trip.scheduled_start < end_dt,
            )
        )
        or 0
    )
    total_passengers_today = (
        await db.scalar(
            select(func.coalesce(func.sum(Trip.passengers), 0)).where(
                Trip.is_deleted.is_(False),
                Trip.scheduled_start >= start_dt,
                Trip.scheduled_start < end_dt,
            )
        )
        or 0
    )

    return PlatformAnalytics(
        total_tenants=total_tenants,
        active_tenants=active_tenants,
        total_vehicles=total_vehicles,
        total_trips_today=total_trips_today,
        total_passengers_today=total_passengers_today,
    )

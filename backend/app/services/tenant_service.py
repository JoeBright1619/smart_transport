from typing import Any

from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import _raise_error
from app.core.security import hash_password
from app.models.tenant import Tenant
from app.models.user import User


def _get_value(data: Any, field: str) -> Any:
    if isinstance(data, dict):
        return data[field]
    return getattr(data, field)


def _get_optional_value(data: Any, field: str) -> Any:
    if isinstance(data, dict):
        return data.get(field)
    return getattr(data, field, None)


async def create_tenant(db: AsyncSession, data: Any) -> Tenant:
    """Create a transport company tenant and its first admin user atomically."""
    admin_email = _get_value(data, "admin_email").lower()

    async with db.begin():
        existing_user = await db.scalar(select(User).where(User.email == admin_email))
        if existing_user is not None:
            _raise_error(
                status.HTTP_409_CONFLICT,
                "EMAIL_ALREADY_EXISTS",
                "A user with this email already exists",
            )

        tenant = Tenant(
            name=_get_value(data, "company_name"),
            contact_email=_get_value(data, "contact_email").lower(),
            is_active=True,
        )
        db.add(tenant)
        await db.flush()

        admin_user = User(
            tenant_id=tenant.id,
            email=admin_email,
            password_hash=hash_password(_get_value(data, "password")),
            full_name=_get_value(data, "admin_full_name"),
            role="admin",
            phone=_get_optional_value(data, "admin_phone"),
            is_deleted=False,
        )
        db.add(admin_user)

    return tenant


async def get_tenant(db: AsyncSession, tenant_id: str) -> Tenant:
    """Load a transport company tenant by ID or raise a not-found API error."""
    tenant = await db.get(Tenant, tenant_id)
    if tenant is None:
        _raise_error(
            status.HTTP_404_NOT_FOUND,
            "NOT_FOUND",
            "Tenant not found",
        )

    return tenant


async def suspend_tenant(db: AsyncSession, tenant_id: str) -> Tenant:
    """Deactivate a transport company account."""
    tenant = await get_tenant(db, tenant_id)
    tenant.is_active = False
    await db.commit()
    await db.refresh(tenant)
    return tenant


async def reactivate_tenant(db: AsyncSession, tenant_id: str) -> Tenant:
    """Reactivate a transport company account."""
    tenant = await get_tenant(db, tenant_id)
    tenant.is_active = True
    await db.commit()
    await db.refresh(tenant)
    return tenant

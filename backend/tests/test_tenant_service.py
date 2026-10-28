"""Unit tests for TenantService."""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import tenant_service
from app.models.user import User


async def test_create_tenant_with_dict(db: AsyncSession):
    # Test dictionary input
    data = {
        "admin_email": "dictadmin@test.local",
        "company_name": "Dict Transport",
        "contact_email": "contact@dict.local",
        "password": "DictPassword123!",
        "admin_full_name": "Dict Admin User",
        "admin_phone": "+250788888888",
    }

    tenant = await tenant_service.create_tenant(db, data)
    await db.flush()
    assert tenant.id is not None
    assert tenant.name == "Dict Transport"
    assert tenant.contact_email == "contact@dict.local"
    assert tenant.is_active is True

    # Load and verify admin user was created
    admin = await db.get(User, f"user-{tenant.id.split('ten-')[1]}")
    if admin is None:
        # Just retrieve the user by email
        from sqlalchemy import select

        admin = await db.scalar(
            select(User).where(User.email == "dictadmin@test.local")
        )

    assert admin is not None
    assert admin.tenant_id == tenant.id
    assert admin.role == "admin"
    assert admin.phone == "+250788888888"


async def test_create_tenant_duplicate_email(db: AsyncSession):
    data = {
        "admin_email": "dupadmin@test.local",
        "company_name": "Company 1",
        "contact_email": "contact1@test.local",
        "password": "Password123!",
        "admin_full_name": "Admin One",
    }
    await tenant_service.create_tenant(db, data)

    # Try creating with duplicate email
    data2 = {
        "admin_email": "dupadmin@test.local",
        "company_name": "Company 2",
        "contact_email": "contact2@test.local",
        "password": "Password123!",
        "admin_full_name": "Admin Two",
    }
    with pytest.raises(HTTPException) as exc_info:
        await tenant_service.create_tenant(db, data2)

    assert exc_info.value.status_code == 409
    assert isinstance(exc_info.value.detail, dict)
    assert exc_info.value.detail["error"]["code"] == "email_already_exists"


async def test_get_tenant_valid_and_invalid(db: AsyncSession, make_tenant):
    tenant = await make_tenant()

    # Valid get
    loaded = await tenant_service.get_tenant(db, tenant.id)
    assert loaded.id == tenant.id

    # Invalid get
    with pytest.raises(HTTPException) as exc_info:
        await tenant_service.get_tenant(db, "ten-does-not-exist")

    assert exc_info.value.status_code == 404
    assert isinstance(exc_info.value.detail, dict)
    assert exc_info.value.detail["error"]["code"] == "tenant_not_found"


async def test_suspend_and_reactivate_tenant(db: AsyncSession, make_tenant):
    tenant = await make_tenant()
    assert tenant.is_active is True

    # Suspend
    suspended = await tenant_service.suspend_tenant(db, tenant.id)
    assert suspended.is_active is False

    # Reactivate
    reactivated = await tenant_service.reactivate_tenant(db, tenant.id)
    assert reactivated.is_active is True

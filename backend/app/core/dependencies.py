from collections.abc import Callable
from typing import Annotated, Any, NoReturn, Awaitable

from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.gps_device import GPSDevice
from app.core.security import decode_access_token
from app.core.config import settings
from app.models.tenant import Tenant
from app.models.user import User

import hmac

from app.services.service_token_service import has_scope, verify_token

security = HTTPBearer(auto_error=False)


async def authenticate_gps_device(
    token: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GPSDevice:
    """Authenticate an external GPS device using its device token."""

    result = await db.execute(
        select(GPSDevice).where(
            GPSDevice.token == token,
            GPSDevice.is_active.is_(True),
        )
    )
    device = result.scalar_one_or_none()

    if device is None:
        _raise_error(
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHORIZED",
            "Invalid or inactive GPS device",
        )

    return device


def _error_detail(code: str, message: str) -> dict[str, Any]:
    return {
        "data": None,
        "meta": None,
        "error": {
            "code": code,
            "message": message,
        },
    }


def _raise_error(status_code: int, code: str, message: str) -> NoReturn:
    raise HTTPException(
        status_code=status_code,
        detail=_error_detail(code, message),
    )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if credentials is None:
        _raise_error(
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHORIZED",
            "Missing bearer token",
        )

    try:
        if credentials is None:
            _raise_error(
                status.HTTP_401_UNAUTHORIZED,
                "UNAUTHORIZED",
                "Missing bearer token",
            )
        payload = decode_access_token(credentials.credentials)
    except JWTError:
        _raise_error(
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHORIZED",
            "Invalid or expired bearer token",
        )

    user_id = payload.get("userId")
    if not user_id or "tenantId" not in payload or "role" not in payload:
        _raise_error(
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHORIZED",
            "Token is missing required identity claims",
        )

    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.is_deleted.is_(False),
        )
    )
    user = result.scalar_one_or_none()
    if user is None:
        _raise_error(
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHORIZED",
            "Authenticated user was not found",
        )

    token_role = payload.get("role")
    token_tenant_id = payload.get("tenantId")
    if user.role != token_role or user.tenant_id != token_tenant_id:
        _raise_error(
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHORIZED",
            "Token identity does not match the authenticated user",
        )

    return user


async def get_current_tenant(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Tenant:
    if current_user.tenant_id is None:
        _raise_error(
            status.HTTP_403_FORBIDDEN,
            "TENANT_REQUIRED",
            "A tenant-scoped account is required",
        )

    result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        _raise_error(
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHORIZED",
            "Authenticated tenant was not found",
        )

    if not tenant.is_active:
        _raise_error(
            status.HTTP_403_FORBIDDEN,
            "TENANT_INACTIVE",
            "Tenant account is inactive",
        )

    return tenant


def require_role(*roles: str) -> Callable[[User], Awaitable[User]]:
    allowed_roles = set(roles)

    async def dependency(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in allowed_roles:
            _raise_error(
                status.HTTP_403_FORBIDDEN,
                "FORBIDDEN",
                "User does not have permission to access this resource",
            )

        return current_user

    return dependency


# backend/app/core/dependencies.py


def get_tenant_or_service(
    *,
    required_scope: str = "vehicles:read",
) -> Callable[..., Awaitable[Tenant]]:
    """Dependency factory: authenticate as a tenant via service token or JWT.

    Service-token path enforces `required_scope`; user path enforces role.
    """

    async def dependency(
        db: Annotated[AsyncSession, Depends(get_db)],
        x_service_token: Annotated[str | None, Header(alias="X-Service-Token")] = None,
        credentials: Annotated[
            HTTPAuthorizationCredentials | None, Depends(security)
        ] = None,
    ) -> Tenant:
        if x_service_token:
            tenant = await _resolve_service_token(
                db, x_service_token, required_scope=required_scope
            )
            if tenant is not None:
                return tenant
            _raise_error(
                status.HTTP_401_UNAUTHORIZED,
                "UNAUTHORIZED",
                "Invalid or inactive service token",
            )

        user = await get_current_user(credentials=credentials, db=db)
        if user.role not in {"admin", "operator", "dispatcher"}:
            _raise_error(
                status.HTTP_403_FORBIDDEN,
                "FORBIDDEN",
                "User does not have permission to access this resource",
            )
        return await get_current_tenant(current_user=user, db=db)

    return dependency


async def _resolve_service_token(
    db: AsyncSession,
    plaintext: str,
    required_scope: str | None = None,
) -> Tenant | None:
    """Try DB-backed tokens first, then the dev-only bootstrap token."""

    # 1) DB-backed tokens
    row = await verify_token(db, plaintext)
    if row is not None:
        if required_scope and not has_scope(row, required_scope):
            _raise_error(
                status.HTTP_403_FORBIDDEN,
                "FORBIDDEN",
                f"Service token missing required scope: {required_scope}",
            )
        tenant = await _load_active_tenant(db, row.tenant_id)
        if tenant is None:
            _raise_error(
                status.HTTP_403_FORBIDDEN,
                "TENANT_INACTIVE",
                "Service token tenant is inactive or missing",
            )
        return tenant

    # 2) Dev-only bootstrap
    if settings.GPS_SERVICE_TOKEN and hmac.compare_digest(
        plaintext, settings.GPS_SERVICE_TOKEN
    ):
        if not settings.GPS_SERVICE_TENANT_ID:
            _raise_error(
                status.HTTP_401_UNAUTHORIZED,
                "UNAUTHORIZED",
                "GPS_SERVICE_TENANT_ID is not configured for the bootstrap token",
            )
        tenant = await _load_active_tenant(db, settings.GPS_SERVICE_TENANT_ID)
        if tenant is None:
            _raise_error(
                status.HTTP_403_FORBIDDEN,
                "TENANT_INACTIVE",
                "Bootstrap tenant is inactive or missing",
            )
        return tenant

    return None


async def _load_active_tenant(db: AsyncSession, tenant_id: str) -> Tenant | None:
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if tenant is None or not tenant.is_active:
        return None
    return tenant

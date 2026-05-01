from collections.abc import Callable
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.tenant import Tenant
from app.models.user import User

security = HTTPBearer(auto_error=False)


def _error_detail(code: str, message: str) -> dict[str, Any]:
    return {
        "data": None,
        "meta": None,
        "error": {
            "code": code,
            "message": message,
        },
    }


def _raise_error(status_code: int, code: str, message: str) -> None:
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


def require_role(*roles: str) -> Callable[[User], User]:
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

from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services import audit_service

ROLE_RANKS = {
    "superadmin": 100,
    "admin": 50,
    "operator": 10,
    "dispatcher": 10,
    "passenger": 10,
}


def get_role_rank(role: str) -> int:
    return ROLE_RANKS.get(role, 0)


def _error_detail(code: str, message: str) -> dict:
    return {
        "data": None,
        "meta": None,
        "error": {
            "code": code,
            "message": message,
        },
    }


async def get_users(
    db: AsyncSession,
    tenant_id: str,
    role: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[Sequence[User], int]:
    query = select(User).where(User.tenant_id == tenant_id, User.is_deleted.is_(False))
    if role:
        query = query.where(User.role == role)

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = (
        query.offset((page - 1) * page_size)
        .limit(page_size)
        .order_by(User.created_at.desc())
    )
    result = await db.execute(query)
    users = result.scalars().all()

    return users, total


async def get_user_by_id(db: AsyncSession, user_id: str, tenant_id: str) -> User:
    result = await db.execute(
        select(User).where(
            User.id == user_id, User.tenant_id == tenant_id, User.is_deleted.is_(False)
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_error_detail("NOT_FOUND", "User not found"),
        )
    return user


async def create_user(
    db: AsyncSession, data: UserCreate, tenant_id: str, current_user: User
) -> User:
    if get_role_rank(data.role) >= get_role_rank(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_error_detail(
                "FORBIDDEN", "Cannot create user with equal or higher role"
            ),
        )

    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_error_detail("CONFLICT", "Email already exists"),
        )

    user = User(
        tenant_id=tenant_id,
        email=data.email,
        full_name=data.full_name,
        role=data.role,
        phone=data.phone,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    await db.flush()
    await audit_service.log(db, current_user.id, tenant_id, "User", user.id, "create")
    return user


async def update_user(
    db: AsyncSession, user_id: str, data: UserUpdate, tenant_id: str, current_user: User
) -> User:
    user = await get_user_by_id(db, user_id, tenant_id)

    is_own_record = user.id == current_user.id

    if data.role is not None and data.role != user.role:
        if is_own_record:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=_error_detail("FORBIDDEN", "Cannot change own role"),
            )
        if get_role_rank(data.role) >= get_role_rank(current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=_error_detail("FORBIDDEN", "Cannot assign equal or higher role"),
            )
        if get_role_rank(user.role) >= get_role_rank(current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=_error_detail(
                    "FORBIDDEN", "Cannot modify user with equal or higher role"
                ),
            )

    if not is_own_record and current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_error_detail("FORBIDDEN", "Cannot modify other users"),
        )

    if data.full_name is not None:
        user.full_name = data.full_name
    if data.phone is not None:
        user.phone = data.phone
    if data.role is not None:
        user.role = data.role

    await db.flush()
    await audit_service.log(
        db,
        current_user.id,
        tenant_id,
        "User",
        user.id,
        "update",
        metadata=data.model_dump(exclude_unset=True),
    )
    return user


async def delete_user(
    db: AsyncSession, user_id: str, tenant_id: str, current_user: User
) -> None:
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_error_detail("BAD_REQUEST", "Cannot delete own account"),
        )

    user = await get_user_by_id(db, user_id, tenant_id)

    if get_role_rank(user.role) >= get_role_rank(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_error_detail(
                "FORBIDDEN", "Cannot delete user with equal or higher role"
            ),
        )

    user.is_deleted = True
    await db.flush()
    await audit_service.log(
        db, current_user.id, tenant_id, "User", user.id, "soft_delete"
    )

import secrets
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import TYPE_CHECKING, Sequence

from fastapi import status
from jose import JWTError
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import error_codes
from app.core.config import settings
from app.core.errors import _raise_error
from app.core.security import decode_access_token, create_access_token, hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserInviteAccept
from app.services import audit_service

if TYPE_CHECKING:
    from app.models.tenant import Tenant

ROLE_RANKS = {
    "superadmin": 100,
    "admin": 50,
    "operator": 10,
    "dispatcher": 10,
    "passenger": 10,
}


def get_role_rank(role: str) -> int:
    return ROLE_RANKS.get(role, 0)


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
        _raise_error(
            status.HTTP_404_NOT_FOUND,
            error_codes.USER_NOT_FOUND,
            "User not found",
        )
    return user


async def create_user(
    db: AsyncSession,
    data: UserCreate,
    tenant_id: str,
    current_user: User,
    tenant: "Tenant | None" = None,
) -> User:
    if get_role_rank(data.role) > get_role_rank(current_user.role):
        _raise_error(
            status.HTTP_403_FORBIDDEN,
            "FORBIDDEN",
            "Cannot create user with a higher role than your own",
        )

    existing = await db.execute(
        select(User).where(User.email == data.email, User.is_deleted.is_(False))
    )
    if existing.scalar_one_or_none():
        _raise_error(
            status.HTTP_409_CONFLICT,
            "CONFLICT",
            "Email already exists",
        )

    if data.password is not None:
        # Direct create — used by seed scripts and superadmin tooling
        user = User(
            tenant_id=tenant_id,
            email=data.email,
            full_name=data.full_name,
            role=data.role,
            phone=data.phone,
            password_hash=hash_password(data.password),
            status="active",
        )
        db.add(user)
        try:
            await db.flush()
        except IntegrityError:
            _raise_error(
                status.HTTP_409_CONFLICT,
                "CONFLICT",
                "Email already exists",
            )
        await audit_service.log(
            db, current_user.id, tenant_id, "User", user.id, "create"
        )
        return user

    # Invitation flow — no password provided
    user = User(
        tenant_id=tenant_id,
        email=data.email,
        full_name=data.full_name,
        role=data.role,
        phone=data.phone,
        # Unguessable placeholder — replaced when the invite is accepted
        password_hash=hash_password(secrets.token_urlsafe(32)),
        status="invited",
    )
    db.add(user)
    try:
        await db.flush()
    except IntegrityError:
        _raise_error(
            status.HTTP_409_CONFLICT,
            "CONFLICT",
            "Email already exists",
        )
    # Signed JWT valid for 48 h; stored as a hash to allow single-use invalidation
    token = create_access_token(
        {"sub": user.id, "type": "invite"},
        expires_delta=timedelta(hours=48),
    )
    user.invitation_token_hash = sha256(token.encode()).hexdigest()
    user.invitation_expires_at = datetime.now(timezone.utc) + timedelta(hours=48)

    tenant_name = tenant.name if tenant else "Smart Transport"
    invite_link = f"{settings.FRONTEND_URL}/accept-invite?token={token}"

    from app.core.email import send_invitation  # local import avoids circular deps

    send_invitation(
        to_email=user.email,
        to_name=user.full_name,
        invite_link=invite_link,
        tenant_name=tenant_name,
        role=data.role,
    )

    await audit_service.log(db, current_user.id, tenant_id, "User", user.id, "invite")
    return user


async def accept_invitation(
    db: AsyncSession,
    data: UserInviteAccept,
) -> User:
    try:
        payload = decode_access_token(data.token)
    except JWTError:
        _raise_error(
            status.HTTP_400_BAD_REQUEST,
            error_codes.INVALID_TOKEN,
            "Invitation token is invalid or expired",
        )

    if payload.get("type") != "invite":
        _raise_error(
            status.HTTP_400_BAD_REQUEST,
            error_codes.INVALID_TOKEN,
            "Not an invitation token",
        )

    user = await db.scalar(
        select(User).where(User.id == payload.get("sub"), User.is_deleted.is_(False))
    )
    if user is None:
        _raise_error(
            status.HTTP_404_NOT_FOUND,
            error_codes.USER_NOT_FOUND,
            "User not found",
        )
    if user.status != "invited":
        _raise_error(
            status.HTTP_409_CONFLICT,
            "ALREADY_ACCEPTED",
            "Invitation has already been used",
        )
    if user.invitation_token_hash != sha256(data.token.encode()).hexdigest():
        _raise_error(
            status.HTTP_400_BAD_REQUEST,
            error_codes.INVALID_TOKEN,
            "Invitation token is invalid",
        )

    user.password_hash = hash_password(data.new_password)
    user.status = "active"
    user.invitation_token_hash = None
    user.invitation_expires_at = None
    await db.flush()
    await audit_service.log(
        db, user.id, user.tenant_id, "User", user.id, "accept_invite"
    )
    return user


async def update_user(
    db: AsyncSession, user_id: str, data: UserUpdate, tenant_id: str, current_user: User
) -> User:
    user = await get_user_by_id(db, user_id, tenant_id)

    is_own_record = user.id == current_user.id

    if data.role is not None and data.role != user.role:
        if is_own_record:
            _raise_error(
                status.HTTP_403_FORBIDDEN,
                "FORBIDDEN",
                "Cannot change own role",
            )
        if get_role_rank(data.role) > get_role_rank(current_user.role):
            _raise_error(
                status.HTTP_403_FORBIDDEN,
                "FORBIDDEN",
                "Cannot assign a role higher than your own",
            )
        if get_role_rank(user.role) > get_role_rank(current_user.role):
            _raise_error(
                status.HTTP_403_FORBIDDEN,
                "FORBIDDEN",
                "Cannot modify a user with a higher role than your own",
            )

    if not is_own_record and current_user.role not in ["admin", "superadmin"]:
        _raise_error(
            status.HTTP_403_FORBIDDEN,
            "FORBIDDEN",
            "Cannot modify other users",
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
        _raise_error(
            status.HTTP_400_BAD_REQUEST,
            "BAD_REQUEST",
            "Cannot delete own account",
        )

    user = await get_user_by_id(db, user_id, tenant_id)

    if get_role_rank(user.role) > get_role_rank(current_user.role):
        _raise_error(
            status.HTTP_403_FORBIDDEN,
            "FORBIDDEN",
            "Cannot delete a user with a higher role than your own",
        )

    user.is_deleted = True
    await db.flush()
    await audit_service.log(
        db, current_user.id, tenant_id, "User", user.id, "soft_delete"
    )

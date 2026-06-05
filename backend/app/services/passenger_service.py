"""Passenger self-registration, OTP verification, and profile management."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.passenger_profile import PassengerProfile
from app.models.route import Route, Stop
from app.models.user import User
from app.schemas.passenger import (
    PassengerProfileRead,
    PassengerProfileUpdate,
    ResolvedRoute,
    ResolvedStop,
)
from app.services import audit_service


def _error_detail(code: str, message: str) -> dict[str, Any]:
    return {"data": None, "meta": None, "error": {"code": code, "message": message}}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _generate_otp() -> str:
    return str(secrets.randbelow(900000) + 100000)


async def register_passenger(
    db: AsyncSession,
    full_name: str,
    email: str,
    password: str,
    phone: str | None,
) -> User:
    existing = await db.scalar(
        select(User).where(User.email == email.lower(), User.is_deleted.is_(False))
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_error_detail(
                "CONFLICT", "An account with this email already exists"
            ),
        )

    user = User(
        email=email.lower(),
        full_name=full_name,
        phone=phone,
        password_hash=hash_password(password),
        role="passenger",
        status="pending_verification",
        email_verified=False,
    )
    db.add(user)
    try:
        await db.flush()
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_error_detail(
                "CONFLICT", "An account with this email already exists"
            ),
        )

    otp = _generate_otp()
    user.otp_code = sha256(otp.encode()).hexdigest()
    user.otp_expires_at = _utc_now() + timedelta(minutes=15)
    user.otp_resent_at = _utc_now()

    from app.core.email import send_verification

    send_verification(user.email, user.full_name, otp)

    await audit_service.log(db, user.id, None, "User", user.id, "create")
    return user


async def verify_email_otp(db: AsyncSession, email: str, otp: str) -> User:
    user = await db.scalar(
        select(User).where(User.email == email.lower(), User.is_deleted.is_(False))
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_error_detail("NOT_FOUND", "No account found for this email"),
        )

    if user.status != "pending_verification":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_error_detail("ALREADY_VERIFIED", "This email is already verified"),
        )

    if user.otp_expires_at is None or _ensure_aware(user.otp_expires_at) < _utc_now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_error_detail(
                "OTP_EXPIRED", "Verification code has expired — request a new one"
            ),
        )

    if user.otp_code != sha256(otp.encode()).hexdigest():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_error_detail("INVALID_OTP", "Verification code is incorrect"),
        )

    user.email_verified = True
    user.status = "active"
    user.otp_code = None
    user.otp_expires_at = None
    user.otp_resent_at = None
    await db.flush()

    await audit_service.log(
        db,
        user.id,
        None,
        "User",
        user.id,
        "update",
        metadata={"action": "email_verified"},
    )
    return user


async def resend_otp(db: AsyncSession, email: str) -> None:
    user = await db.scalar(
        select(User).where(User.email == email.lower(), User.is_deleted.is_(False))
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_error_detail("NOT_FOUND", "No account found for this email"),
        )

    if user.status != "pending_verification":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_error_detail("ALREADY_VERIFIED", "This email is already verified"),
        )

    if user.otp_resent_at is not None:
        elapsed = (_utc_now() - _ensure_aware(user.otp_resent_at)).total_seconds()
        if elapsed < 60:
            remaining = int(60 - elapsed)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=_error_detail(
                    "TOO_MANY_REQUESTS",
                    f"Please wait {remaining} seconds before requesting another code",
                ),
            )

    otp = _generate_otp()
    user.otp_code = sha256(otp.encode()).hexdigest()
    user.otp_expires_at = _utc_now() + timedelta(minutes=15)
    user.otp_resent_at = _utc_now()
    await db.flush()

    from app.core.email import send_verification

    send_verification(user.email, user.full_name, otp)


# ---------------------------------------------------------------------------
# Passenger profile
# ---------------------------------------------------------------------------


async def create_profile(db: AsyncSession, user_id: str) -> PassengerProfile:
    """Create a blank PassengerProfile for a newly activated passenger."""
    profile = PassengerProfile(user_id=user_id)
    db.add(profile)
    await db.flush()
    return profile


async def _resolve_profile(
    db: AsyncSession, profile: PassengerProfile, user: User
) -> PassengerProfileRead:
    """Enrich a profile with resolved route and stop names."""
    resolved_routes: list[ResolvedRoute] = []
    if profile.preferred_routes:
        rows = await db.execute(
            select(Route.id, Route.name, Route.number, Route.color).where(
                Route.id.in_(profile.preferred_routes), Route.is_deleted.is_(False)
            )
        )
        resolved_routes = [
            ResolvedRoute(id=r.id, name=r.name, number=r.number, color=r.color)
            for r in rows
        ]

    resolved_stops: list[ResolvedStop] = []
    if profile.preferred_stops:
        rows = await db.execute(
            select(Stop.id, Stop.name).where(
                Stop.id.in_(profile.preferred_stops), Stop.is_deleted.is_(False)
            )
        )
        resolved_stops = [ResolvedStop(id=r.id, name=r.name) for r in rows]

    return PassengerProfileRead(
        id=profile.id,
        user_id=profile.user_id,
        full_name=user.full_name,
        email=user.email,
        phone=profile.phone or user.phone,
        preferred_routes=resolved_routes,
        preferred_stops=resolved_stops,
        notify_on_arrival=profile.notify_on_arrival,
        notify_on_delay=profile.notify_on_delay,
        total_trips_recorded=profile.total_trips_recorded,
    )


async def get_profile(db: AsyncSession, user: User) -> PassengerProfileRead:
    profile = await db.scalar(
        select(PassengerProfile).where(PassengerProfile.user_id == user.id)
    )
    if profile is None:
        profile = await create_profile(db, user.id)
        await db.flush()
    return await _resolve_profile(db, profile, user)


async def update_profile(
    db: AsyncSession, user: User, data: PassengerProfileUpdate
) -> PassengerProfileRead:
    profile = await db.scalar(
        select(PassengerProfile).where(PassengerProfile.user_id == user.id)
    )
    if profile is None:
        profile = await create_profile(db, user.id)

    if data.phone is not None:
        profile.phone = data.phone
    if data.preferred_routes is not None:
        profile.preferred_routes = data.preferred_routes
    if data.preferred_stops is not None:
        profile.preferred_stops = data.preferred_stops
    if data.notify_on_arrival is not None:
        profile.notify_on_arrival = data.notify_on_arrival
    if data.notify_on_delay is not None:
        profile.notify_on_delay = data.notify_on_delay

    await db.flush()
    return await _resolve_profile(db, profile, user)


async def list_passengers(
    db: AsyncSession, page: int, page_size: int
) -> tuple[list[dict[str, Any]], int]:
    offset = (page - 1) * page_size
    total = await db.scalar(
        select(func.count())
        .select_from(User)
        .where(User.role == "passenger", User.is_deleted.is_(False))
    )
    rows = await db.execute(
        select(User, PassengerProfile)
        .outerjoin(PassengerProfile, PassengerProfile.user_id == User.id)
        .where(User.role == "passenger", User.is_deleted.is_(False))
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = []
    for user, profile in rows:
        result.append(
            {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "phone": (profile.phone if profile else None) or user.phone,
                "total_trips_recorded": profile.total_trips_recorded if profile else 0,
                "created_at": user.created_at,
            }
        )
    return result, total or 0

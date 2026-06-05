"""Passenger self-registration: register, verify email OTP, resend OTP."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User
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

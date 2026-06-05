"""Tests for passenger self-registration with email OTP (Task 11.2).

Covers:
  - POST /auth/register/passenger
  - POST /auth/verify-email
  - POST /auth/resend-otp
  - Login blocked for pending_verification accounts
"""

from __future__ import annotations

from datetime import timedelta, timezone
from hashlib import sha256
from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# POST /auth/register/passenger
# ---------------------------------------------------------------------------


async def test_register_passenger_returns_201_and_pending_status(client):
    r = await client.post(
        "/auth/register/passenger",
        json={
            "full_name": "Alice Mutoni",
            "email": "alice@test.local",
            "password": "SecurePass1!",
        },
    )
    assert r.status_code == 201
    assert "Verification code" in r.json()["data"]["message"]


async def test_register_passenger_creates_pending_verification_user(
    client, db: AsyncSession
):
    await client.post(
        "/auth/register/passenger",
        json={
            "full_name": "Bob",
            "email": "bob@test.local",
            "password": "SecurePass1!",
        },
    )
    from sqlalchemy import select

    user = await db.scalar(select(User).where(User.email == "bob@test.local"))
    assert user is not None
    assert user.status == "pending_verification"
    assert user.role == "passenger"
    assert user.email_verified is False
    assert user.otp_code is not None
    assert user.otp_expires_at is not None


async def test_register_passenger_duplicate_email_returns_409(client):
    payload = {
        "full_name": "Carol",
        "email": "carol@test.local",
        "password": "SecurePass1!",
    }
    await client.post("/auth/register/passenger", json=payload)
    r = await client.post("/auth/register/passenger", json=payload)
    assert r.status_code == 409


async def test_register_passenger_short_password_returns_422(client):
    r = await client.post(
        "/auth/register/passenger",
        json={"full_name": "Dan", "email": "dan@test.local", "password": "short"},
    )
    assert r.status_code == 422


async def test_register_passenger_missing_email_returns_422(client):
    r = await client.post(
        "/auth/register/passenger",
        json={"full_name": "Eve", "password": "SecurePass1!"},
    )
    assert r.status_code == 422


async def test_register_passenger_with_optional_phone(client):
    r = await client.post(
        "/auth/register/passenger",
        json={
            "full_name": "Frank",
            "email": "frank@test.local",
            "phone": "+250788000001",
            "password": "SecurePass1!",
        },
    )
    assert r.status_code == 201


# ---------------------------------------------------------------------------
# POST /auth/verify-email
# ---------------------------------------------------------------------------


@pytest.fixture
async def pending_user(db: AsyncSession):
    """Create a passenger with pending_verification status and a known OTP."""
    otp = "123456"
    user = User(
        email="pending@test.local",
        full_name="Pending User",
        password_hash="x",
        role="passenger",
        status="pending_verification",
        email_verified=False,
        otp_code=sha256(otp.encode()).hexdigest(),
        otp_expires_at=_utc_now() + timedelta(minutes=15),
        otp_resent_at=_utc_now(),
    )
    db.add(user)
    await db.commit()
    return user, otp


async def test_verify_email_happy_path_returns_200_with_token(client, pending_user):
    _, otp = pending_user
    r = await client.post(
        "/auth/verify-email",
        json={"email": "pending@test.local", "otp": otp},
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert "accessToken" in data
    assert data["user"]["role"] == "passenger"


async def test_verify_email_activates_user(client, pending_user, db: AsyncSession):
    user, otp = pending_user
    await client.post(
        "/auth/verify-email",
        json={"email": "pending@test.local", "otp": otp},
    )
    await db.refresh(user)
    assert user.status == "active"
    assert user.email_verified is True
    assert user.otp_code is None
    assert user.otp_expires_at is None


async def test_verify_email_wrong_otp_returns_400(client, pending_user):
    r = await client.post(
        "/auth/verify-email",
        json={"email": "pending@test.local", "otp": "000000"},
    )
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_OTP"


async def test_verify_email_expired_otp_returns_400(client, db: AsyncSession):
    otp = "654321"
    user = User(
        email="expired@test.local",
        full_name="Expired OTP",
        password_hash="x",
        role="passenger",
        status="pending_verification",
        email_verified=False,
        otp_code=sha256(otp.encode()).hexdigest(),
        otp_expires_at=_utc_now() - timedelta(minutes=1),
        otp_resent_at=_utc_now() - timedelta(minutes=20),
    )
    db.add(user)
    await db.commit()

    r = await client.post(
        "/auth/verify-email",
        json={"email": "expired@test.local", "otp": otp},
    )
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "OTP_EXPIRED"


async def test_verify_email_unknown_email_returns_404(client):
    r = await client.post(
        "/auth/verify-email",
        json={"email": "nobody@test.local", "otp": "123456"},
    )
    assert r.status_code == 404


async def test_verify_email_already_verified_returns_409(
    client, pending_user, db: AsyncSession
):
    user, otp = pending_user
    # First verification succeeds
    await client.post(
        "/auth/verify-email", json={"email": "pending@test.local", "otp": otp}
    )
    # Second attempt on the now-active user must be rejected
    r = await client.post(
        "/auth/verify-email",
        json={"email": "pending@test.local", "otp": otp},
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "ALREADY_VERIFIED"


# ---------------------------------------------------------------------------
# POST /auth/resend-otp
# ---------------------------------------------------------------------------


async def test_resend_otp_happy_path_returns_200(client, db: AsyncSession):
    otp = "111111"
    user = User(
        email="resend@test.local",
        full_name="Resend User",
        password_hash="x",
        role="passenger",
        status="pending_verification",
        email_verified=False,
        otp_code=sha256(otp.encode()).hexdigest(),
        otp_expires_at=_utc_now() + timedelta(minutes=15),
        otp_resent_at=_utc_now() - timedelta(seconds=61),
    )
    db.add(user)
    await db.commit()

    r = await client.post("/auth/resend-otp", json={"email": "resend@test.local"})
    assert r.status_code == 200
    assert "verification code" in r.json()["data"]["message"].lower()


async def test_resend_otp_rate_limit_returns_429(client, db: AsyncSession):
    otp = "222222"
    user = User(
        email="ratelimit@test.local",
        full_name="Rate Limit",
        password_hash="x",
        role="passenger",
        status="pending_verification",
        email_verified=False,
        otp_code=sha256(otp.encode()).hexdigest(),
        otp_expires_at=_utc_now() + timedelta(minutes=15),
        otp_resent_at=_utc_now() - timedelta(seconds=10),
    )
    db.add(user)
    await db.commit()

    r = await client.post("/auth/resend-otp", json={"email": "ratelimit@test.local"})
    assert r.status_code == 429
    assert r.json()["error"]["code"] == "TOO_MANY_REQUESTS"


async def test_resend_otp_unknown_email_returns_404(client):
    r = await client.post("/auth/resend-otp", json={"email": "ghost@test.local"})
    assert r.status_code == 404


async def test_resend_otp_already_verified_returns_409(client, db: AsyncSession):
    db.add(
        User(
            email="verified@test.local",
            full_name="Verified",
            password_hash="x",
            role="passenger",
            status="active",
            email_verified=True,
        )
    )
    await db.commit()

    r = await client.post("/auth/resend-otp", json={"email": "verified@test.local"})
    assert r.status_code == 409


# ---------------------------------------------------------------------------
# Login blocked for unverified accounts
# ---------------------------------------------------------------------------


async def test_login_blocked_for_pending_verification(client, db: AsyncSession):
    from app.core.security import hash_password

    user = User(
        email="unverified@test.local",
        full_name="Unverified",
        password_hash=hash_password("SecurePass1!"),
        role="passenger",
        status="pending_verification",
        email_verified=False,
    )
    db.add(user)
    await db.commit()

    r = await client.post(
        "/auth/login",
        json={"email": "unverified@test.local", "password": "SecurePass1!"},
    )
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "EMAIL_NOT_VERIFIED"

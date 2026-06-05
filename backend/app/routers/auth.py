from datetime import datetime, timedelta, timezone
from hashlib import sha256
from secrets import token_urlsafe
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.models.refresh_token import RefreshToken
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.auth import (
    AuthTenantSummary,
    AuthUserSummary,
    LoginRequest,
    PassengerRegisterRequest,
    RefreshTokenResponse,
    RegisterRequest,
    RegisterResponse,
    ResendOtpRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from app.schemas.common import APIResponse, MessageResponse
from app.services import audit_service, passenger_service, tenant_service

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_TOKEN_COOKIE = "refresh_token"  # nosec


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


def _token_hash(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _auth_user_summary(user: User, tenant: Tenant | None = None) -> AuthUserSummary:
    return AuthUserSummary(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        tenant_id=user.tenant_id,
        tenant_name=tenant.name if tenant else None,
        tenant_email=tenant.contact_email if tenant else None,
        tenant_address=tenant.address if tenant else None,
        tenant_phone=tenant.phone if tenant else None,
        tenant_logo_path=tenant.logo_path if tenant else None,
    )


def _access_token_for_user(user: User, tenant: Tenant | None = None) -> str:
    return create_access_token(
        {
            "userId": user.id,
            "tenantId": user.tenant_id,
            "tenantName": tenant.name if tenant else None,
            "tenantEmail": tenant.contact_email if tenant else None,
            "tenantAddress": tenant.address if tenant else None,
            "tenantPhone": tenant.phone if tenant else None,
            "tenantLogoPath": tenant.logo_path if tenant else None,
            "role": user.role,
        }
    )


def _set_refresh_cookie(response: Response, token: str) -> None:
    max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=max_age,
        path="/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_TOKEN_COOKIE,
        httponly=True,
        samesite="lax",
        path="/auth",
    )


async def _create_refresh_token(db: AsyncSession, user_id: str) -> str:
    raw_token = token_urlsafe(48)
    refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=_token_hash(raw_token),
        expires_at=_utc_now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(refresh_token)
    await db.flush()
    return raw_token


async def _get_active_tenant(db: AsyncSession, tenant_id: str | None) -> Tenant | None:
    if tenant_id is None:
        return None

    tenant = await db.get(Tenant, tenant_id)
    if tenant is None or not tenant.is_active:
        _raise_error(
            status.HTTP_403_FORBIDDEN,
            "TENANT_INACTIVE",
            "Tenant account is inactive",
        )

    return tenant


async def _get_refresh_token_record(db: AsyncSession, raw_token: str) -> RefreshToken:
    refresh_token = await db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == _token_hash(raw_token))
    )
    if refresh_token is None or refresh_token.revoked_at is not None:
        _raise_error(
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHORIZED",
            "Refresh token is invalid",
        )

    if _ensure_aware(refresh_token.expires_at) <= _utc_now():
        refresh_token.revoked_at = _utc_now()
        await db.commit()
        _raise_error(
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHORIZED",
            "Refresh token has expired",
        )

    return refresh_token


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=APIResponse[RegisterResponse],
    summary="Register a new tenant",
    description=(
        "Creates a new tenant organisation together with its first admin user. "
        "Returns an access token and sets a `refresh_token` HttpOnly cookie."
    ),
)
async def register(
    data: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[RegisterResponse]:
    tenant = await tenant_service.create_tenant(db, data)
    user = await db.scalar(select(User).where(User.email == data.admin_email.lower()))
    if user is None:
        _raise_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "INTERNAL_SERVER_ERROR",
            "Registered admin user was not found",
        )

    refresh_token = await _create_refresh_token(db, user.id)
    await audit_service.log(
        db=db,
        user_id=user.id,
        tenant_id=tenant.id,
        entity_type="User",
        entity_id=user.id,
        action_type="login",
        metadata={"source": "register"},
    )
    await db.commit()

    _set_refresh_cookie(response, refresh_token)
    return APIResponse(
        data=RegisterResponse(
            tenant=AuthTenantSummary.model_validate(tenant),
            user=_auth_user_summary(user, tenant),
            access_token=_access_token_for_user(user, tenant),
        )
    )


@router.post(
    "/login",
    response_model=APIResponse[TokenResponse],
    summary="Log in",
    description=(
        "Authenticates a user by email and password. "
        "Returns a short-lived access token and sets a `refresh_token` HttpOnly cookie."
    ),
)
async def login(
    data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TokenResponse]:
    user = await db.scalar(
        select(User).where(
            User.email == data.email.lower(),
            User.is_deleted.is_(False),
        )
    )
    if user is None:
        _raise_error(
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHORIZED",
            "Invalid email or password",
        )

    if user.status == "pending_verification":
        _raise_error(
            status.HTTP_403_FORBIDDEN,
            "EMAIL_NOT_VERIFIED",
            "Please verify your email before logging in",
        )

    if not verify_password(data.password, user.password_hash):
        await audit_service.log(
            db=db,
            user_id=user.id,
            tenant_id=user.tenant_id,
            entity_type="User",
            entity_id=user.id,
            action_type="login_failed",
            metadata={"source": "login"},
        )
        await db.commit()
        _raise_error(
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHORIZED",
            "Invalid email or password",
        )

    tenant = await _get_active_tenant(db, user.tenant_id)
    refresh_token = await _create_refresh_token(db, user.id)
    await audit_service.log(
        db=db,
        user_id=user.id,
        tenant_id=user.tenant_id,
        entity_type="User",
        entity_id=user.id,
        action_type="login",
        metadata={"source": "login"},
    )
    await db.commit()

    _set_refresh_cookie(response, refresh_token)
    return APIResponse(
        data=TokenResponse(
            access_token=_access_token_for_user(user, tenant),
            user=_auth_user_summary(user, tenant),
        )
    )


@router.post(
    "/refresh",
    response_model=APIResponse[RefreshTokenResponse],
    summary="Refresh access token",
    description=(
        "Issues a new access token using the `refresh_token` HttpOnly cookie. "
        "The old refresh token is revoked and a new one is set in the cookie."
    ),
)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[RefreshTokenResponse]:
    raw_token = request.cookies.get(REFRESH_TOKEN_COOKIE)
    if raw_token is None:
        _raise_error(
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHORIZED",
            "Refresh token is missing",
        )

    refresh_token = await _get_refresh_token_record(db, raw_token)
    user = await db.scalar(
        select(User).where(
            User.id == refresh_token.user_id,
            User.is_deleted.is_(False),
        )
    )
    if user is None:
        refresh_token.revoked_at = _utc_now()
        await db.commit()
        _raise_error(
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHORIZED",
            "Refresh token user was not found",
        )

    tenant = await _get_active_tenant(db, user.tenant_id)
    refresh_token.revoked_at = _utc_now()
    new_refresh_token = await _create_refresh_token(db, user.id)
    await db.commit()

    _set_refresh_cookie(response, new_refresh_token)
    return APIResponse(
        data=RefreshTokenResponse(
            access_token=_access_token_for_user(user, tenant),
        )
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Log out",
    description="Revokes the current refresh token and clears the `refresh_token` cookie.",
)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> Response:
    raw_token = request.cookies.get(REFRESH_TOKEN_COOKIE)
    if raw_token is not None:
        refresh_token = await db.scalar(
            select(RefreshToken).where(
                RefreshToken.token_hash == _token_hash(raw_token)
            )
        )
        if refresh_token is not None and refresh_token.revoked_at is None:
            refresh_token.revoked_at = _utc_now()
            await db.commit()

    _clear_refresh_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.post(
    "/register/passenger",
    status_code=status.HTTP_201_CREATED,
    response_model=APIResponse[MessageResponse],
    summary="Passenger self-registration",
    description=(
        "Creates a passenger account and sends a 6-digit OTP to the provided email. "
        "The account is activated only after the OTP is verified."
    ),
)
async def register_passenger(
    data: PassengerRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[MessageResponse]:
    await passenger_service.register_passenger(
        db,
        full_name=data.full_name,
        email=data.email,
        password=data.password,
        phone=data.phone,
    )
    await db.commit()
    return APIResponse(
        data=MessageResponse(message="Verification code sent to your email.")
    )


@router.post(
    "/verify-email",
    response_model=APIResponse[TokenResponse],
    summary="Verify passenger email with OTP",
    description=(
        "Confirms the 6-digit OTP sent at registration. "
        "Activates the account and returns a login token."
    ),
)
async def verify_email(
    data: VerifyEmailRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TokenResponse]:
    user = await passenger_service.verify_email_otp(db, email=data.email, otp=data.otp)
    refresh_token = await _create_refresh_token(db, user.id)
    await audit_service.log(
        db=db,
        user_id=user.id,
        tenant_id=None,
        entity_type="User",
        entity_id=user.id,
        action_type="login",
        metadata={"source": "email_verify"},
    )
    await db.commit()
    _set_refresh_cookie(response, refresh_token)
    return APIResponse(
        data=TokenResponse(
            access_token=_access_token_for_user(user),
            user=_auth_user_summary(user),
        )
    )


@router.post(
    "/resend-otp",
    response_model=APIResponse[MessageResponse],
    summary="Resend email verification OTP",
    description="Re-generates and re-sends the OTP. Rate-limited to once per 60 seconds.",
)
async def resend_otp(
    data: ResendOtpRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[MessageResponse]:
    await passenger_service.resend_otp(db, email=data.email)
    await db.commit()
    return APIResponse(
        data=MessageResponse(
            message="A new verification code has been sent to your email."
        )
    )

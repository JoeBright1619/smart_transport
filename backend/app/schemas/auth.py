from pydantic import Field

from app.schemas.base import APIModel
from app.schemas.user import UserRole


class RegisterRequest(APIModel):
    company_name: str = Field(
        min_length=1,
        max_length=255,
        json_schema_extra={"example": "EcoFleet Ltd"},
    )
    contact_email: str = Field(
        min_length=3,
        max_length=255,
        json_schema_extra={"example": "admin@ecofleet.rw"},
    )
    admin_full_name: str = Field(
        min_length=1,
        max_length=255,
        json_schema_extra={"example": "Jean Claude Mugabo"},
    )
    admin_email: str = Field(
        min_length=3,
        max_length=255,
        json_schema_extra={"example": "jean@ecofleet.rw"},
    )
    admin_phone: str | None = Field(
        default=None,
        max_length=50,
        json_schema_extra={"example": "+250788123456"},
    )
    password: str = Field(
        min_length=8,
        max_length=128,
        json_schema_extra={"example": "SecurePass123!"},
    )


class LoginRequest(APIModel):
    email: str = Field(
        min_length=3,
        max_length=255,
        json_schema_extra={"example": "jean@ecofleet.rw"},
    )
    password: str = Field(
        min_length=1,
        max_length=128,
        json_schema_extra={"example": "SecurePass123!"},
    )


class AuthTenantSummary(APIModel):
    id: str = Field(json_schema_extra={"example": "ten-uuid"})
    name: str = Field(json_schema_extra={"example": "EcoFleet Ltd"})
    is_active: bool = Field(default=True, json_schema_extra={"example": True})


class AuthUserSummary(APIModel):
    id: str = Field(json_schema_extra={"example": "user-uuid"})
    email: str | None = Field(
        default=None, json_schema_extra={"example": "jean@ecofleet.rw"}
    )
    full_name: str | None = Field(
        default=None, json_schema_extra={"example": "Jean Claude Mugabo"}
    )
    role: UserRole = Field(json_schema_extra={"example": "admin"})
    tenant_id: str | None = Field(
        default=None, json_schema_extra={"example": "ten-uuid"}
    )


class RegisterResponse(APIModel):
    tenant: AuthTenantSummary
    user: AuthUserSummary
    access_token: str = Field(json_schema_extra={"example": "<jwt>"})


class TokenResponse(APIModel):
    access_token: str = Field(json_schema_extra={"example": "<jwt>"})
    user: AuthUserSummary


class RefreshTokenResponse(APIModel):
    access_token: str = Field(json_schema_extra={"example": "<new_jwt>"})

from pydantic import Field

from app.schemas.base import APIModel
from app.schemas.user import UserRole
from app.schemas.validators import Email, OptionalPhone, Password, PersonName


class RegisterRequest(APIModel):
    company_name: str = Field(
        min_length=1,
        max_length=255,
        json_schema_extra={"example": "EcoFleet Ltd"},
    )
    contact_email: Email = Field(
        max_length=255,
        json_schema_extra={"example": "admin@ecofleet.rw"},
    )
    admin_full_name: PersonName = Field(
        max_length=255,
        json_schema_extra={"example": "Jean Claude Mugabo"},
    )
    admin_email: Email = Field(
        max_length=255,
        json_schema_extra={"example": "jean@ecofleet.rw"},
    )
    admin_phone: OptionalPhone = Field(
        default=None,
        max_length=50,
        json_schema_extra={"example": "+250788123456"},
    )
    password: Password = Field(
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
    contact_email: str = Field(json_schema_extra={"example": "admin@ecofleet.rw"})
    address: str | None = Field(
        default=None, json_schema_extra={"example": "Kigali, Rwanda"}
    )
    phone: str | None = Field(
        default=None, json_schema_extra={"example": "+250788123456"}
    )
    logo_path: str | None = Field(
        default=None, json_schema_extra={"example": "/tenant-logos/Ecofleet_logo.png"}
    )
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
    tenant_name: str | None = Field(
        default=None, json_schema_extra={"example": "EcoFleet Ltd"}
    )
    tenant_email: str | None = Field(
        default=None, json_schema_extra={"example": "admin@ecofleet.rw"}
    )
    tenant_address: str | None = Field(
        default=None, json_schema_extra={"example": "Kigali, Rwanda"}
    )
    tenant_phone: str | None = Field(
        default=None, json_schema_extra={"example": "+250788123456"}
    )
    tenant_logo_path: str | None = Field(
        default=None, json_schema_extra={"example": "/tenant-logos/Ecofleet_logo.png"}
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


class PassengerRegisterRequest(APIModel):
    full_name: PersonName = Field(
        max_length=255, json_schema_extra={"example": "Alice Mutoni"}
    )
    email: Email = Field(
        max_length=255, json_schema_extra={"example": "alice@example.rw"}
    )
    phone: OptionalPhone = Field(
        default=None, max_length=50, json_schema_extra={"example": "+250788000001"}
    )
    password: Password = Field(
        min_length=8, max_length=128, json_schema_extra={"example": "MyPass123!"}
    )


class VerifyEmailRequest(APIModel):
    email: Email = Field(
        max_length=255, json_schema_extra={"example": "alice@example.rw"}
    )
    otp: str = Field(
        min_length=6, max_length=6, json_schema_extra={"example": "482951"}
    )


class ResendOtpRequest(APIModel):
    email: Email = Field(
        max_length=255, json_schema_extra={"example": "alice@example.rw"}
    )

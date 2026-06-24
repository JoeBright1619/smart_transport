from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas.base import APIModel
from app.schemas.validators import (
    Email,
    OptionalPassword,
    OptionalPersonName,
    OptionalPhone,
    Password,
    PersonName,
)

UserRole = Literal["superadmin", "admin", "operator", "dispatcher", "passenger"]
TenantUserRole = Literal["admin", "operator", "dispatcher", "passenger"]


class UserBase(APIModel):
    full_name: PersonName = Field(
        max_length=255,
        json_schema_extra={"example": "Paul Nkunda"},
    )
    email: Email = Field(
        max_length=255,
        json_schema_extra={"example": "paul@ecofleet.rw"},
    )
    role: TenantUserRole = Field(json_schema_extra={"example": "dispatcher"})
    phone: OptionalPhone = Field(
        default=None,
        max_length=50,
        json_schema_extra={"example": "+250788345678"},
    )


class UserCreate(UserBase):
    # Optional — omit when inviting staff (the invite email provides a link to set it).
    # Provide when seeding or creating accounts that bypass the invitation flow.
    password: OptionalPassword = Field(
        default=None,
        min_length=8,
        max_length=128,
        json_schema_extra={"example": None},
    )


class UserUpdate(APIModel):
    full_name: OptionalPersonName = Field(
        default=None,
        max_length=255,
        json_schema_extra={"example": "Paul Nkunda Jr."},
    )
    phone: OptionalPhone = Field(
        default=None,
        max_length=50,
        json_schema_extra={"example": "+250788345679"},
    )
    role: TenantUserRole | None = Field(
        default=None,
        json_schema_extra={"example": "operator"},
    )


class UserRead(APIModel):
    id: str = Field(json_schema_extra={"example": "user-uuid"})
    tenant_id: str | None = Field(
        default=None, json_schema_extra={"example": "ten-uuid"}
    )
    full_name: str = Field(json_schema_extra={"example": "Marie Umutesi"})
    email: str = Field(json_schema_extra={"example": "marie@ecofleet.rw"})
    role: UserRole = Field(json_schema_extra={"example": "operator"})
    phone: str | None = Field(
        default=None, json_schema_extra={"example": "+250788234567"}
    )
    status: str = Field(default="active", json_schema_extra={"example": "active"})
    is_deleted: bool = Field(default=False, json_schema_extra={"example": False})
    created_at: datetime = Field(json_schema_extra={"example": "2026-04-01T08:00:00Z"})


class UserInviteAccept(APIModel):
    token: str = Field(json_schema_extra={"example": "<invite-jwt>"})
    new_password: Password = Field(
        min_length=8,
        max_length=128,
        json_schema_extra={"example": "NewSecurePass123!"},
    )

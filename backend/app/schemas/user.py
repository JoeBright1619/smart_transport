from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas.base import APIModel

UserRole = Literal["superadmin", "admin", "operator", "dispatcher", "passenger"]
TenantUserRole = Literal["admin", "operator", "dispatcher", "passenger"]


class UserBase(APIModel):
    full_name: str = Field(
        min_length=1,
        max_length=255,
        json_schema_extra={"example": "Paul Nkunda"},
    )
    email: str = Field(
        min_length=3,
        max_length=255,
        json_schema_extra={"example": "paul@kigaliexpress.rw"},
    )
    role: TenantUserRole = Field(json_schema_extra={"example": "dispatcher"})
    phone: str | None = Field(
        default=None,
        max_length=50,
        json_schema_extra={"example": "+250788345678"},
    )


class UserCreate(UserBase):
    password: str = Field(
        min_length=8,
        max_length=128,
        json_schema_extra={"example": "TempPass123!"},
    )


class UserUpdate(APIModel):
    full_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        json_schema_extra={"example": "Paul Nkunda Jr."},
    )
    phone: str | None = Field(
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
    tenant_id: str | None = Field(default=None, json_schema_extra={"example": "ten-uuid"})
    full_name: str = Field(json_schema_extra={"example": "Marie Umutesi"})
    email: str = Field(json_schema_extra={"example": "marie@kigaliexpress.rw"})
    role: UserRole = Field(json_schema_extra={"example": "operator"})
    phone: str | None = Field(default=None, json_schema_extra={"example": "+250788234567"})
    is_deleted: bool = Field(default=False, json_schema_extra={"example": False})
    created_at: datetime = Field(json_schema_extra={"example": "2026-04-01T08:00:00Z"})

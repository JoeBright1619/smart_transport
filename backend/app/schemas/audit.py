from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.base import APIModel


class AuditLogRead(APIModel):
    id: str = Field(json_schema_extra={"example": "audit-uuid"})
    user_id: str = Field(json_schema_extra={"example": "user-uuid"})
    tenant_id: str | None = Field(
        default=None, json_schema_extra={"example": "tenant-uuid"}
    )
    resource_type: str = Field(json_schema_extra={"example": "Route"})
    resource_id: str = Field(json_schema_extra={"example": "route-uuid"})
    action: str = Field(json_schema_extra={"example": "update"})
    metadata: dict[str, Any] | None = Field(default=None)
    created_at: datetime = Field(json_schema_extra={"example": "2026-05-28T10:00:00Z"})

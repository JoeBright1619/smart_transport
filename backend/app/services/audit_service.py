from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog

AuditActionType = Literal["create", "update", "soft_delete", "login", "impersonate"]


async def log(
    db: AsyncSession,
    user_id: str,
    tenant_id: str | None,
    entity_type: str,
    entity_id: str,
    action_type: AuditActionType,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    """Insert an immutable audit log entry for a business mutation."""
    audit_log = AuditLog(
        user_id=user_id,
        tenant_id=tenant_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action_type=action_type,
        metadata_=metadata,
    )
    db.add(audit_log)
    await db.flush()
    return audit_log

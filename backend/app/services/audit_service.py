from typing import Any, Literal, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog

AuditActionType = Literal[
    "create", "update", "soft_delete", "login", "login_failed", "impersonate"
]


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


async def list_logs(
    db: AsyncSession,
    tenant_id: str,
    page: int = 1,
    page_size: int = 50,
    action: str | None = None,
    resource_type: str | None = None,
) -> tuple[Sequence[AuditLog], int]:
    query = select(AuditLog).where(AuditLog.tenant_id == tenant_id)

    if action:
        query = query.where(AuditLog.action_type == action)
    if resource_type:
        query = query.where(AuditLog.entity_type == resource_type)

    total = await db.scalar(select(func.count()).select_from(query.subquery())) or 0
    result = await db.execute(
        query.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return result.scalars().all(), total

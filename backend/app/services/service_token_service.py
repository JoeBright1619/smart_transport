from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service_token import ServiceToken

TOKEN_PREFIX_LIVE = "stk_live_"  # nosec
TOKEN_PREFIX_DEV = "stk_dev_"  # nosec


def hash_token(plaintext: str) -> str:
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


def generate_plaintext_token(dev: bool = False) -> str:
    prefix = TOKEN_PREFIX_DEV if dev else TOKEN_PREFIX_LIVE
    return prefix + secrets.token_urlsafe(32)


async def issue_token(
    db: AsyncSession,
    *,
    tenant_id: str | None = None,
    name: str,
    scopes: str = "vehicles:read",
    universal: bool = False,
    dev: bool = False,
) -> tuple[ServiceToken, str]:
    """Create a service token. Returns (row, plaintext).

    The plaintext is returned exactly once and never stored.

    Pass ``universal=True`` for a tenant-agnostic token (``tenant_id`` is
    set to NULL). Universal tokens bypass tenant resolution and should carry
    a ``*_universal`` scope such as ``passengers:read_universal`` — that scope
    is sensitive and should only be issued to known machine consumers.
    """
    if universal and tenant_id is not None:
        raise ValueError("universal=True is incompatible with tenant_id")
    if not universal and tenant_id is None:
        raise ValueError("tenant_id is required unless universal=True")

    plaintext = generate_plaintext_token(dev=dev)
    row = ServiceToken(
        tenant_id=None if universal else tenant_id,
        name=name,
        token_prefix=plaintext[:16],
        token_hash=hash_token(plaintext),
        scopes=scopes,
        is_active=True,
    )
    db.add(row)
    await db.flush()
    return row, plaintext


async def verify_token(
    db: AsyncSession,
    plaintext: str,
) -> ServiceToken | None:
    """Look up an active service token by plaintext. Updates last_used_at."""
    if not plaintext:
        return None

    digest = hash_token(plaintext)
    result = await db.execute(
        select(ServiceToken).where(
            ServiceToken.token_hash == digest,
            ServiceToken.is_active.is_(True),
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        return None

    row.last_used_at = datetime.now(UTC)
    return row


def has_scope(row: ServiceToken, scope: str) -> bool:
    if not row.scopes:
        return False
    return scope in {s.strip() for s in row.scopes.split(",") if s.strip()}

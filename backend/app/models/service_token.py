from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def generate_service_token_id() -> str:
    return f"stk-{uuid.uuid4()}"


class ServiceToken(Base):
    __tablename__ = "service_tokens"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=generate_service_token_id
    )
    tenant_id: Mapped[str] = mapped_column(
        String, ForeignKey("tenants.id"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String, nullable=False)

    # First 16 chars of the plaintext token (e.g. "stk_live_a1b2c3d4").
    # Safe to display; never sufficient to reconstruct the token.
    token_prefix: Mapped[str] = mapped_column(String, nullable=False)

    # sha256(plaintext) hex digest.
    token_hash: Mapped[str] = mapped_column(
        String, nullable=False, unique=True, index=True
    )

    # Comma-separated scopes, e.g. "vehicles:read".
    scopes: Mapped[str] = mapped_column(String, nullable=False, default="")

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _generate_id() -> str:
    return f"pp-{uuid.uuid4()}"


class PassengerProfile(Base):
    __tablename__ = "passenger_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_generate_id)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id"), unique=True, nullable=False, index=True
    )
    tenant_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("tenants.id"), nullable=True, index=True
    )
    phone: Mapped[str | None] = mapped_column(String, nullable=True)

    # Stored as JSON lists of string IDs
    preferred_routes: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    preferred_stops: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    notify_on_arrival: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    notify_on_delay: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notification_threshold_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=10, server_default="10"
    )
    total_trips_recorded: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

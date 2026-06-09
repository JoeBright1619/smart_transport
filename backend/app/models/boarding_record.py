from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _generate_id() -> str:
    return f"brd-{uuid.uuid4()}"


class BoardingRecord(Base):
    __tablename__ = "boarding_records"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_generate_id)
    trip_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("trips.id"), nullable=True
    )
    route_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("routes.id"), nullable=True
    )
    stop_id: Mapped[str] = mapped_column(String, ForeignKey("stops.id"), nullable=False)
    passenger_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("users.id"), nullable=True
    )
    event_type: Mapped[str] = mapped_column(
        Enum("boarded", "alighted", name="boarding_event_type_enum"),
        nullable=False,
    )
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    occupancy_after: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tenant_id: Mapped[str] = mapped_column(
        String, ForeignKey("tenants.id"), nullable=False
    )

    __table_args__ = (
        Index("idx_boarding_tenant", "tenant_id"),
        Index("idx_boarding_stop", "stop_id"),
        Index("idx_boarding_trip", "trip_id"),
        Index("idx_boarding_route", "route_id"),
        Index("idx_boarding_passenger", "passenger_id"),
        Index("idx_boarding_recorded_at", "recorded_at"),
    )

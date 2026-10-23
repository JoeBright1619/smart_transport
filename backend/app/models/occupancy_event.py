"""SQLAlchemy model for ``occupancy_events`` — append-only aggregate log.

One row per occupancy event received from passenger_service. Written by the
backend's occupancy MQTT subscriber; see design §8. ``idempotency_key`` is
UNIQUE and is what makes ingestion idempotent: an ``INSERT ... ON CONFLICT
(idempotency_key) DO NOTHING`` is the guard for the entire transaction
(children, vehicle update, revenue, alert).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.boarding_passenger_event import BoardingPassengerEvent


def generate_occupancy_event_id() -> str:
    return f"occ-{uuid.uuid4()}"


class OccupancyEvent(Base):
    __tablename__ = "occupancy_events"
    __table_args__ = (
        Index(
            "ix_occupancy_events_vehicle_id_arrival_sequence",
            "vehicle_id",
            "arrival_sequence",
        ),
        Index(
            "ix_occupancy_events_tenant_id_position_timestamp",
            "tenant_id",
            "position_timestamp",
        ),
        CheckConstraint(
            "arrival_sequence >= 0", name="ck_occ_events_arrival_seq_nonneg"
        ),
        CheckConstraint("boardings >= 0", name="ck_occ_events_boardings_nonneg"),
        CheckConstraint("alightings >= 0", name="ck_occ_events_alightings_nonneg"),
        CheckConstraint("onboard >= 0", name="ck_occ_events_onboard_nonneg"),
        CheckConstraint("revenue_delta >= 0", name="ck_occ_events_revenue_nonneg"),
    )

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=generate_occupancy_event_id
    )
    tenant_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    vehicle_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("vehicles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    stop_id: Mapped[str] = mapped_column(String, nullable=False)
    route_id: Mapped[str] = mapped_column(String, nullable=False)
    arrival_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    boardings: Mapped[int] = mapped_column(Integer, nullable=False)
    alightings: Mapped[int] = mapped_column(Integer, nullable=False)
    onboard: Mapped[int] = mapped_column(Integer, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    position_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    service_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revenue_delta: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        server_default=func.now(),
        nullable=False,
    )

    passenger_events: Mapped[list[BoardingPassengerEvent]] = relationship(
        "BoardingPassengerEvent",
        back_populates="occupancy_event",
        cascade="all, delete-orphan",
    )

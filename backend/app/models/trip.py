from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.driver import Driver
    from app.models.route import Route
    from app.models.tenant import Tenant
    from app.models.vehicle import Vehicle


def generate_trip_id() -> str:
    return f"trip-{uuid.uuid4()}"


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_trip_id)
    tenant_id: Mapped[str] = mapped_column(
        String, ForeignKey("tenants.id"), nullable=False
    )

    vehicle_id: Mapped[str] = mapped_column(
        String, ForeignKey("vehicles.id"), nullable=False
    )
    route_id: Mapped[str] = mapped_column(
        String, ForeignKey("routes.id"), nullable=False
    )
    driver_id: Mapped[str] = mapped_column(
        String, ForeignKey("drivers.id"), nullable=False
    )

    scheduled_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    actual_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    scheduled_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    actual_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        Enum("scheduled", "active", "completed", "cancelled", name="trip_status_enum"),
        nullable=False,
        default="scheduled",
    )
    passengers: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    delay: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        server_default=func.now(),
        nullable=False,
    )

    tenant: Mapped["Tenant"] = relationship("Tenant")
    vehicle: Mapped["Vehicle"] = relationship("Vehicle")
    route: Mapped["Route"] = relationship("Route")
    driver: Mapped["Driver"] = relationship("Driver")

    __table_args__ = (
        Index("idx_trips_tenant_id", "tenant_id"),
        Index("idx_trips_status", "status"),
    )

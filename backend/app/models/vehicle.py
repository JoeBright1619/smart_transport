from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    func,
    ForeignKey,
    Enum,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.tenant import Tenant


def generate_vehicle_id() -> str:
    return f"veh-{uuid.uuid4()}"


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=generate_vehicle_id
    )
    tenant_id: Mapped[str] = mapped_column(
        String, ForeignKey("tenants.id"), nullable=False
    )

    registration_number: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    seating_capacity: Mapped[int] = mapped_column(
        Integer, nullable=False, default=45, server_default="45"
    )
    current_occupancy: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    status: Mapped[str] = mapped_column(
        Enum("active", "idle", "maintenance", "offline", name="vehicle_status_enum"),
        nullable=False,
        default="offline",
    )

    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    speed: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    heading: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    fuel: Mapped[int | None] = mapped_column(Integer, nullable=True, default=100)

    engine_status: Mapped[str] = mapped_column(
        Enum("good", "warning", "critical", name="engine_status_enum"),
        nullable=False,
        default="good",
    )

    # These models aren't created yet, so they must use strings for FK targets
    route_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("routes.id"), nullable=True
    )
    driver_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("drivers.id"), nullable=True
    )

    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships can be added later once the other models exist, or using string refs
    tenant: Mapped["Tenant"] = relationship("Tenant")

    __table_args__ = (
        Index("idx_vehicles_tenant_id", "tenant_id"),
        Index("idx_vehicles_status", "status"),
    )

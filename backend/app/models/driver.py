from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.vehicle import Vehicle


def generate_driver_id() -> str:
    return f"drv-{uuid.uuid4()}"


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=generate_driver_id
    )
    tenant_id: Mapped[str] = mapped_column(
        String, ForeignKey("tenants.id"), nullable=False
    )

    name: Mapped[str] = mapped_column(String, nullable=False)
    license_number: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str] = mapped_column(String, nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_trips: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        Enum("available", "on-trip", "off-duty", name="driver_status_enum"),
        nullable=False,
        default="available",
    )
    vehicle_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("vehicles.id"), nullable=True
    )
    certification_expiry: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

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
    vehicle: Mapped["Vehicle | None"] = relationship("Vehicle")

    __table_args__ = (Index("idx_drivers_tenant_id", "tenant_id"),)

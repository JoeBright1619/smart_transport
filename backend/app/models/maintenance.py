import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def generate_maintenance_id() -> str:
    return f"maint-{uuid.uuid4()}"


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_maintenance_id)
    tenant_id: Mapped[str] = mapped_column(String, ForeignKey("tenants.id"), nullable=False)
    vehicle_id: Mapped[str] = mapped_column(String, ForeignKey("vehicles.id"), nullable=False)

    type: Mapped[str] = mapped_column(
        Enum("routine", "repair", "inspection", name="maintenance_type_enum"),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(String, nullable=False)
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    completed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(
        Enum("scheduled", "in-progress", "completed", name="maintenance_status_enum"),
        nullable=False,
        default="scheduled",
    )
    next_due: Mapped[date | None] = mapped_column(Date, nullable=True)

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

    __table_args__ = (Index("idx_maintenance_records_tenant_id", "tenant_id"),)

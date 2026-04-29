import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def generate_alert_id() -> str:
    return f"alert-{uuid.uuid4()}"


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_alert_id)
    tenant_id: Mapped[str] = mapped_column(String, ForeignKey("tenants.id"), nullable=False)

    type: Mapped[str] = mapped_column(
        Enum("delay", "breakdown", "maintenance", "geofence", "speeding", "info", name="alert_type_enum"),
        nullable=False,
    )
    severity: Mapped[str] = mapped_column(
        Enum("low", "medium", "high", "critical", name="alert_severity_enum"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    vehicle_id: Mapped[str | None] = mapped_column(String, ForeignKey("vehicles.id"), nullable=True)
    driver_id: Mapped[str | None] = mapped_column(String, ForeignKey("drivers.id"), nullable=True)
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    tenant: Mapped["Tenant"] = relationship("Tenant")
    vehicle: Mapped["Vehicle | None"] = relationship("Vehicle")
    driver: Mapped["Driver | None"] = relationship("Driver")

    __table_args__ = (
        Index("idx_alerts_tenant_id", "tenant_id"),
        Index("idx_alerts_is_acknowledged", "is_acknowledged"),
    )

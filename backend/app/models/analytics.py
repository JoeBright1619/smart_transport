from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, Float, ForeignKey, String, func, Index, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.tenant import Tenant


def generate_analytics_id() -> str:
    return f"analytics-{uuid.uuid4()}"


class AnalyticsRecord(Base):
    __tablename__ = "analytics"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=generate_analytics_id
    )
    tenant_id: Mapped[str] = mapped_column(
        String, ForeignKey("tenants.id"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)

    total_fuel_consumption: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    total_revenue: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    tenant: Mapped["Tenant"] = relationship("Tenant")

    __table_args__ = (
        Index("idx_analytics_tenant_date", "tenant_id", "date", unique=True),
    )

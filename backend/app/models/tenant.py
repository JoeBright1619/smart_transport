import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, func, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

def generate_tenant_id() -> str:
    return f"ten-{uuid.uuid4()}"

def generate_sub_id() -> str:
    return f"sub-{uuid.uuid4()}"

class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_tenant_id)
    name: Mapped[str] = mapped_column(String, nullable=False)
    contact_email: Mapped[str] = mapped_column(String, nullable=False)
    billing_email: Mapped[str] = mapped_column(String, nullable=True)
    subscription_tier: Mapped[str] = mapped_column(
        Enum("starter", "pro", "enterprise", name="subscription_tier_enum"), 
        nullable=False, 
        default="starter"
    )
    vehicle_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    trial_ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)

    subscriptions: Mapped[list["Subscription"]] = relationship("Subscription", back_populates="tenant", cascade="all, delete-orphan")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_sub_id)
    tenant_id: Mapped[str] = mapped_column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    tier: Mapped[str] = mapped_column(
        Enum("starter", "pro", "enterprise", name="subscription_tier_enum", create_type=False), 
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        Enum("active", "past_due", "cancelled", "trialing", name="subscription_status_enum"), 
        nullable=False
    )
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    external_billing_id: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="subscriptions")

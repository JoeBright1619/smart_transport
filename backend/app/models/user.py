import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

def generate_user_id() -> str:
    return f"user-{uuid.uuid4()}"

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_user_id)
    # nullable=True because superadmin has NO tenant_id
    tenant_id: Mapped[str | None] = mapped_column(String, ForeignKey("tenants.id"), nullable=True, index=True)
    
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    
    role: Mapped[str] = mapped_column(
        Enum("superadmin", "admin", "operator", "dispatcher", "passenger", name="user_role_enum"), 
        nullable=False
    )
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)

    tenant: Mapped["Tenant"] = relationship("Tenant")

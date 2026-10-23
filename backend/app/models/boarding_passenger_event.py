"""SQLAlchemy model for ``boarding_passenger_events`` — per-passenger audit log.

Child rows of ``occupancy_events``, one per real passenger per direction,
derived from the parent event's ``boarded_passenger_ids`` /
``alighted_passenger_ids``. Rows are inserted in the same transaction as the
parent and only when the parent insert actually inserted (design §8).
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.occupancy_event import OccupancyEvent


def generate_boarding_passenger_event_id() -> str:
    return f"bpe-{uuid.uuid4()}"


class BoardingEventType(str, enum.Enum):
    boarded = "boarded"
    alighted = "alighted"


class BoardingPassengerEvent(Base):
    __tablename__ = "boarding_passenger_events"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=generate_boarding_passenger_event_id
    )
    occupancy_event_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("occupancy_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    passenger_id: Mapped[str | None] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    event_type: Mapped[BoardingEventType] = mapped_column(
        Enum(BoardingEventType, name="boarding_event_type"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    occupancy_event: Mapped[OccupancyEvent] = relationship(
        "OccupancyEvent", back_populates="passenger_events"
    )

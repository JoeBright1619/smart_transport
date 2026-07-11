"""Helpers for assigning realistic GPS positions to fleet vehicles.

Every vehicle retains a GPS position at all times — including when ``offline`` — so the
fleet's last-known location is always available (e.g. after an accident or a disabled
tracker). ``offline`` means "not transmitting / last-known", not "no position". A newly
created or repositioned vehicle is placed near one of its tenant's bus stops.
"""

from __future__ import annotations

import random

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.route import Stop
from app.models.vehicle import Vehicle

# ~100 m of jitter so co-located vehicles don't stack on the exact same coordinate.
_JITTER_DEGREES = 0.0009


async def starting_position_near_stop(
    db: AsyncSession, tenant_id: str
) -> tuple[float, float] | None:
    """Return a ``(lat, lng)`` near a random active bus stop for the tenant.

    Returns ``None`` when the tenant has no stops yet — the caller leaves GPS unset in
    that case (there is no meaningful position to invent).
    """
    stops = (
        await db.execute(
            select(Stop.lat, Stop.lng).where(
                Stop.tenant_id == tenant_id, Stop.is_deleted.is_(False)
            )
        )
    ).all()
    if not stops:
        return None

    stop = random.choice(stops)  # nosec B311
    lat = stop.lat + random.uniform(-_JITTER_DEGREES, _JITTER_DEGREES)  # nosec B311
    lng = stop.lng + random.uniform(-_JITTER_DEGREES, _JITTER_DEGREES)  # nosec B311
    return lat, lng


async def ensure_vehicle_position(db: AsyncSession, vehicle: Vehicle) -> None:
    """Assign a starting position to a vehicle that has none, if the tenant has stops.

    GPS is never cleared once set — this only fills in a missing position.
    """
    if vehicle.lat is not None and vehicle.lng is not None:
        return
    position = await starting_position_near_stop(db, vehicle.tenant_id)
    if position is not None:
        vehicle.lat, vehicle.lng = position

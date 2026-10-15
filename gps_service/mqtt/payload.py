"""Adapter from internal VehicleState to the MQTT wire format.

The wire format is owned by the backend's GPSPositionUpdate schema
(backend/app/schemas/gps.py). If that schema changes, this module must
change with it.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from gps_service.models.gps_data import VehicleState


def to_backend_payload(
    vehicle: VehicleState,
    timestamp: datetime,
) -> dict[str, Any]:
    """Build the payload shape expected by the backend's GPSPositionUpdate.

    The backend owns this wire contract. Keep this mapping in one place so
    the contract is visible and testable.
    """
    return {
        "vehicle_id": vehicle.vehicle_id,
        "device_id": vehicle.device_id,
        "tenant_id": vehicle.tenant_id,
        "lat": float(vehicle.latitude),
        "lng": float(vehicle.longitude),
        "speed": _clamp_int(vehicle.speed, 0, 200),
        "heading": _wrap_heading(vehicle.heading),
        "fuel": _clamp_int(vehicle.fuel, 0, 100),
        "engine_status": vehicle.engine_status,
        "timestamp": timestamp.isoformat(),
        "source": "gps_service",
    }


def _clamp_int(value: float, lo: int, hi: int) -> int:
    return max(lo, min(hi, int(round(value))))


def _wrap_heading(value: float) -> int:
    return int(round(value)) % 360

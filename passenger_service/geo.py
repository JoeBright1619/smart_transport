"""Geodesy helpers for passenger_service.

Mirrors the haversine implementation in gps_service's geo/math.py.
Copied rather than imported — services do not share code (architectural
boundary, project context §1). Keep in sync if the algorithm changes.

Only `haversine_distance` is copied: passenger_service needs distance
for stop detection and route-distance computation. The bearing /
move_along_bearing helpers from gps_service are not used here and are
deliberately omitted.
"""

from __future__ import annotations

from math import atan2, cos, radians, sin, sqrt

EARTH_RADIUS_M = 6_371_000


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate the great-circle distance between two WGS84 points in metres."""
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lng = radians(lng2 - lng1)

    a = (
        sin(delta_lat / 2) ** 2
        + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lng / 2) ** 2
    )
    return EARTH_RADIUS_M * 2 * atan2(sqrt(a), sqrt(1 - a))

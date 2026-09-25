from math import asin, atan2, cos, degrees, radians, sin, sqrt

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


def bearing(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate the initial compass bearing from point 1 to point 2 in degrees."""
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lng = radians(lng2 - lng1)

    x = cos(lat2_rad) * sin(delta_lng)
    y = cos(lat1_rad) * sin(lat2_rad) - sin(lat1_rad) * cos(lat2_rad) * cos(delta_lng)
    return (degrees(atan2(x, y)) + 360) % 360


def move_along_bearing(
    lat: float, lng: float, bearing_deg: float, distance_m: float
) -> tuple[float, float]:
    """Move a WGS84 point along a compass bearing by a distance in metres."""
    angular_distance = distance_m / EARTH_RADIUS_M
    bearing_rad = radians(bearing_deg)
    lat_rad = radians(lat)
    lng_rad = radians(lng)

    new_lat_rad = asin(
        sin(lat_rad) * cos(angular_distance)
        + cos(lat_rad) * sin(angular_distance) * cos(bearing_rad)
    )
    new_lng_rad = lng_rad + atan2(
        sin(bearing_rad) * sin(angular_distance) * cos(lat_rad),
        cos(angular_distance) - sin(lat_rad) * sin(new_lat_rad),
    )

    return degrees(new_lat_rad), degrees(new_lng_rad)

from math import asin, cos, radians, sin, sqrt

EARTH_RADIUS_KM = 6371.0


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate the great-circle distance between two WGS84 points in kilometers."""
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lng = radians(lng2 - lng1)

    a = (
        sin(delta_lat / 2) ** 2
        + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lng / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))

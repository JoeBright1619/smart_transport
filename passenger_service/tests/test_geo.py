from __future__ import annotations

import pytest

from passenger_service.geo import EARTH_RADIUS_M, haversine_distance


def test_identical_points_zero_distance() -> None:
    assert haversine_distance(0.0, 0.0, 0.0, 0.0) == 0.0


def test_nairobi_to_mombasa_roughly_correct() -> None:
    """Nairobi (-1.2921, 36.8219) → Mombasa (-4.0435, 39.6682) is
    ~440 km great-circle. Assert within 1%."""
    d = haversine_distance(-1.2921, 36.8219, -4.0435, 39.6682)
    assert 435_000 <= d <= 445_000


def test_one_degree_latitude_at_equator_is_about_111km() -> None:
    # 1° of latitude on a sphere of EARTH_RADIUS_M = 2π*R/360 ≈ 111194.9 m
    d = haversine_distance(0.0, 0.0, 1.0, 0.0)
    assert 111_000 <= d <= 111_500


def test_one_degree_longitude_at_equator_is_about_111km() -> None:
    d = haversine_distance(0.0, 0.0, 0.0, 1.0)
    assert 111_000 <= d <= 111_500


def test_distance_is_symmetric() -> None:
    a = haversine_distance(10.0, 20.0, -5.0, -15.0)
    b = haversine_distance(-5.0, -15.0, 10.0, 20.0)
    assert a == pytest.approx(b, rel=1e-12)


def test_earth_radius_constant() -> None:
    assert EARTH_RADIUS_M == 6_371_000

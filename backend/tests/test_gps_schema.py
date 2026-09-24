"""Tests for GPSPositionUpdate schema validation."""

from __future__ import annotations

import pytest

from app.schemas.gps import GPSPositionUpdate


class TestGPSPositionSchema:
    """Tests for GPSPositionUpdate schema validation."""

    def test_valid_gps_position(self):
        """Test valid GPS position passes validation."""
        data = {
            "vehicle_id": "veh-123",
            "tenant_id": "tenant-1",
            "lat": -1.9536,
            "lng": 30.0606,
            "speed": 45,
            "heading": 90,
            "fuel": 85,
            "engine_status": "good",
            "timestamp": "2026-09-24T09:00:00Z",
        }

        position = GPSPositionUpdate(**data)
        assert position.vehicle_id == "veh-123"
        assert position.lat == -1.9536
        assert position.speed == 45

    def test_latitude_bounds_validation(self):
        """Test latitude must be between -90 and 90."""
        data = {
            "vehicle_id": "veh-123",
            "tenant_id": "tenant-1",
            "lat": 91.0,
            "lng": 30.0606,
            "speed": 45,
            "heading": 90,
            "fuel": 85,
            "engine_status": "good",
            "timestamp": "2026-09-24T09:00:00Z",
        }

        with pytest.raises(Exception):
            GPSPositionUpdate(**data)

    def test_longitude_bounds_validation(self):
        """Test longitude must be between -180 and 180."""
        data = {
            "vehicle_id": "veh-123",
            "tenant_id": "tenant-1",
            "lat": -1.9536,
            "lng": 181.0,
            "speed": 45,
            "heading": 90,
            "fuel": 85,
            "engine_status": "good",
            "timestamp": "2026-09-24T09:00:00Z",
        }

        with pytest.raises(Exception):
            GPSPositionUpdate(**data)

    def test_speed_bounds_validation(self):
        """Test speed must be between 0 and 200."""
        data = {
            "vehicle_id": "veh-123",
            "tenant_id": "tenant-1",
            "lat": -1.9536,
            "lng": 30.0606,
            "speed": 250,
            "heading": 90,
            "fuel": 85,
            "engine_status": "good",
            "timestamp": "2026-09-24T09:00:00Z",
        }

        with pytest.raises(Exception):
            GPSPositionUpdate(**data)

    def test_heading_bounds_validation(self):
        """Test heading must be between 0 and 359."""
        data = {
            "vehicle_id": "veh-123",
            "tenant_id": "tenant-1",
            "lat": -1.9536,
            "lng": 30.0606,
            "speed": 45,
            "heading": 360,
            "fuel": 85,
            "engine_status": "good",
            "timestamp": "2026-09-24T09:00:00Z",
        }

        with pytest.raises(Exception):
            GPSPositionUpdate(**data)

    def test_fuel_bounds_validation(self):
        """Test fuel must be between 0 and 100."""
        data = {
            "vehicle_id": "veh-123",
            "tenant_id": "tenant-1",
            "lat": -1.9536,
            "lng": 30.0606,
            "speed": 45,
            "heading": 90,
            "fuel": 150,
            "engine_status": "good",
            "timestamp": "2026-09-24T09:00:00Z",
        }

        with pytest.raises(Exception):
            GPSPositionUpdate(**data)

    def test_engine_status_values(self):
        """Test valid engine status values."""
        for status in ["good", "warning", "critical"]:
            data = {
                "vehicle_id": "veh-123",
                "tenant_id": "tenant-1",
                "lat": -1.9536,
                "lng": 30.0606,
                "speed": 45,
                "heading": 90,
                "fuel": 85,
                "engine_status": status,
                "timestamp": "2026-09-24T09:00:00Z",
            }
            position = GPSPositionUpdate(**data)
            assert position.engine_status == status

    def test_optional_fields_have_defaults(self):
        """Test optional fields have correct defaults."""
        data = {
            "vehicle_id": "veh-123",
            "tenant_id": "tenant-1",
            "lat": -1.9536,
            "lng": 30.0606,
            "speed": 45,
            "heading": 90,
            "fuel": 85,
            "timestamp": "2026-09-24T09:00:00Z",
        }

        position = GPSPositionUpdate(**data)
        assert position.engine_status == "good"
        assert position.source == "gps_service"

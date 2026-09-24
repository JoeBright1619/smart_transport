"""Tests for route tracking service."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.route_tracking_service import (
    RouteEventType,
    RouteEvent,
    track_gps_update,
    clear_vehicle_state,
)


class TestRouteTrackingService:
    """Unit tests for route tracking service."""

    @pytest.fixture
    def mock_vehicle(self):
        """Create a mock vehicle with route."""
        vehicle = MagicMock()
        vehicle.id = "veh-test-001"
        vehicle.tenant_id = "tenant-1"
        vehicle.route_id = "route-1"
        vehicle.completed_loops = 0
        vehicle.planned_loops = 2
        return vehicle

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return AsyncMock()

    async def test_track_gps_update_no_route(self, mock_db_session, mock_vehicle):
        """Test GPS tracking with no route_id returns empty events."""
        mock_vehicle.route_id = None

        gps_data = {"lat": -1.9536, "lng": 30.0606, "speed": 45}

        events = await track_gps_update(mock_db_session, mock_vehicle, gps_data)

        assert events == []

    async def test_track_gps_update_short_route(self, mock_db_session, mock_vehicle):
        """Test GPS tracking with route having less than 2 stops."""
        mock_vehicle.route_id = "route-1"

        gps_data = {"lat": -1.9536, "lng": 30.0606, "speed": 45}

        with patch(
            "app.services.route_tracking_service._get_route_stops"
        ) as mock_stops:
            mock_stops.return_value = []
            events = await track_gps_update(mock_db_session, mock_vehicle, gps_data)

            assert events == []

    async def test_track_gps_update_vehicle_not_at_stop(
        self, mock_db_session, mock_vehicle
    ):
        """Test GPS update when vehicle is not near a stop."""
        mock_vehicle.route_id = "route-1"

        gps_data = {"lat": -1.9536, "lng": 30.0606, "speed": 45}

        mock_stop = MagicMock()
        mock_stop.id = "stop-1"
        mock_stop.name = "Terminal"
        mock_stop.lat = -1.9536
        mock_stop.lng = 30.0606

        with patch(
            "app.services.route_tracking_service._get_route_stops"
        ) as mock_stops:
            mock_stops.return_value = [mock_stop]
            with patch("app.core.geo_math.haversine_distance", return_value=50):
                events = await track_gps_update(mock_db_session, mock_vehicle, gps_data)

                assert events == []

    async def test_track_gps_update_stop_arrival(self, mock_db_session, mock_vehicle):
        """Test GPS update triggers stop arrival event."""
        mock_vehicle.route_id = "route-1"

        gps_data = {"lat": -1.9536, "lng": 30.0606, "speed": 0}

        mock_stop = MagicMock()
        mock_stop.id = "stop-1"
        mock_stop.name = "Terminal"
        mock_stop.lat = -1.9536
        mock_stop.lng = 30.0606

        mock_stop2 = MagicMock()
        mock_stop2.id = "stop-2"
        mock_stop2.name = "Next Stop"
        mock_stop2.lat = -1.9540
        mock_stop2.lng = 30.0610

        with patch(
            "app.services.route_tracking_service._get_route_stops"
        ) as mock_stops:
            # Need at least 2 stops for route tracking
            mock_stops.return_value = [mock_stop, mock_stop2]
            with patch("app.core.geo_math.haversine_distance", return_value=20):
                with patch("app.services.route_tracking_service._handle_stop_arrival"):
                    events = await track_gps_update(
                        mock_db_session, mock_vehicle, gps_data
                    )

                    assert len(events) == 1
                    assert events[0].event_type == RouteEventType.STOP_ARRIVAL
                    assert events[0].vehicle_id == "veh-test-001"
                    assert events[0].stop_id == "stop-1"


class TestRouteEvent:
    """Tests for RouteEvent dataclass."""

    def test_route_event_creation(self):
        """Test RouteEvent can be created."""
        now = datetime.now(timezone.utc)
        event = RouteEvent(
            event_type=RouteEventType.STOP_ARRIVAL,
            vehicle_id="veh-123",
            tenant_id="tenant-1",
            stop_id="stop-1",
            stop_name="Terminal",
            stop_index=0,
            timestamp=now,
        )

        assert event.event_type == RouteEventType.STOP_ARRIVAL
        assert event.vehicle_id == "veh-123"
        assert event.stop_name == "Terminal"
        assert event.timestamp == now


class TestVehicleState:
    """Tests for vehicle state management."""

    def test_clear_vehicle_state(self):
        """Test clearing vehicle state."""
        from app.services.route_tracking_service import _vehicle_states

        _vehicle_states["veh-test"] = {"next_stop_index": 0}

        result = clear_vehicle_state("veh-test")

        assert result is True
        assert "veh-test" not in _vehicle_states

    def test_clear_vehicle_state_nonexistent(self):
        """Test clearing non-existent vehicle state."""

        result = clear_vehicle_state("nonexistent-veh")

        assert result is False

    def test_clear_all_states(self):
        """Test clearing all states."""
        from app.services.route_tracking_service import (
            clear_all_states,
            _vehicle_states,
            _route_stops_cache,
        )

        _vehicle_states["veh-1"] = {}
        _vehicle_states["veh-2"] = {}
        _route_stops_cache["route-1"] = []

        clear_all_states()

        assert len(_vehicle_states) == 0
        assert len(_route_stops_cache) == 0

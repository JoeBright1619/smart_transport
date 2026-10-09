from __future__ import annotations

from random import uniform
from gps_service.geo.math import bearing, haversine_distance, move_along_bearing
from gps_service.models.gps_data import RouteStop, VehicleState
from gps_service.simulator.state_manager import SimulationState
from gps_service.simulator.congestion import update_congestion


TICK_SECONDS = 5
OPEN_ROAD_SPEED = 35
DECEL_START_DIST = 250

FUEL_CONSUMPTION_PCT_PER_KM = 2.5

DWELL_TICKS = 2

CONGESTION_CHANCE = 0.015
CONGESTION_MIN_TICKS = 24
CONGESTION_MAX_TICKS = 48
CONGESTION_SPEED = 7
DELAY_ALERT_MINUTES = 2


class SimulationEngine:
    """Calculate vehicle movement for each simulation tick."""

    def advance_vehicle(
        self,
        vehicle: VehicleState,
        stops: list[RouteStop],
        state: SimulationState,
    ) -> VehicleState | None:
        """Advance a vehicle one simulation tick toward its next route stop."""

        if len(stops) < 2:
            return None

        # Only advance vehicles whose operational status allows movement.
        # Engine health (`engine_status`) is metadata and does not gate
        # simulation (policy B).
        if vehicle.status != "active":
            return vehicle

        next_stop_index = max(
            0,
            min(state.next_stop_index, len(stops) - 1),
        )
        state.next_stop_index = next_stop_index

        # Bus pauses at each stop before moving again.
        if state.dwell_remaining > 0:
            state.dwell_remaining -= 1
            vehicle.speed = 0

            return vehicle

        target = stops[state.next_stop_index]

        distance_m = haversine_distance(
            vehicle.latitude,
            vehicle.longitude,
            target.latitude,
            target.longitude,
        )

        current_speed = vehicle.speed

        in_congestion, _delay_crossed = update_congestion(state)

        if in_congestion:
            new_speed = CONGESTION_SPEED
        elif current_speed == 0:
            new_speed = min(OPEN_ROAD_SPEED, current_speed + 8)
        elif distance_m < DECEL_START_DIST:
            ratio = distance_m / DECEL_START_DIST
            new_speed = max(5, int(OPEN_ROAD_SPEED * ratio))
        else:
            variation = round(uniform(-3, 3))  # nosec B311
            new_speed = max(
                15,
                min(50, current_speed + variation),
            )

        vehicle.speed = new_speed

        advance_m = new_speed * 1000 / 3600 * TICK_SECONDS

        if distance_m <= advance_m or distance_m < 30:
            vehicle.latitude = target.latitude
            vehicle.longitude = target.longitude
            vehicle.speed = 0

            current_stop_index = state.next_stop_index

            state.next_stop_index = (current_stop_index + 1) % len(stops)

            state.dwell_remaining = DWELL_TICKS

        else:
            current_bearing = bearing(
                vehicle.latitude,
                vehicle.longitude,
                target.latitude,
                target.longitude,
            )

            vehicle.latitude, vehicle.longitude = move_along_bearing(
                vehicle.latitude,
                vehicle.longitude,
                current_bearing,
                advance_m,
            )

            vehicle.heading = current_bearing

        # Fuel is consumed according to the distance travelled during this tick.
        km_this_tick = new_speed * TICK_SECONDS / 3600
        fuel_drop = km_this_tick * FUEL_CONSUMPTION_PCT_PER_KM

        new_fuel = max(
            0,
            vehicle.fuel - fuel_drop,
        )

        vehicle.fuel = new_fuel

        return vehicle

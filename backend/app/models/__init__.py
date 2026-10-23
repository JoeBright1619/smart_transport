from app.models.alert import Alert
from app.models.analytics import AnalyticsRecord
from app.models.audit_log import AuditLog
from app.models.boarding_passenger_event import BoardingPassengerEvent
from app.models.boarding_record import BoardingRecord
from app.models.driver import Driver
from app.models.gps_device import GPSDevice
from app.models.maintenance import MaintenanceRecord
from app.models.occupancy_event import OccupancyEvent
from app.models.passenger_profile import PassengerProfile
from app.models.refresh_token import RefreshToken
from app.models.route import Route, RouteStop, Stop
from app.models.service_token import ServiceToken
from app.models.tenant import Tenant
from app.models.telemetry import Telemetry
from app.models.trip import Trip
from app.models.user import User
from app.models.vehicle import Vehicle

__all__ = [
    "Alert",
    "AnalyticsRecord",
    "AuditLog",
    "BoardingPassengerEvent",
    "BoardingRecord",
    "Driver",
    "GPSDevice",
    "MaintenanceRecord",
    "OccupancyEvent",
    "PassengerProfile",
    "RefreshToken",
    "Route",
    "RouteStop",
    "ServiceToken",
    "Stop",
    "Tenant",
    "Telemetry",
    "Trip",
    "User",
    "Vehicle",
]

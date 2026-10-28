"""Named error codes for the API's canonical error envelope.

Codes appear as ``{"error": {"code": ..., "message": ...}}`` on the wire
and are the client-facing discriminator for programmatic error handling.
Renaming a code requires coordinating with any client that matches on it
(the frontend, integrations, or API consumers).

Convention: snake_case. Codes are grouped by kind below.

Generic HTTP-class codes (``FORBIDDEN``, ``CONFLICT``, ``BAD_REQUEST``,
``UNAUTHORIZED``) are deliberately not named here. They remain as literal
strings in call sites: the client outcome is identical regardless of
casing, so renaming them would break consumers without adding information.
"""

from __future__ import annotations

# 404 — resource not found
STOP_NOT_FOUND = "stop_not_found"
DRIVER_NOT_FOUND = "driver_not_found"
ROUTE_NOT_FOUND = "route_not_found"
TRIP_NOT_FOUND = "trip_not_found"
USER_NOT_FOUND = "user_not_found"
TENANT_NOT_FOUND = "tenant_not_found"
TENANT_ADMIN_NOT_FOUND = "tenant_admin_not_found"
ALERT_NOT_FOUND = "alert_not_found"
MAINTENANCE_RECORD_NOT_FOUND = "maintenance_record_not_found"
PASSENGER_NOT_FOUND = "passenger_not_found"
ACCOUNT_NOT_FOUND = "account_not_found"
STOPS_NOT_FOUND = "stops_not_found"  # plural — bulk stop lookup
VEHICLE_NOT_FOUND = "vehicle_not_found"
NO_ARRIVAL_RECORDS = "no_arrival_records"

# Specific conditions
EMAIL_ALREADY_EXISTS = "email_already_exists"
ALREADY_VERIFIED = "already_verified"
INVALID_OTP = "invalid_otp"
INVALID_TOKEN = "invalid_token"  # nosec B105
TENANT_INACTIVE = "tenant_inactive"
TENANT_REQUIRED = "tenant_required"

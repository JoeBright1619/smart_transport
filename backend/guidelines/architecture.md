# Backend Architecture

## Overview

This FastAPI backend is one of three Smart Transport services. It provides the
tenant-scoped REST API, persistence, alerting, and WebSocket delivery layer; it
consumes vehicle-position and occupancy events from MQTT but does not simulate
vehicles or passengers. The canonical system-wide topology is documented in
[`docs/Architecture.md`](../../docs/Architecture.md).

---

## Backend Responsibilities

- Expose tenant-scoped REST endpoints and universal cross-service endpoints.
- Authenticate users, superadmins, and service tokens; enforce tenant isolation.
- Persist vehicle position, telemetry, occupancy, passenger-event, and analytics data.
- Generate alert records from GPS and occupancy ingestion.
- Publish tenant-scoped tracking and occupancy messages through Redis and WebSockets.
- Run scheduled-trip activation and startup trip reconciliation.

The separate services own their simulations and publish their outputs; this
backend owns the durable operational record and API-facing representation.

---

## Full Directory Layout

```
backend/
├── main.py                         # FastAPI app factory, lifespan, router registration
├── Dockerfile                      # Backend container image
├── requirements.txt                # Python dependencies
├── alembic.ini                     # Alembic configuration
├── .env.example                    # Local environment template
├── alembic/
│   ├── env.py                      # Migration environment
│   ├── script.py.mako              # Alembic revision template
│   └── versions/                   # Ordered schema migrations
│       ├── 20260429_0001_initial_schema.py
│       ├── 20260507_0002_add_telemetry_table.py
│       ├── 20260521_0003_add_analytics_table.py
│       ├── 20260528_0004_add_login_failed_audit_action.py
│       ├── 20260529_0005_add_tenant_contact_fields.py
│       ├── 20260529_0006_add_tenant_logo_path.py
│       ├── 20260603_0007_add_user_invitation_fields.py
│       ├── 20260603_0008_add_invite_audit_actions.py
│       ├── 20260603_0009_partial_unique_index_users_email.py
│       ├── 20260605_0010_add_otp_verification_fields.py
│       ├── 20260605_0011_add_passenger_profile.py
│       ├── 20260605_0012_add_boarding_records.py
│       ├── 20260606_0013_add_vehicle_capacity_fields.py
│       ├── 20260606_0014_add_capacity_alert_type.py
│       ├── 20260608_0015_add_notification_threshold_to_passenger_profile.py
│       ├── 20260609_0016_add_route_id_to_boarding_records.py
│       ├── 20260609_0017_drop_vehicle_capacity_column.py
│       ├── 20260712_0018_add_vehicle_journey_loops.py
│       ├── 20260712_0019_add_trip_start_delay.py
│       ├── 20260923_d7ef32e5127d_add_gps_devices_table.py
│       ├── 20261008_dbef00630ff8_add_service_tokens_table.py
│       ├── 20261023_be9989e72aa2_add_occupancy_tables.py
│       └── 20261027_4ab6d44381f4_make_service_tokens_tenant_id_nullable.py
├── app/
│   ├── __init__.py
│   ├── core/                       # Settings, database, auth, shared helpers
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── dependencies.py
│   │   ├── email.py
│   │   ├── error_codes.py
│   │   ├── errors.py
│   │   ├── geo.py
│   │   ├── geo_math.py
│   │   ├── mqtt_client.py
│   │   ├── security.py
│   │   └── seed.py
│   ├── crud/
│   │   └── analytics.py            # Daily analytics upsert/query helpers
│   ├── models/                     # SQLAlchemy ORM models
│   │   ├── alert.py, analytics.py, audit_log.py
│   │   ├── boarding_passenger_event.py, boarding_record.py
│   │   ├── driver.py, gps_device.py, maintenance.py
│   │   ├── occupancy_event.py, passenger_profile.py, refresh_token.py
│   │   ├── route.py, service_token.py, telemetry.py, tenant.py
│   │   └── trip.py, user.py, vehicle.py
│   ├── routers/                    # Thin HTTP route definitions
│   │   ├── alerts.py, analytics.py, arrivals.py, audit.py, auth.py
│   │   ├── boardings.py, drivers.py, maintenance.py, passengers.py
│   │   ├── routes.py, stops.py, trips.py, users.py, vehicles.py
│   │   └── service.py, service_routes.py, service_vehicles.py, superadmin.py
│   ├── schemas/                    # Pydantic input/output contracts
│   │   ├── alert.py, analytics.py, arrival.py, audit.py, auth.py
│   │   ├── base.py, boarding.py, common.py, driver.py, gps.py
│   │   ├── maintenance.py, occupancy.py, passenger.py, route.py
│   │   ├── service.py, superadmin.py, trip.py, user.py, validators.py
│   │   └── vehicle.py
│   ├── services/                   # Business logic and MQTT consumers
│   │   ├── alert_service.py, analytics_service.py, arrival_service.py
│   │   ├── audit_service.py, boarding_service.py, driver_service.py
│   │   ├── fleet_assignment.py, fleet_position.py, gps_handler.py
│   │   ├── gps_mqtt_subscriber.py, maintenance_service.py
│   │   ├── occupancy_mqtt_subscriber.py, occupancy_service.py
│   │   ├── passenger_report_service.py, passenger_service.py
│   │   ├── passenger_stats_service.py, route_progress.py, route_service.py
│   │   ├── route_tracking_service.py, service_token_service.py
│   │   └── superadmin_service.py, tenant_service.py, trip_auto_start.py,
│   │       trip_reconciliation.py, trip_service.py, user_service.py,
│   │       vehicle_service.py
│   └── websocket/                  # Tenant-scoped WebSocket delivery
│       ├── manager.py
│       ├── route_trip_records.py
│       └── tracking.py
└── tests/                          # 59 Python test files
```

`models/`, `routers/`, `schemas/`, and `services/` each contain an
`__init__.py` package marker in addition to the files shown above.

---

## Router Registration in `main.py`

`create_app()` registers these routers in this order:

```python
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(passengers.router)
app.include_router(boardings.router)
app.include_router(vehicles.router)
app.include_router(routes.router)
app.include_router(stops.router)
app.include_router(trips.router)
app.include_router(drivers.router)
app.include_router(maintenance.router)
app.include_router(alerts.router)
app.include_router(analytics.router)
app.include_router(arrivals.router)
app.include_router(audit.router)
app.include_router(superadmin.router, prefix="/superadmin")
app.include_router(tracking.router)
app.include_router(service.router)
app.include_router(service_routes.router)
app.include_router(service_vehicles.router)
```

The lifespan connects the shared MQTT client, starts `GPSMQTTSubscriber` and
`OccupancyMQTTSubscriber`, checks migration state, reconciles orphaned trips,
and starts the scheduled-trip auto-start loop. Shutdown disconnects MQTT,
stops the loop, and disposes the database engine.

---

## MQTT Topics and Data Flow

The backend subscribes to `gps/+/+/position` and passes validated messages to
`gps_handler.process_gps_update`, which updates the current vehicle position
and writes telemetry. It also subscribes to `gps/+/+/occupancy`; the
idempotent `occupancy_service.record` writer persists occupancy and
per-passenger events, updates current occupancy and analytics revenue, and can
create a capacity alert. WebSocket tracking reads persisted state and publishes
tenant-scoped messages through Redis. See the canonical
[system-wide real-time flow](../../docs/Architecture.md#6-real-time-architecture).

---

## Known Gaps

The known post-cutover regression is the `atStop` field in WebSocket
`vehicle_update` messages, which is currently always empty. For the restore
note, alert coverage, and the restart and loop-counting limitations, see
[Known Gaps after Phase 5](../../docs/Architecture.md#12-known-gaps-after-phase-5).

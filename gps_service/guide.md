> [!NOTE]
> **Agent Best Practices:** Always follow these best practices when implementing tasks:
> - **Write tests before or alongside implementation** — Don't wait until the end to test. Test each phase as you complete it. See "Testing Tasks" section below.
> - **Keep code minimal and focused** — Minimize files to the absolute minimum lines needed. Remove dead code, unused imports, and redundant abstractions. Prefer simple, direct solutions over complex ones. This is more efficient to write, read, debug, and maintain.
> - **Single responsibility per file** — Each file should have one clear purpose and not grow beyond 250-300 lines. Split files when they need more than one responsibility.
> - **Incremental testing strategy** — For backend tasks: unit tests for new functions, integration tests for component interactions, run full suite before marking complete. For frontend: verify builds, check TypeScript types.
> - **No test follow-ups** — If tests are needed, write them in the same commit/PR as the implementation.
> - **Run verification gates after every task** — Never assume everything works. Always run the full test suite (`./.venv/Scripts/python.exe -m pytest -q`) before declaring a task complete.
> - **Clear commit messages** — Use the exact commit messages provided in the task description to maintain traceability.
> - **Stop and report after each task** — Report implementation details, decisions, problems, and ask for confirmation before proceeding.

# GPS Service Extraction Guide

**Current Task:** Phase 4, Task 4.3: Add vehicle management endpoints

---

## Overview

This guide tracks the extraction of GPS simulation logic from the backend into a standalone MQTT-based microservice. Each phase contains tickable tasks with commit messages.

---

## Testing Tasks & Strategy

### Why Test Incrementally?

Testing after every phase is **possible and recommended**. Here's why:

- **Early bug detection** — Find issues while they're fresh and isolated
- **Faster feedback loops** — You know immediately if something works
- **Better confidence** — You can build on solid ground
- **Easier debugging** — Problems are contained to what you just wrote
- **Better git history** — Changes are small and meaningful

### Testing Strategy by Phase

**Phase 1: Backend MQTT Infrastructure**
- Task 1.1-1.7: Write unit tests for each new service/model
- Test GPS device model serialization, MQTT client connection, subscriber message handling
- Test route tracking detects stop arrivals and loop completions
- Run full backend suite before Phase 2: `./.venv/Scripts/python.exe -m pytest -q`

**Phase 2: GPS Service Foundation**
- Test MQTT broker configuration, GPS position publishing, vehicle tracking state
- Test stop/loop detection in GPS service context
- Test WebSocket event publishing and telemetry storage

**Phase 3: GPS Simulator Engine**
- Test route loading, GPS position generation with noise, dwell time handling
- Test multiple vehicle simulation and journey lifecycle completion

**Phase 4: GPS Service Main Entry Point**
- Test FastAPI startup/shutdown, health/metrics endpoints
- Test MQTT message publishing and telemetry endpoint

**Phase 5: Backend Cleanup & Integration**
- Test MQTT integration with backend simulation
- Test GPS handler processes both MQTT and internal sources
- Full backend suite must be green before Phase 6

**Phase 6: Production Readiness**
- Test Prometheus metrics, MQTT health checks, load handling (100+ vehicles)
- Test real GPS device input (non-simulation mode)

**Phase 7: Final Verification**
- Full integration test suite + performance benchmarks
- Final baseline verification (298+ tests passing)

### Testing Checklist for Every Task

Before marking any task complete:

- [ ] Unit tests written and passing for new functions
- [ ] Integration tests written and passing for component interactions
- [ ] Full backend suite runs green: `./.venv/Scripts/python.exe -m pytest -q`
- [ ] No new TypeScript/JavaScript errors in frontend (if applicable): `npm run build`
- [ ] Code follows project conventions (imports, naming, formatting)
- [ ] No code duplication or redundant abstractions
- [ ] File size is minimal (under 250-300 lines per file)
- [ ] Clear, traceable commit message used

### Quick Testing Commands

| What to Test | Command |
|-------------|---------|
| Backend unit tests | `cd backend && ./.venv/Scripts/python.exe -m pytest -q` |
| Specific test file | `cd backend && ./.venv/Scripts/python.exe -m pytest test_<filename>.py` |
| Backend with coverage | `cd backend && ./.venv/Scripts/python.exe -m pytest --cov=app --cov-report=term-missing` |
| Frontend build | `cd frontend && npm run build` |
| Frontend lint | `cd frontend && npm run lint` |
| GPS service unit tests | `cd gps_service && pytest` |

---

## Phase 1: Backend MQTT Infrastructure

**Description:** Add MQTT support to the backend before extracting the GPS service. This includes creating the GPS device authentication model, MQTT subscriber in the backend, and updating the database schema. These changes are non-breaking and allow the backend to receive GPS data via MQTT while the internal simulation still runs.

### Tasks

- [x] **Task 1.1: Create GPS device model**
  - Create `backend/app/models/gps_device.py` with `GPSDevice` model
  - Add fields: `id`, `tenant_id`, `name`, `token`, `device_type`, `is_active`, `created_at`
  - Import model in `backend/app/models/__init__.py`
  - **Commit:** `feat(backend): add GPS device model for MQTT authentication`

- [x] **Task 1.2: Create GPS position schema**
  - Create `backend/app/schemas/gps.py` with `GPSPositionUpdate` schema
  - Add validation for lat/lng bounds, speed, heading, fuel
  - **Commit:** `feat(backend): add GPS position update schema`

- [x] **Task 1.3: Add MQTT dependencies**
  - Add `paho-mqtt` to `backend/requirements.txt`
  - Create `backend/app/core/mqtt_client.py` with MQTT client setup
  - **Commit:** `feat(backend): add MQTT client dependencies and setup`

- [x] **Task 1.4: Create MQTT subscriber service**
  - Create `backend/app/services/gps_mqtt_subscriber.py`
  - Implement `on_message` handler to process incoming GPS positions
  - Subscribe to topic pattern: `gps/+/+/position`
  - **Commit:** `feat(backend): add MQTT subscriber for GPS positions`

- [x] **Task 1.5: Create GPS position handler service**
  - Create `backend/app/services/gps_handler.py`
  - Implement `process_gps_update()` to update vehicle, create telemetry
  - Delegate alert triggering to existing `alert_service.py`
  - Keep handler stateless and focused on data ingestion only
  - **Commit:** `feat(backend): add GPS position handler service`

- [x] **Task 1.6: Update simulation_runner to handle trip lifecycle from GPS**
  - Create `backend/app/services/route_tracking_service.py`
  - Implement `track_gps_update()` to detect stop arrivals and loop completions
  - Call `start_trip()`, `complete_trip()`, `end_journey()` based on GPS position
  - Call `simulate_passengers_at_stop()` when vehicle arrives at stop
  - Works with BOTH internal simulation AND external GPS sources
  - **Commit:** `feat(backend): add route tracking service for GPS-based trip lifecycle`

- [x] **Task 1.7: Update simulation_runner for passenger simulation from GPS**
  - Handled within `route_tracking_service.py` (created in Task 1.6)
  - `_handle_stop_arrival()` calls `simulate_passengers_at_stop()` when vehicle at stop
  - No separate task needed - passenger simulation is integrated with route tracking
  - **Commit:** Already included in Task 1.6


- [x] **Task 1.8: Create GPS device authentication**
  - Add `authenticate_gps_device()` dependency in `backend/app/core/dependencies.py`
  - Validate MQTT device token against database
  - **Commit:** `feat(backend): add GPS device authentication dependency`

- [x] **Task 1.9: Add MQTT lifecycle to backend startup**
  - Update `backend/main.py` to start MQTT subscriber on startup
  - Connect to MQTT broker, subscribe to topics
  - Handle graceful shutdown
  - **Commit:** `feat(backend): integrate MQTT subscriber into app lifecycle`

- [x] **Task 1.10: Create database migration for GPS devices**
  - Generate Alembic migration for `gps_devices` table
  - Run migration
  - **Commit:** `feat(backend): add migration for GPS devices table`

- [x] **Task 1.11: Add environment configuration for MQTT**
  - Add MQTT config vars to `backend/app/core/config.py`
  - Variables: `MQTT_BROKER_URL`, `MQTT_BROKER_PORT`, `MQTT_USERNAME`, `MQTT_PASSWORD`
  - Update `.env.example`
  - **Commit:** `feat(backend): add MQTT configuration variables`

- [x] **Task 1.12: Write tests for GPS handler**
  - Create `backend/tests/test_gps_handler.py`
  - Test GPS position processing
  - Test vehicle update, telemetry creation
  - Test alert triggering
  - **Commit:** `test(backend): add tests for GPS position handler`

---

## Phase 2: GPS Service Foundation

**Description:** Create the standalone GPS service with basic structure. This phase sets up the directory structure, configuration, MQTT client, and core simulator logic. The service won't be fully functional yet but will have the foundation in place.

### Tasks

- [x] **Task 2.1: Create GPS service directory structure**
  - Create `gps_service/` top-level directory
  - Create subdirectories: `simulator/`, `mqtt/`, `vehicle_tracker/`, `route_cache/`, `models/`, `tests/`
  - Create `__init__.py` files in each directory
  - **Commit:** `feat(gps-service): create directory structure`

- [x] **Task 2.2: Create GPS service configuration**
  - Create `gps_service/config.py` with Pydantic settings
  - Add MQTT broker config, poll interval, simulation mode, retry settings
  - Create `.env.example` file
  - **Commit:** `feat(gps-service): add configuration module`

- [x] **Task 2.3: Create requirements.txt**
  - Add dependencies: `paho-mqtt`, `pydantic`, `pydantic-settings`, `aiohttp`, `asyncio`
  - **Commit:** `feat(gps-service): add requirements.txt`

- [x] **Task 2.4: Create GPS data models**
  - Create `gps_service/models/gps_data.py` with Pydantic models
  - `GPSPosition`, `VehicleState`, `RouteStop` models
  - **Commit:** `feat(gps-service): add GPS data models`

- [x] **Task 2.5: Copy geospatial math utilities**
  - Copy `backend/app/core/geo_math.py` to `gps_service/geo/math.py`
  - Functions: `haversine`, `bearing`, `move_along_bearing`, `point_in_radius`
  - Update imports if needed
  - **Commit:** `feat(gps-service): copy geospatial math utilities`

- [x] **Task 2.6: Create MQTT publisher client**
  - Create `gps_service/mqtt/publisher.py`
  - Implement connection, publish, reconnect logic
  - Add retry with exponential backoff
  - Support QoS levels
  - **Commit:** `feat(gps-service): add MQTT publisher client`

- [x] **Task 2.7: Create vehicle state manager**
  - Create `gps_service/simulator/state_manager.py`
  - Track in-memory state per vehicle: position, progress, speed, heading, fuel
  - Handle state persistence/recovery on restart
  - **Commit:** `feat(gps-service): add vehicle state manager`

- [x] **Task 2.8: Create route cache module**
  - Create `gps_service/route_cache/cache.py`
  - Fetch and cache route stops from backend API
  - Implement TTL-based cache refresh
  - **Commit:** `feat(gps-service): add route cache module`

- [x] **Task 2.9: Create vehicle tracker (fetches from backend)**
  - Create `gps_service/vehicle_tracker/fetcher.py`
  - Poll backend API for active vehicles: `GET /api/v1/vehicles?status=active`
  - Handle pagination, authentication
  - **Commit:** `feat(gps-service): add vehicle tracker fetcher`

- [x] **Task 2.10: Write basic tests for GPS service modules**
  - Create `gps_service/tests/` structure
  - Test state manager, route cache, MQTT publisher mock
  - **Commit:** `test(gps-service): add unit tests for core modules`

- [x] **Task 2.11: Set up local MQTT broker**
  - Use Mosquitto locally, preferably through Docker since the rest of your project already uses containers.

  - The goal would be only:

    - Add Mosquitto to the project's Docker setup.
    - Configure it for local development.
    - Start the broker.
    - Verify the GPS service can connect.
    - Verify the GPS service can publish a message.
    - Verify the backend can subscribe and receive it.
    - Test the actual topic:

---

## Phase 3: GPS Simulator Engine

**Description:** Extract and adapt the core simulation logic from the backend. This is the heart of the GPS service - the physics engine that calculates vehicle positions, speed, heading, and fuel consumption as vehicles follow routes.

### Tasks

- [x] **Task 3.1: Extract advance_vehicle logic**
  - Copy `advance_vehicle()` from `backend/app/websocket/route_simulation.py` to `gps_service/simulator/engine.py`
  - Remove database dependencies, adapt to use cached route data
  - Keep physics: position calculation, speed simulation, fuel depletion
  - **Commit:** `feat(gps-service): extract advance_vehicle core logic`

- [x] **Task 3.2: Adapt congestion simulation**
  - Copy `_handle_congestion()` logic to `gps_service/simulator/congestion.py`
  - Make configurable (enable/disable, probability)
  - **Commit:** `feat(gps-service): add congestion simulation module`

- [x] **Task 3.3: Create simulator orchestrator**
  - Create `gps_service/simulator/orchestrator.py`
  - Implement main tick loop: for each active vehicle, advance and publish
  - Coordinate state manager, route cache, MQTT publisher
  - **Commit:** `feat(gps-service): add simulator orchestrator`

- [x] **Task 3.4: Implement position publishing**
  - In orchestrator, after advancing vehicle, publish to MQTT
  - Topic: `gps/{tenant_id}/{vehicle_id}/position`
  - Payload: GPSPosition model as JSON
  - **Commit:** `feat(gps-service): implement position publishing to MQTT`

- [x] **Task 3.5: Add error handling and recovery**
  - Handle MQTT publish failures with retry
  - Handle route fetch failures gracefully
  - Log errors, continue processing other vehicles
  - **Commit:** `feat(gps-service): add error handling and recovery`

- [x] **Task 3.6: Write simulator integration tests**
  - Test full tick loop with mock backend
  - Test position calculation accuracy
  - Test MQTT publish success/failure scenarios
  - **Commit:** `test(gps-service): add simulator integration tests`

---

## Phase 4: GPS Service Main Entry Point

**Description:** Create the main entry point and API for the GPS service. This includes the FastAPI app for health/status endpoints, the main async loop, and graceful shutdown handling.

### Tasks

- [x] **Task 4.1: Create main.py entry point**
  - Create `gps_service/main.py`
  - Initialize config, MQTT client, state manager
  - Start main simulation loop
  - **Commit:** `feat(gps-service): add main entry point`

- [x] **Task 4.2: Create FastAPI app for GPS service**
  - Create `gps_service/api/app.py`
  - Add health check endpoint: `GET /health`
  - Add status endpoint: `GET /status`
  - **Commit:** `feat(gps-service): add FastAPI app with health endpoints`

- [ ] **Task 4.3: Add vehicle management endpoints**
  - `GET /vehicles` - List tracked vehicles
  - `POST /vehicles` - Add vehicle to track
  - `DELETE /vehicles/{vehicle_id}` - Remove vehicle
  - **Commit:** `feat(gps-service): add vehicle management endpoints`

- [x] **Task 4.4: Implement graceful shutdown**
  - Handle SIGTERM, SIGINT signals
  - Disconnect MQTT client
  - Save state if needed
  - **Commit:** `feat(gps-service): implement graceful shutdown`

- [x] **Task 4.5: Add logging infrastructure**
  - Configure structured logging
  - Log vehicle tracking, position updates, errors
  - **Commit:** `feat(gps-service): add structured logging`

- [x] **Task 4.6: Create Docker configuration**
  - Create `gps_service/docker/Dockerfile`
  - Create `docker-compose.yml` for GPS service + Mosquitto
  - **Commit:** `feat(gps-service): add Docker configuration`

---

## Phase 5: Backend Cleanup & Integration

**Description:** Remove or disable the internal simulation in the backend. Update architecture documentation. Test the full integration between GPS service and backend via MQTT.

### Tasks

- [ ] **Task 5.1: Remove internal simulation runner**
  - Delete or comment out `start_vehicle_simulation()` calls in `backend/main.py`
  - Keep `auto_start_scheduled_trips()` if still needed (move to trip_service)
  - **Commit:** `refactor(backend): disable internal GPS simulation`

### Task 5.2 — Clean up simulation_runner.py

Delete `backend/app/services/simulation_runner.py`. Its three
responsibilities are split three ways:

1. **Auto-start scheduled trips** (`auto_start_scheduled_trips`,
   `start_offset_minutes`) — **kept**. Move verbatim to a new module
   `backend/app/services/trip_auto_start.py`. Add a periodic task in the
   backend lifespan (equivalent to the old `_simulation_loop` tick,
   5s interval) so auto-start continues to work without a manual click.
2. **Vehicle movement + telemetry + fuel/delay alerts**
   (`simulate_active_vehicles`, `advance_vehicle` consumer) — **deleted**.
   Replaced by gps_service → MQTT → backend (`gps_handler` writes
   telemetry). Low-fuel and delay alerts are **not** restored in v1;
   see the "Alerts dropped" note below.
3. **Simulation loop plumbing** (`start_vehicle_simulation`,
   `stop_vehicle_simulation`, `_simulation_loop`, `_auto_start_cycle`,
   `_simulation_task` global) — **deleted**. The loop's only caller
   was its own `start_vehicle_simulation`, which Task 7.4 commented out
   in `main.py`; Task 5.1 removed the orphaned stop call.

- [x] Create `backend/app/services/trip_auto_start.py` with
      `start_offset_minutes` and `auto_start_scheduled_trips`, moved
      verbatim from `simulation_runner.py`.
- [x] Add `_auto_start_loop(stop_event)` and its task to `backend/main.py`'s
      lifespan (5s interval, matching the old `TICK_SECONDS`).
- [x] Delete `backend/app/services/simulation_runner.py`.
- [x] Update `backend/tests/trips/test_auto_start_trips.py` — import
      `auto_start_scheduled_trips` from the new module.
- [x] Update `backend/guidelines/architecture.md` — remove
      `simulation_runner.py` from the file listing (5.4 does the broader
      doc rewrite; this is the minimal edit so the doc doesn't reference
      a deleted file).
- [x] **Alerts dropped (document in commit):**
      - Low-fuel alert fired at `fuel < LOW_FUEL_THRESHOLD` (15%). No
        equivalent in the MQTT pipeline. A future task could add a
        low-fuel check to `gps_handler.process_position` (which already
        receives `fuel` on the MQTT payload via `GPSPositionUpdate`).
      - Delay alert fired when `advance_vehicle` signalled
        `delay_crossed`. No equivalent signal exists in the MQTT
        pipeline; retired permanently unless a new delay detection is
        designed.
      - Capacity alert continues to fire via `occupancy_service.record`
        (Task 7.2) — unaffected by this task.
- [x] Test: full backend suite passes; `rg "simulation_runner" backend/`
      returns only `guidelines/architecture.md` (which 5.4 updates);
      auto-start test still passes.
- [x] Commit: `refactor(backend): clean up simulation_runner.py`

### Task 5.3 — Remove route_simulation imports from backend

`route_simulation.py` has four external consumers: `tracking.py`,
`arrival_service.py`, `trip_service.py`, and the test suite. This task
removes the production dependencies in 5.3a and deletes the module +
its tests in 5.3b.

**Design note — next_stop_index duplication.** gps_service's
`SimulationEngine` tracks `state.next_stop_index` per vehicle to drive
movement. The backend's `route_simulation._state[vehicle_id]` tracks
its own copy for display (WS `nextStopName`, `arrival_service` ETAs).
After 5.3a, the backend derives `next_stop_index` from position
(nearest stop + 1). This is an approximation: when a vehicle has just
left stop A and is closer to B than to A, it computes "next = C" while
gps_service's true value is B. Matches the pre-existing fallback in
`arrival_service` (not worse than today). Task 5.7 (evaluate after
5.3b) may wire `nextStopId` through the MQTT payload to eliminate the
approximation if the demo needs exact ETAs.

#### Task 5.3a — Extract position-derived helpers

- [x] Create `backend/app/services/route_progress.py` with:
      - `StopPoint` (dataclass, moved from `route_simulation.py`)
      - `load_route_stops` + `get_stops_cached` (per-process cache)
      - `compute_next_stop_index(vehicle, stops) -> int` — nearest stop
        + 1 (position-derived; see design note above)
      - `get_next_stop_name(vehicle, stops) -> str`
      - `compute_progress_pct(vehicle, stops) -> int`
- [x] Rewire `backend/app/websocket/tracking.py`:
      - Replace `from app.websocket.route_simulation import (...)` with
        `from app.services.route_progress import (...)`.
      - `fuel`, `currentOccupancy`: from `vehicle.fuel` /
        `vehicle.current_occupancy` (written by the GPS handler and
        occupancy pipeline). Drop `_state` accesses.
      - `nextStopName`, `progressPct`: from the new helpers.
      - `atStop`: **dropped** — always `""`. It was a visual-only field
        fed by sim `dwell_remaining`; no equivalent in the MQTT
        pipeline. See follow-up note below.
- [x] Rewire `backend/app/services/arrival_service.py`:
      - Replace lazy `_state` imports with top-level
        `from app.services.route_progress import get_stops_cached,
        compute_next_stop_index, StopPoint`.
      - `current_occupancy`: from `vehicle.current_occupancy`.
      - `_next_stop_index` becomes a one-line delegate to
        `compute_next_stop_index`.
- [x] Update `backend/app/services/trip_service.py`:
      - Remove `from app.websocket import route_simulation`.
      - Delete the two `route_simulation.clear_vehicle_state(...)`
        calls (they cleared `_state`, which no longer exists).
- [x] Test: `pytest backend/tests -q` — same count as before, all green.
      `rg "route_simulation" backend/app/` returns only
      `route_simulation.py` itself.
- [x] **Follow-up (not in this commit):** if the frontend uses `atStop`,
      add a backend query for the most recent `occupancy_event` per
      vehicle (within dwell window) to repopulate it. Defer until
      confirmed needed.
- [x] Commit: `refactor(backend): extract route position helpers`

#### Task 5.3b — Delete route_simulation.py

- [ ] Delete `backend/app/websocket/route_simulation.py`.
- [ ] Delete tests that directly exercise it:
      - `backend/tests/test_fuel_model.py` (fuel depletion over sim ticks)
      - `backend/tests/trips/test_journey_rounds.py` (loop counting via sim)
      - `backend/tests/trips/test_simulation_trip_dedup.py`
      - `backend/tests/test_capacity_and_delay_alerts.py` (patches sim
        random/randint to trigger alerts; the loop no longer exists)
- [ ] Update `backend/guidelines/architecture.md` — remove
      `route_simulation.py` from the file listing.
- [ ] Test: full backend suite green; `rg "route_simulation" backend/`
      returns zero hits (excluding `alembic/versions/`).
- [ ] Commit: `refactor(backend): delete route_simulation`

**Note on lost test coverage:** the four test files above tested
behaviour that no longer exists after 5.2 + 5.3a:
- `advance_vehicle` movement, deceleration, congestion, dwell
- fuel depletion over sim ticks (vehicle.fuel is now written by the
  GPS handler from MQTT)
- loop counting via `completed_loops` (already stale; see design §12)
- delay alerts (`delay_crossed` came from `advance_vehicle`; see 5.2's
  "alerts dropped" note)

No equivalent tests are added — the equivalent behaviour lives in
gps_service (`SimulationEngine`) and passenger_service (occupancy
pipeline), tested there.

**Task 5.7 (evaluate)** — after 5.3b, watch `/api/v1/arrivals` ETAs.
If they look wrong near stops (vehicle "arriving at C" while actually
heading to B), add `nextStopId` to the gps_service MQTT payload, store
it on `vehicles` (new column), and read it in `tracking` /
`arrival_service`. Not scheduled; evaluate from real behaviour.

- [ ] **Task 5.4: Update backend architecture documentation**
  - Update `backend/guidelines/architecture.md` to reflect MQTT GPS service
  - Document new data flow: GPS service → MQTT → Backend
  - **Commit:** `docs(backend): update architecture for GPS service`

- [ ] **Task 5.5: Create integration test suite**
  - Create `tests/test_gps_mqtt_integration.py`
  - Test: GPS service publishes → Backend receives → Vehicle updated
  - Test: Telemetry created, alerts triggered
  - **Commit:** `test(backend): add GPS MQTT integration tests`

- [ ] **Task 5.6: Test end-to-end flow**
  - Start MQTT broker (Mosquitto or Redis)
  - Start GPS service
  - Start backend
  - Verify position updates flow through
  - **Commit:** `test: verify end-to-end GPS flow`

---

## Phase 6: Production Readiness

**Description:** Make the system production-ready with proper error handling, monitoring, documentation, and deployment configurations. Add support for switching between simulation and real GPS devices.

### Tasks

- [ ] **Task 6.1: Add Prometheus metrics to GPS service**
  - Track: positions published, MQTT errors, vehicles tracked
  - Expose metrics endpoint
  - **Commit:** `feat(gps-service): add Prometheus metrics`

- [ ] **Task 6.2: Add health checks for MQTT connection**
  - Check MQTT broker connectivity in `/health` endpoint
  - Report connection status in `/status`
  - **Commit:** `feat(gps-service): add MQTT health checks`

- [ ] **Task 6.3: Create deployment documentation**
  - Document environment variables
  - Document MQTT broker setup (Mosquitto/Redis)
  - Document how to switch to real GPS devices
  - **Commit:** `docs(gps-service): add deployment guide`

- [ ] **Task 6.4: Add support for real GPS devices**
  - Update GPS service to accept external GPS input
  - Configuration: `SIMULATION_MODE=false`
  - Document real device integration
  - **Commit:** `feat(gps-service): add real GPS device support`

- [ ] **Task 6.5: Load testing**
  - Test with 100+ vehicles
  - Verify MQTT broker handles load
  - Optimize if needed
  - **Commit:** `test(gps-service): load test with 100+ vehicles`

- [ ] **Task 6.6: Security hardening**
  - Add MQTT TLS support
  - Validate device tokens
  - Rate limiting if needed
  - **Commit:** `feat(gps-service): add security hardening`

- [ ] **Task 6.7: Create runbook for operations**
  - Document common issues and fixes
  - Document restart procedures
  - Document monitoring alerts
  - **Commit:** `docs(gps-service): add operations runbook`

---

## Phase 7: Final Verification & Documentation

**Description:** Final verification that everything works together, update all documentation, and mark the project as complete.

### Tasks

- [ ] **Task 7.1: Update main project README**
  - Add GPS service to architecture overview
  - Update setup instructions
  - **Commit:** `docs: update main README with GPS service`

- [ ] **Task 7.2: Create architecture diagram**
  - Create visual diagram showing GPS service → MQTT → Backend flow
  - Add to documentation
  - **Commit:** `docs: add architecture diagram for GPS service`

- [ ] **Task 7.3: Final integration test**
  - Run full test suite
  - Verify all tests pass
  - **Commit:** `test: final integration test verification`

- [ ] **Task 7.4: Performance benchmark**
  - Measure latency: GPS publish → Backend process
  - Measure throughput: positions per second
  - Document results
  - **Commit:** `docs: add performance benchmark results`

- [ ] **Task 7.5: Mark project complete**
  - Update this guide with all tasks ticked
  - Create summary of changes
  - **Commit:** `docs: mark GPS service extraction complete`

---

## Summary

| Phase | Description | Tasks |
|-------|-------------|-------|
| Phase 1 | Backend MQTT Infrastructure | 12 tasks |
| Phase 2 | GPS Service Foundation | 10 tasks |
| Phase 3 | GPS Simulator Engine | 6 tasks |
| Phase 4 | GPS Service Main Entry Point | 6 tasks |
| Phase 5 | Backend Cleanup & Integration | 6 tasks |
| Phase 6 | Production Readiness | 7 tasks |
| Phase 7 | Final Verification & Documentation | 5 tasks |

**Total: 52 tasks**

---

## Notes

- Each task should be a single logical change with a clear commit
- Run tests after each phase to ensure nothing breaks
- Phase 1 and 2 can be done in parallel if needed
- Phase 5 is the breaking change - plan accordingly
- Keep the backend simulation running during Phase 1-4 for safety

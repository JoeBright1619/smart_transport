# Passenger Service — Implementation Plan

Build a standalone `passenger_service` that subscribes to `gps_service`'s MQTT
position events, detects stop arrivals, simulates boardings and alightings,
and publishes occupancy events for the backend to consume.

**Companion document:** `passenger_service/design.md`. Read it before
starting any phase — this plan assumes every decision there.

**Relationship to `gps_service`:** `passenger_service` mirrors `gps_service`'s
layout, conventions, and testing discipline. When in doubt, open the
corresponding file in `gps_service/` and copy its shape.

**Working agreement:**
- One task per commit.
- Tests written in the same commit as implementation.
- Run `cd passenger_service && pytest -q` after every task.
- Stop and report after each task; do not chain into the next task unprompted.

---

## Testing Tasks & Strategy

### Why Test Incrementally?

(Same rationale as gps_service/guide.md — copy verbatim.)

### Testing Strategy by Phase

**Phase 0: Scaffolding**
- Test settings load from env with defaults and overrides.
- Test Dockerfile builds: `docker compose build passenger_service`.

**Phase 1: MQTT transport**
- Test publisher connect/publish/disconnect/retry with mocked paho client.
- Test subscriber dispatches incoming JSON to the async callback via `run_coroutine_threadsafe`.

**Phase 2: Backend contract additions**
- Test `latest-arrival-sequence` returns max sequence, 404 for unknown vehicle, tenant-scoped.
- Test `OccupancyEvent` schema validates representative payload.
- Test Alembic migration applies cleanly.

**Phase 3: Backend integration (passenger_service side)**
- Test route cache hit/miss/TTL.
- Test vehicle map fetcher camelCase→snake_case, skips route-less vehicles.
- Test tenant identity resolver.
- Test arrival-sequence seeding (mocked HTTP, 404 → 0).
- Test onboard seeding from `currentOccupancy`.

**Phase 4: Detection and simulation**
- Test `VehicleArrivalState` lifecycle and route-change reset.
- Test detector: near+slow, near+fast, far+slow, cooldown, different stop.
- Test simulation engine: terminus, last stop, mid-route, crush cap, determinism.
- Test `OccupancyEvent` construction: idempotency key format, timestamps.

**Phase 5: Orchestration**
- Test orchestrator with mocked collaborators: publish on arrival, no publish otherwise.
- Test periodic vehicle refresh: calls fetcher on interval, stops on shutdown event.

**Phase 6: Service entry point**
- Test FastAPI lifespan: startup resolves tenant, connects MQTT, subscribes, starts refresh; shutdown reverses.
- Test `/health` and `/status` response shapes.

### Testing Checklist for Every Task

(Bullets adapted: `cd passenger_service && pytest -q` for the suite command, keep the rest.)

### Quick Testing Commands

| What to Test | Command |
|---|---|
| Passenger service unit tests | `cd passenger_service && pytest -q` |
| Specific test file | `cd passenger_service && pytest tests/test_<filename>.py -q` |
| With coverage | `cd passenger_service && pytest --cov=passenger_service --cov-report=term-missing -q` |
| Docker build | `docker compose build passenger_service` |
| Backend suite | `cd backend && ./.venv/Scripts/python.exe -m pytest -q` |
| GPS service suite | `cd gps_service && pytest -q` |


## Phase 0 — Scaffolding

### Task 0.1 — Directory skeleton and config
- [x] Create `passenger_service/__init__.py`
- [x] Create `passenger_service/config.py` with `PassengerServiceSettings`
      (mirror `gps_service/config.py`). Fields:
      `MQTT_BROKER_URL`, `MQTT_BROKER_PORT`, `MQTT_USERNAME`, `MQTT_PASSWORD`,
      `MQTT_CLIENT_ID`, `MQTT_RETRY_ATTEMPTS`, `MQTT_RETRY_DELAY`,
      `BACKEND_BASE_URL`, `BACKEND_SERVICE_TOKEN`, `BACKEND_REQUEST_TIMEOUT`,
      `BACKEND_PAGE_SIZE`, `VEHICLE_REFRESH_INTERVAL`,
      `API_HOST`, `API_PORT`, `STOP_ARRIVAL_RADIUS_M`,
      `STOP_SPEED_THRESHOLD_KMH`, `STOP_COOLDOWN_SECONDS`,
      `CRUSH_CAPACITY_FACTOR`.
- [x] Create `passenger_service/requirements.txt` (mirror gps_service; drop
      anything not needed).
- [x] Test: settings load from env with defaults.
- [x] Commit: `passenger_service: scaffold package and settings`

### Task 0.2 — Dockerfile and compose entry
- [x] Create `passenger_service/Dockerfile` (mirror `gps_service/Dockerfile`).
- [x] Add `passenger_service` service to root `docker-compose.yml`.
      Reuse `GPS_SERVICE_TOKEN` bootstrap token for auth (see 5.1a).
- [x] Test: `docker compose build passenger_service` succeeds.
- [x] Commit: `passenger_service: add Dockerfile and compose service`

---

## Phase 1 — MQTT transport

### Task 1.1 — Publisher
- [ ] Create `passenger_service/mqtt/publisher.py`, mirroring
      `gps_service/mqtt/publisher.py`. Same API: `connect`, `disconnect`,
      `publish(topic, payload, qos, retain)`.
- [ ] Test: mocked paho client; connect/publish/disconnect call the right
      methods; publish retries on failure.
- [ ] Commit: `passenger_service: add MQTT publisher`

### Task 1.2 — Subscriber
- [ ] Create `passenger_service/mqtt/subscriber.py`. Wraps paho-mqtt with
      a background loop, accepts a `(topic, payload) -> Awaitable[None]`
      callback. Runs the callback on the asyncio loop via
      `run_coroutine_threadsafe`, mirroring the backend's existing subscriber.
- [ ] Test: mocked client; a published message invokes the callback with
      the parsed JSON.
- [ ] Commit: `passenger_service: add MQTT subscriber`

---

## Phase 2 - Backend contract additions

### Task 2.0 — Latest-arrival-sequence endpoint
- [ ] Add `GET /api/v1/vehicles/{vehicle_id}/latest-arrival-sequence`
      to the backend. Requires the `boarding_records` table (Task 2.1)
      to exist; sequence the two tasks accordingly.
- [ ] Returns `{"data": {"arrival_sequence": N}}` or 404 if no records.
- [ ] Test: returns max sequence for a vehicle; 404 for unknown vehicle;
      scoped to the caller's tenant.
- [ ] Commit: `backend: add latest-arrival-sequence endpoint`

### Task 2.1 — OccupancyEvent schema and model
- [ ] `backend/app/schemas/occupancy.py` — `OccupancyEvent` Pydantic model
      matching `passenger_service/models/occupancy.py` field-for-field.
- [ ] `backend/app/models/boarding_record.py` — SQLAlchemy model per
      design.md §8, with `idempotency_key` UNIQUE.
- [ ] Alembic migration for `boarding_records`.
- [ ] Test: schema validates a representative payload; migration applies.
- [ ] Commit: `backend: add occupancy schema, model, and migration`

## Phase 3 — Backend integration

### Task 3.1 — Route cache
- [ ] Create `passenger_service/route_cache/cache.py`, mirroring
      `gps_service/route_cache/cache.py`. Same API:
      `get_route_stops(route_id, token) -> list[RouteStop]`, TTL 60s,
      `close()`.
- [ ] Test: mocked aiohttp; cache hit avoids second HTTP call; TTL expiry
      triggers refetch; missing stops handled.
- [ ] Commit: `passenger_service: add route cache`

### Task 3.2 — Vehicle map
- [ ] Create `passenger_service/vehicle_map/fetcher.py` with
      `VehicleMapFetcher(base_url, service_token, ...)` exposing
      `fetch_active_vehicles() -> list[VehicleInfo]` where `VehicleInfo`
      carries `vehicle_id`, `tenant_id`, `route_id`, `seating_capacity`.
      Reuse `gps_service/vehicle_tracker/wire.py`'s `normalize_keys` approach
      (copy, don't import).
- [ ] Test: mocked HTTP; camelCase → snake_case; skips vehicles with no
      route_id.
- [ ] Commit: `passenger_service: add vehicle map fetcher`

### Task 3.3 — Tenant identity
- [ ] Create `passenger_service/identity.py` with `resolve_tenant_id(...)`,
      mirroring `gps_service/vehicle_tracker/identity.py`.
- [ ] Test: mocked HTTP; parses `{data: {tenant_id: ...}}`.
- [ ] Commit: `passenger_service: add tenant identity resolver`

### Task 3.4 — Arrival sequence seeding
- [ ] Add `GET /api/v1/vehicles/{vehicle_id}/latest-arrival-sequence` to
      the backend, returning the max `arrival_sequence` from
      `boarding_records` for that vehicle (or 404 if none).
- [ ] In `passenger_service/vehicle_map/fetcher.py` (or a new
      `seeding.py`), add `fetch_latest_sequences(vehicle_ids) ->
      dict[str, int]` that queries the new endpoint per vehicle at
      startup.
- [ ] In `VehicleStateStore.get_or_create`, accept an optional initial
      `arrival_sequence` and use it when constructing fresh state.
- [ ] Test: mocked HTTP; sequences seeded correctly; 404 defaults to 0;
      startup uses seeded values.
- [ ] Commit: `passenger_service: seed arrival_sequence from backend at startup`

### Task 3.5 — Onboard count seeding
- [ ] Extend the vehicle-list fetch to read `currentOccupancy` (or
      `current_occupancy`) from each active vehicle.
- [ ] In `VehicleStateStore.get_or_create`, accept an optional initial
      `onboard` and use it when constructing fresh state.
- [ ] Test: mocked HTTP with non-zero occupancy; state initialises with
      that value; missing field defaults to 0.
- [ ] Commit: `passenger_service: seed onboard count from backend at startup`

---

## Phase 4 — Detection and simulation

### Task 4.1 — Vehicle arrival state
- [ ] Create `passenger_service/detection/state.py` with
      `VehicleArrivalState` dataclass (fields per design.md §3) and a
      `VehicleStateStore` holding `dict[str, VehicleArrivalState]` with
      `get_or_create(vehicle_id, route_id)` that resets state on route change.
- [ ] Test: state initialises, persists across calls, resets on route change.
- [ ] Commit: `passenger_service: add per-vehicle arrival state`

### Task 4.2 — Stop arrival detection
- [ ] Create `passenger_service/detection/detector.py` with
      `detect_arrival(position, stops, state, now_mono) -> RouteStop | None`.
      Pure function: haversine distance, speed threshold, cooldown debounce.
- [ ] Test: near+slow → returns stop; near+fast → None; far+slow → None;
      repeat within cooldown → None; different stop → returns.
- [ ] Commit: `passenger_service: add stop arrival detector`

### Task 4.3 — Passenger simulation
- [ ] Create `passenger_service/simulation/engine.py` with
      `simulate_passengers(state, stop, stops, vehicle_id, seating_capacity)
      -> tuple[int, int]` returning `(boardings, alightings)`. Deterministic
      seed derived from `hashlib.sha256(f"{vehicle_id}:{arrival_sequence}")`.
      Constraints per design.md §8.
- [ ] Test: terminus behaviour, last-stop behaviour, mid-route bounds,
      alightings <= onboard, crush capacity respected, deterministic across
      runs with same inputs.
- [ ] Commit: `passenger_service: add passenger simulation engine`

### Task 4.4 — Occupancy event model
- [ ] Create `passenger_service/models/occupancy.py` with `OccupancyEvent`
      Pydantic model per design.md §6. Include `build_occupancy_event(...)`
      helper that constructs it with both timestamps and the derived
      `idempotency_key`.
- [ ] Test: field validation, idempotency key format, timestamp serialisation.
- [ ] Commit: `passenger_service: add occupancy event model`

---

## Phase 5 — Orchestration

### Task 5.1 — Detector orchestration
- [ ] Create `passenger_service/detection/orchestrator.py` with a class
      that, given a `PositionEvent` and its collaborators
      (`state_store`, `route_cache`, `vehicle_map`, `publisher`), runs the
      detection loop and emits an occupancy event on arrival. Pure logic,
      no MQTT wiring — takes already-parsed inputs.
- [ ] Test: inject mocked collaborators; assert occupancy event is published
      on detected arrival with expected fields; assert no publish on
      non-arrival.
- [ ] Commit: `passenger_service: add detection orchestrator`

### Task 5.2 — Periodic vehicle refresh
- [ ] Add a background task that refreshes the vehicle map every
      `VEHICLE_REFRESH_INTERVAL` seconds, mirroring
      `gps_service/api/app.py`'s `_sync_loop`.
- [ ] Test: mock fetcher; assert periodic calls; assert shutdown event stops it.
- [ ] Commit: `passenger_service: add periodic vehicle map refresh`

---

## Phase 6 — Service entry point

### Task 6.1 — FastAPI app with lifespan
- [ ] Create `passenger_service/api/app.py` with `create_app()` and a
      `lifespan` that:
      - resolves tenant
      - connects MQTT publisher and subscriber
      - builds route cache, vehicle map
      - subscribes to `gps/+/+/position`
      - starts the periodic vehicle-refresh task
      - on shutdown: unsubscribes, disconnects MQTT, closes route cache
- [ ] Add `/health` (returns `{"status": "ok"}`) and `/status` (tenant,
      mqtt_connected, vehicles_tracked, events_published, uptime) in the
      `{data, meta, error}` envelope.
- [ ] Test: mocked collaborators; app starts, both endpoints return expected
      shapes, shutdown completes cleanly.
- [ ] Commit: `passenger_service: add FastAPI app with health endpoints`

### Task 6.2 — Entry point
- [ ] Create `passenger_service/main.py` as a thin uvicorn runner
      mirroring `gps_service/main.py`.
- [ ] Commit: `passenger_service: add service entry point`

---

## Phase 7 — Backend integration

### Task 7.2 — Occupancy MQTT subscriber
- [ ] `backend/app/services/occupancy_mqtt_subscriber.py`, mirroring
      `gps_mqtt_subscriber.py`. Subscribes to `gps/+/+/occupancy`, validates
      against `OccupancyEvent`, hands to `OccupancyService.record(...)`.
- [ ] Test: mocked client + mocked service; invalid payload is logged and
      dropped; valid payload calls service.
- [ ] Commit: `backend: subscribe to occupancy MQTT topic`

### Task 7.3 — Occupancy service
- [ ] `backend/app/services/occupancy_service.py` with
      `record(db, event: OccupancyEvent) -> None`:
      - `INSERT INTO boarding_records ... ON CONFLICT (idempotency_key) DO NOTHING`
      - if inserted, `UPDATE vehicles SET current_occupancy = event.onboard`
      - if `onboard >= seating_capacity * 0.9`, emit capacity alert
- [ ] Test: dedup on idempotency key; capacity alert triggers at threshold;
      no alert below threshold; unknown vehicle is logged and skipped.
- [ ] Commit: `backend: add occupancy service with idempotent writes`

### Task 7.4 — Wire subscriber into app startup
- [ ] Register the occupancy subscriber in the backend's FastAPI lifespan,
      alongside the existing GPS subscriber.
- [ ] Test: app starts, both subscriptions are registered.
- [ ] Commit: `backend: wire occupancy subscriber into app lifespan`

### Task 7.5 — WebSocket broadcast
- [ ] Extend the existing WebSocket broadcaster to emit `occupancy_update`
      messages after successful commits.
- [ ] Test: mocked broadcaster; occupancy commit triggers broadcast with
      expected envelope.
- [ ] Commit: `backend: broadcast occupancy updates over WebSocket`

---

## Phase 8 — Cleanup

### Task 8.1 — Delete backend simulation
- [ ] Remove `backend/app/services/passenger_simulation.py` (confirm exact
      path during task).
- [ ] Remove any scheduled task or background loop that drove it.
- [ ] Remove `backend/tests/test_passenger_simulation.py` (or equivalent).
- [ ] Test: full backend suite passes.
- [ ] Commit: `backend: remove passenger simulation (moved to passenger_service)`

### Task 8.2 — Documentation
- [ ] Add `docs/architecture.md` explaining the full system: backend,
      gps_service, passenger_service, MQTT topics, data flow, and the
      reasoning behind the split.
- [ ] Update root `README.md` to reflect the three-service layout and the
      `docker compose up` demo flow.
- [ ] Commit: `docs: add architecture overview`

---

## Testing checklist (run before declaring the project complete)

- [ ] `cd passenger_service && pytest -q` — all green
- [ ] `cd gps_service && pytest -q` — all green
- [ ] `cd backend && ./.venv/Scripts/python.exe -m pytest -q` — all green
- [ ] `docker compose down && docker compose up --build` — all services healthy
- [ ] `curl http://localhost:8001/health` — GPS service up
- [ ] `curl http://localhost:8002/health` — Passenger service up
- [ ] Subscribe to `gps/+/+/occupancy` — events flow within one route loop
- [ ] Query `SELECT COUNT(*) FROM boarding_records;` — grows over time
- [ ] Query `SELECT vehicle_id, current_occupancy FROM vehicles;` — plausible non-zero
- [ ] Frontend: occupancy indicators update live
- [ ] `rg "passenger_simulation" backend/` — no hits
- [ ] Ctrl+C on `docker compose` — clean shutdown, no orphaned processes

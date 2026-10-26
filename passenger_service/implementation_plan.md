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

**Task order matters.** Within each phase, tasks are listed in dependency order.
Backend contract work (Phase 2) lands before the passenger_service clients that
call it (Phase 3), and `VehicleStateStore` (Task 4.1) exists before anything
seeds it.

---

## Testing Tasks & Strategy

### Why Test Incrementally?

> TODO: copy this section verbatim from `gps_service/guide.md` (the source file
> was not available when this plan was revised).

### Testing Strategy by Phase

**Phase 0: Scaffolding**
- Test settings load from env with defaults and overrides (including `REVENUE_PER_KM`).
- Test Dockerfile builds: `docker compose build passenger_service`.

**Phase 1: MQTT transport and position model**
- Test publisher connect/publish/disconnect/retry with mocked paho client.
- Test subscriber dispatches incoming JSON to the async callback via `run_coroutine_threadsafe`.
- Test `PositionEvent` parses a representative `GPSPositionUpdate` payload and rejects malformed ones.

**Phase 2: Backend contract additions**
- Test `OccupancyEvent` schema validates a representative payload and applies defaults for the optional fields.
- Test Alembic migration applies cleanly; `boarding_passenger_events` rows cascade-delete with the parent.
- Test `latest-arrival-sequence` returns max sequence, 404 (`vehicle_not_found`) for unknown/other-tenant vehicle, 404 (`no_arrival_records`) for a vehicle with no events.
- Test the passengers endpoint: returns the universal pool when `tenant_id`  is omitted, the tenant-scoped subset when supplied, and is role-filtered(`role=passenger`).

**Phase 3: passenger_service backend clients**
- Test route cache hit/miss/TTL.
- Test vehicle map fetcher camelCase→snake_case, skips route-less vehicles, reads `currentOccupancy` (missing → 0).
- Test tenant identity resolver.
- Test passenger pool fetcher: expected list, cache hit avoids a second call, refresh after interval.
- Test sequence client: 200 → value, both 404 variants → 0, network error/5xx raises.

**Phase 4: Detection and simulation**
- Test `VehicleArrivalState` / `VehicleStateStore`: lifecycle, seeding, route change preserves `arrival_sequence` and returns released IDs, `remove`.
- Test detector: near+slow, near+fast, far+slow, cooldown, re-arm after dwell, different stop, returns the matching `RouteStop`.
- Test simulation engine: terminus, last stop (all alight + 3–6 anonymous re-boards), mid-route, crush cap, synthesis of seeded passengers, real-ID exclusions, revenue, determinism, purity (state not mutated).

- Gapped sequence data (`[0, 1, 3]`): destinations sampled over positions map back to valid `sequence` values; a passenger with `dest_sequence=3` alights  when `current_sequence=3`, not when the array index reaches 2.

- Test `OccupancyEvent` construction: idempotency key format, timestamps, optional fields.

**Phase 5: Orchestration**
- Test orchestrator with mocked collaborators: publish on arrival, no publish otherwise.
- Test lazy seeding on first sight (and skip-without-guessing on seed failure), route-change release of IDs, global-set updates, one real ID never on two vehicles at once.
- Test periodic refresh: calls fetchers on interval, releases IDs for vehicles that left the map, stops on shutdown event.

**Phase 6: Service entry point**
- Test FastAPI lifespan: startup resolves tenant, connects MQTT, subscribes, starts refresh; shutdown reverses.
- Test `/health` and `/status` response shapes.

**Phase 7: Backend consumption**
- Test subscriber drops invalid payloads and forwards valid ones.
- Test occupancy service: dedup, children/vehicle/revenue/alert skipped on duplicate, capacity threshold and 5-minute dedup, unknown vehicle skipped, atomic transaction.
- Test WebSocket broadcast after commit only.
- Test legacy loop disabled; subscriber registered in lifespan.

**Phase 8: Verification and cleanup**
- Full backend suite passes after deletion; `alembic downgrade`/`upgrade` round-trip is clean.

### Testing Checklist for Every Task

- Run `cd passenger_service && pytest -q` (or the relevant suite for backend tasks) and confirm all green.
- New behaviour has a test in the same commit.
- No test depends on wall-clock time, network, or a real broker (inject clocks/mocks).
  In particular: `detect_arrival` takes `now_mono` as a parameter precisely so
  cooldown/re-arm tests can advance a fake clock; it must never call
  `time.monotonic()` internally..
- Pure functions are tested with fixed seeds; assertions never depend on global state.

### Quick Testing Commands

| What to Test | Command |
|---|---|
| Passenger service unit tests | `cd passenger_service && pytest -q` |
| Specific test file | `cd passenger_service && pytest tests/test_<filename>.py -q` |
| With coverage | `cd passenger_service && pytest --cov=passenger_service --cov-report=term-missing -q` |
| Docker build | `docker compose build passenger_service` |
| Backend suite | `cd backend && ./.venv/Scripts/python.exe -m pytest -q` |
| GPS service suite | `cd gps_service && pytest -q` |

The backend command uses the Windows venv path (./.venv/Scripts/python.exe);
on macOS/Linux use ./.venv/bin/python -m pytest -q.

---

## Phase 0 — Scaffolding

### Task 0.1 — Directory skeleton and config
- [x] Create `passenger_service/__init__.py`
- [x] Create `passenger_service/config.py` with `PassengerServiceSettings`
      (mirror `gps_service/config.py`). Fields:
      `MQTT_BROKER_URL`, `MQTT_BROKER_PORT`, `MQTT_USERNAME`, `MQTT_PASSWORD`,
      `MQTT_CLIENT_ID`, `MQTT_RETRY_ATTEMPTS`, `MQTT_RETRY_DELAY`,
      `BACKEND_BASE_URL`, `BACKEND_SERVICE_TOKEN`, `BACKEND_REQUEST_TIMEOUT`,
      `BACKEND_PAGE_SIZE` (max items per page when fetching the vehicle list / passenger pool), `VEHICLE_REFRESH_INTERVAL`,
            `API_HOST`, `API_PORT`, `STOP_ARRIVAL_RADIUS_M`,
      `STOP_SPEED_THRESHOLD_KMH`, `STOP_COOLDOWN_SECONDS`,
      `CRUSH_CAPACITY_FACTOR`, `REVENUE_PER_KM` (default 60.0; the
      simulation engine is the first consumer, but the setting belongs
      with the rest of the config block).
- [x] Create `passenger_service/requirements.txt` (mirror gps_service; drop
      anything not needed).
- [x] Test: settings load from env with defaults.
- [x] Commit: `passenger_service: scaffold package and settings`

### Task 0.2 — Dockerfile and compose entry
- [x] Create `passenger_service/Dockerfile` (mirror `gps_service/Dockerfile`).
- [x] Add `passenger_service` service to root `docker-compose.yml`.
      Reuse the `GPS_SERVICE_TOKEN` bootstrap token for backend auth.
- [x] Test: `docker compose build passenger_service` succeeds.
- [x] Commit: `passenger_service: add Dockerfile and compose service`

### Task 0.3 — (removed)

`REVENUE_PER_KM` is part of Task 0.1. There is no separate task.

---

## Phase 1 — MQTT transport and position model

### Task 1.1 — Publisher
- [x] Create `passenger_service/mqtt/publisher.py`, mirroring
      `gps_service/mqtt/publisher.py`. Same API: `connect`, `disconnect`,
      `publish(topic, payload, qos, retain)`.
- [x] Test: mocked paho client; connect/publish/disconnect call the right
      methods; publish retries on failure.
- [x] Commit: `passenger_service: add MQTT publisher`

### Task 1.2 — Subscriber
- [x] Create `passenger_service/mqtt/subscriber.py`. Wraps paho-mqtt with
      a background loop, accepts a `(topic, payload) -> Awaitable[None]`
      callback. Runs the callback on the asyncio loop via
      `run_coroutine_threadsafe`, mirroring the backend's existing subscriber.
- [x] Test: mocked client; a published message invokes the callback with
      the parsed JSON.
- [x] Commit: `passenger_service: add MQTT subscriber`

### Task 1.3 — Position event model
- [x] Create `passenger_service/models/position.py` with `PositionEvent`
      (Pydantic): `vehicle_id`, `tenant_id`, `lat`, `lng`, `speed`,
      `timestamp`. Mirror the fields of `gps_service/mqtt/payload.py`
      (confirm exact names there). If the wire names differ from the
      design's snake_case assumption, use Pydantic field aliases rather
      than renaming the internal fields — and update design §3 in the
      same commit.
- [x] Test: parses a representative payload; malformed payload raises.
- [x] Commit: `passenger_service: add position event model`

---

## Phase 2 — Backend contract additions

### Task 2.1 — OccupancyEvent schema and models
- [x] `backend/app/schemas/occupancy.py` — `OccupancyEvent` Pydantic model.
      Author it against **design §5** (not against the not-yet-written
      Task 4.4 model; Task 4.5 brings the wire model into line). It must
      match `passenger_service/models/occupancy.py` field-for-field once
      4.5 lands, including
      `boarded_passenger_ids: list[str] = []`, `alighted_passenger_ids: list[str] = []`,
      `revenue_delta: float = Field(default=0.0, ge=0.0)`.
- [x] `backend/app/models/occupancy_event.py` — `OccupancyEvent` SQLAlchemy model per
      design §8: `arrival_sequence` NOT NULL, `idempotency_key` UNIQUE,
      `revenue_delta NUMERIC(10,2) NOT NULL DEFAULT 0`. FKs: tenant → tenants
      (`ON DELETE RESTRICT`), vehicle → vehicles (`ON DELETE RESTRICT`). Column
      types must match the referenced PK types — confirm against the existing
      models, do not assume UUID vs. VARCHAR. Index on
      `(vehicle_id, arrival_sequence)` (for Task 2.2's query) and on
      `(tenant_id, position_timestamp)` (time-range queries).
- [x] `backend/app/models/boarding_passenger_event.py` — child model:
      `occupancy_event_id` FK (ON DELETE CASCADE), `passenger_id` FK → users
      (nullable, `ON DELETE SET NULL` — a deleted user must not delete the
      audit row), `event_type` ENUM('boarded','alighted').
- [x] Update `backend/app/models/__init__.py` — export both new models.
- [x] Alembic migration for both new tables.
- [x] Test: schema validates a representative payload and applies defaults for
      the optional fields; migration applies; `boarding_passenger_events` rows
      cascade-delete with the parent.
- [x] Commit: `backend: add occupancy schema, models, and migration`

### Task 2.2 — Latest-arrival-sequence endpoint
- [ ] Add `GET /api/v1/vehicles/{vehicle_id}/latest-arrival-sequence`
      (requires Task 2.1's `occupancy_events` table).
- [ ] Returns `{"data": {"arrival_sequence": N}}` with `N = MAX(arrival_sequence)`
      from `occupancy_events` for that vehicle, scoped to the caller's tenant.
- [ ] 404 with error code `vehicle_not_found` for an unknown vehicle or one
      belonging to another tenant; 404 with error code `no_arrival_records` for a
      known vehicle with no events yet.
- [ ] Test: returns max sequence; both 404 variants; tenant scoping.
- [ ] Commit: `backend: add latest-arrival-sequence endpoint`

### Task 2.3 — Confirm universal passenger pool endpoint
The backend **already exposes a passengers endpoint**; this task confirms
its contract and closes any gap, rather than adding a new route.

- [x] Read the existing endpoint in the backend (likely under
      `backend/app/api/` — locate it before editing). Record in the task
      commit:
      - Exact path and HTTP method.
      - Query parameters it accepts (in particular: does it accept
        `tenant_id`? If so, **the pool fetch must omit it** — see below).
      - Response shape (list of IDs vs. list of objects; field names).
      - Auth: what token/role it requires.
- [x] If the endpoint **requires** `tenant_id` and there is no tenant-agnostic
      mode, add a query-parameter path (e.g. `tenant_id` optional; omitted
      = universal pool) — do **not** add a second endpoint. Document the
      new behaviour in the endpoint's docstring.
- [x] If the endpoint's response is not a flat list of passenger IDs
      (`["u1", "u2", ...]`), add a thin projection in
      `passenger_service/passenger_pool/fetcher.py` (Task 3.4) that
      extracts IDs. Do **not** change the backend's response shape — other
      consumers may depend on it.
- [x] Confirm the endpoint returns **passengers** (`role=passenger`), not
      all users (drivers, admins). If it returns all users, add role
      filtering to the request in Task 3.4.
- [x] Test (backend): the endpoint returns the universal pool when no
      `tenant_id` is supplied, and the tenant-scoped subset when it is.
      The universal response is a superset of every tenant's response.
- [x] Commit: `backend: confirm/extend passenger pool endpoint for universal use`


### Task 2.4 — Error-code consistency sweep across backend services
**Scope.** Task 2.2 migrated the vehicle-not-found code from `"NOT_FOUND" → "vehicle_not_found"` in three services (vehicle_service, fleet_assignment, trip_service).
 The remaining ~27 **"NOT_FOUND"** sites across 11 services and two error-body shapes remain. This task completes the sweep.

- [ ] Decide whether the canonical error-body shape is `{"detail": {"code": ..., "message": ...}} (FastAPI default, ~28 sites) or {"error": {"code": ..., "message": ...}} (alert_service:55, tenant_service:83)`. Client-contract decision; confirm with the API consumer before proceeding.

- [ ] Rename every **"NOT_FOUND"** in `backend/app/services/` to a specific snake_case code:
      stop_not_found, driver_not_found, route_not_found, trip_not_found, user_not_found, tenant_not_found, tenant_admin_not_found, alert_not_found, maintenance_record_not_found, passenger_not_found, account_not_found, stops_not_found (for the plural case in route_service:186).

- [ ] Unify the error-body shape per the decision above.

- [ ] Add `backend/app/core/error_codes.py` with a named     constant per code, and reference constants rather than string literals in services (prevents recurrence).

- [ ] Update every test asserting on **"NOT_FOUND"** — currently `tests/test_tenant_service.py:86`, plus any others surfaced by running the suite.

- [ ] Verify no external client (frontend, API docs, integrations) matches on **"NOT_FOUND"** before merging. If any do, coordinate a compatible release or add a shim.

- [ ] Update API docs (if docs/ exists) to enumerate codes per endpoint.

- [ ] Commit: `backend: use resource-specific error codes for 404s.`

**Constraints.** No HTTP status changes, no error-message changes, no changes to response models or router signatures, no renaming of non-404 codes (FORBIDDEN, CONFLICT, VALIDATION_ERROR) — those may warrant their own task.

**Wire casing for error codes.** Error codes are snake_case in the body (`"vehicle_not_found"`, `"NOT_FOUND"`) even though response models serialize to camelCase (`arrivalSequence`, `pageSize`). Decide whether codes should follow the camelCase convention (`"vehicleNotFound"`) or stay snake_case (current). **Recommendation: stay snake_case** — error codes are identifiers, not display strings, and `gps_handler.py:54` already uses `"vehicle_not_found"` (snake_case). Snake_case codes are also easier to grep for in client code. Confirm and document; if camelCase is chosen, all codes and every test that asserts on them change together.

**Risk.** Client compatibility (any consumer matching on "NOT_FOUND"); test surface (expect 5–20 stale assertions to update, all mechanical).

---

## Phase 3 — passenger_service backend clients

### Task 3.1 — Route cache
- [ ] Create `passenger_service/route_cache/cache.py`. Mirror
      `gps_service/route_cache/cache.py` (copy, don't import), with these
      **deliberate differences**:
      1. **Sort by `sequence` after fetch.** `_fetch_route_stops` returns
         `sorted(stops, key=lambda s: s.sequence)`. The detector and
         simulation rely on `stops` being sequence-sorted; this is the
         only place the data enters the process, so it is the only place
         the sort belongs.
      2. **Re-export `RouteStop`** from `gps_service.models.gps_data`
         (or import it directly in callers) — do **not** define a
         duplicate. The model is `stop_id`, `latitude`, `longitude`,
         `sequence`; there is no `stop_index`.
      3. Keep the wire-to-model mapping `stop["order"] → sequence`
         exactly as gps_service does; add a one-line comment:
         `# backend wire field is "order"; model field is "sequence"`.
- [ ] Same API as gps_service: `get_route_stops(route_id, token) ->
      list[RouteStop]`, TTL 60s, `close()`.
- [ ] Test: mocked aiohttp; cache hit avoids second HTTP call; TTL expiry
      triggers refetch; missing stops handled; **returned stops are sorted
      by `sequence` even when the mocked response is out of order**; the
      `order → sequence` mapping is exercised.
- [ ] Commit: `passenger_service: add route cache`

### Task 3.2 — Vehicle map
- [ ] Create `passenger_service/vehicle_map/fetcher.py` with
      `VehicleMapFetcher(base_url, service_token, ...)` exposing
      `fetch_active_vehicles() -> list[VehicleInfo]` where `VehicleInfo`
      carries `vehicle_id`, `tenant_id`, `route_id`, `seating_capacity`,
      `current_occupancy` (from `currentOccupancy` / `current_occupancy`;
      missing → 0).
      Reuse `gps_service/vehicle_tracker/wire.py`'s `normalize_keys` approach
      (copy, don't import).
- [ ] Test: mocked HTTP; camelCase → snake_case; skips vehicles with no
      `route_id`; non-zero occupancy is read; missing field defaults to 0.
- [ ] Commit: `passenger_service: add vehicle map fetcher`

### Task 3.3 — Tenant identity
- [ ] Create `passenger_service/identity.py` with `resolve_tenant_id(...)`,
      mirroring `gps_service/vehicle_tracker/identity.py`.
- [ ] Test: mocked HTTP; parses `{data: {tenant_id: ...}}`.
- [ ] Commit: `passenger_service: add tenant identity resolver`

### Task 3.4 — Passenger pool fetcher
- [ ] Add `passenger_service/passenger_pool/fetcher.py` — a **single universal**
      `PassengerPoolFetcher` with `fetch_passenger_ids() -> list[str]` (calls
      Task 2.3's endpoint **without** `tenant_id` — passengers are not
      tenant-bound; see design §7 "Universal passengers") and
      `cached_ids() -> Sequence[str]`, refreshed on the same
      `VEHICLE_REFRESH_INTERVAL` as the vehicle map. There is no per-vehicle
      copy and no per-tenant copy of the pool.
- [ ] Test: mocked HTTP returns the expected list; **the request URL contains
      no `tenant_id` query parameter**; cache hit avoids a second call; refresh
      after the interval.
- [ ] Commit: `passenger_service: add passenger pool fetcher`

### Task 3.5 — Arrival-sequence client
- [ ] Create `passenger_service/vehicle_map/sequence_client.py` with
      `SequenceClient.fetch_latest_sequence(vehicle_id) -> int` calling
      Task 2.2's endpoint.
- [ ] Both 404 variants (`vehicle_not_found`, `no_arrival_records`) → `0`.
      Network errors and 5xx **raise** (the caller must not guess 0 on a
      transient failure).
- [ ] Test: mocked HTTP; 200 → value; both 404s → 0; 5xx / timeout raises.
- [ ] Commit: `passenger_service: add arrival-sequence client`

---

## Phase 4 — Detection and simulation

### Task 4.1 — Vehicle arrival state and store
- [ ] Create `passenger_service/detection/state.py` with the
      `VehicleArrivalState` dataclass (fields per design §3, including
      `armed`, `needs_synthesis`, `passengers`, `current_trip_id`; **no**
      `passenger_pool`), `VehicleSeed(arrival_sequence=0, onboard=0)`, and
      `VehicleStateStore`:
      - `has(vehicle_id)`
      - `get_or_create(vehicle_id, route_id, seed=None) -> StateLookup(state, released_ids)`
        - new vehicle: state from `seed`; `needs_synthesis = onboard > 0`
        - route change: **preserves `arrival_sequence` and `onboard`**, clears
          `passengers` and the last-stop/observation fields, re-arms, sets
          `needs_synthesis = onboard > 0`, returns the old real passenger IDs in
          `released_ids`
        - same route: returns the existing state, `released_ids = []`
      - `remove(vehicle_id) -> list[str]` returns the real IDs that were on board
- [ ] Test: initialises with and without a seed; persists across calls; seeded
      `arrival_sequence`/`onboard` applied; route change keeps the sequence,
      returns released IDs and sets `needs_synthesis`; `remove` returns IDs.
- [ ] Commit: `passenger_service: add per-vehicle arrival state`

### Task 4.2 — Stop arrival detection
- [ ] Create `passenger_service/detection/detector.py` with
      `detect_arrival(position, stops, state, now_mono, settings) -> RouteStop | None`.
      **Pure**: it does not mutate `state` (the orchestrator updates
      `arrival_sequence`, `last_stop_id`, `last_arrival_ts`, `armed`).
      `stops` is assumed sorted by `sequence` (Task 3.1 guarantees it);
      the detector iterates in that order and returns the **first**
      `RouteStop` satisfying near + slow and not suppressed. There is no
      index in the return value — callers use `stop.sequence`.
      Haversine distance, speed threshold, cooldown, and re-arm
      (`state.armed`); first match in `sequence` order.
- [ ] Test: near+slow → returns the `RouteStop` (assert on `stop_id`);
      near+fast → None; far+slow → None; repeat within cooldown → None;
      same stop after cooldown but `armed=False` → None; different stop
      → returns; **gapped sequence data (`[0, 1, 3]`) returns the stop
      whose `sequence` matches, not the array index**; state is not
      mutated.
- [ ] Commit: `passenger_service: add stop arrival detector`

### Task 4.3 — Passenger simulation
- [ ] Create `passenger_service/simulation/engine.py` implementing design §7:
      ```python
      make_rng(vehicle_id, arrival_sequence) -> random.Random
          # random.Random(int.from_bytes(sha256(f"{vehicle_id}:{arrival_sequence}".encode()).digest()[:8], "big"))

      simulate_passengers(
          state: VehicleArrivalState,
          current_sequence: int,        # the arriving stop's RouteStop.sequence
          stops: list[RouteStop],       # sorted by .sequence (Task 3.1)
          seating_capacity: int,
          passenger_pool: Sequence[str],
          excluded_ids: AbstractSet[str],
          params: SimulationParams,      # crush_capacity_factor, revenue_per_km
          rng: random.Random,
      ) -> SimulationResult
      ```
      SimulationParams is a frozen dataclass (crush_capacity_factor,
      revenue_per_km), constructed by the orchestrator from settings and
      passed in — the engine never reads settings directly.
      `SimulationResult` carries `boardings, alightings, onboard, revenue_delta,
      boarded_ids, alighted_ids, passengers`. The function is **pure**: it does not
      mutate `state` and reads no module-level state. The orchestrator owns and
      updates the global on-board set. Includes:
      - synthesis of anonymous passengers when `state.needs_synthesis`
        (`origin_index = randint(0, i-1)` or 0 at terminus,
        `dest_index = randint(max(i,1), len(stops)-1)`)
      - terminus crush loading (`target = randint(int(0.75c), int(1.10c))`)
      - mid-route loading (`board_cap = max(1, c // 6)`)
      - last stop (`len(stops) > 2`): everyone alights (revenue for all, real IDs in
        `alighted_ids`); `min(randint(3, 6), alighted_count)` re-board as anonymous
        through-passengers (counted in `boardings`)
      - last stop (`len(stops) <= 2`): all alight, no re-boards
      - per-passenger `origin_sequence` / `dest_sequence` and `distance_km`
        (summed haversine legs). Comparisons are
        `dest_sequence == current_sequence`, never array indices.
      - real-ID assignment from `passenger_pool` excluding remaining passengers'
        IDs, this stop's alighted IDs, and `excluded_ids`
      - revenue accumulation (`sum(distance_km of alighters) * revenue_per_km`)
- [ ] Test cases (each with a named seed):
      - Terminus loads within `[0.75c, 1.10c]`, all boarders have
        `dest_sequence > 0` (sequence, not array index)
      - Mid-route respects `capacity // 6` cap and available seats
      - Last stop: all alight; real IDs are in `alighted_ids`; 3–6 anonymous
        re-boards with `passenger_id=None`, `origin_index=0`; `onboard` equals the
        re-board count
      - Synthesis: `onboard` seeded without passengers → `len(passengers) == onboard`,
        no destination behind the current stop, `onboard` does not grow unboundedly
      - Real-ID subset respects `excluded_ids` and no same-stop reboard
      - Revenue: `sum(distance_km of alighters) * 60.0` matches `revenue_delta`
      - Determinism: same seed and inputs → identical output across two calls
      - Purity: input `state` is unchanged after the call
      - Constraints: `alightings <= onboard_before`, `boardings <= crush headroom`
        (+ through-passengers at the last stop), `onboard == len(passengers)`
      - Gapped sequence data (`[0, 1, 3]`): a passenger with   `dest_sequence=3` alights when `current_sequence=3`, not when
        the array index reaches 2.
- [ ] Commit: `passenger_service: add passenger simulation engine`

### Task 4.4 — Occupancy event model
- [x] Create `passenger_service/models/occupancy.py` with `OccupancyEvent`
      Pydantic model per design §5. Include `build_occupancy_event(...)`
      helper that constructs it with both timestamps and the derived
      `idempotency_key`.
- [x] Test: field validation, idempotency key format, timestamp serialisation.
- [x] Commit: `passenger_service: add occupancy event model`

### Task 4.5 — Occupancy event: per-passenger and revenue fields
(Follow-up to 4.4, whose first commit landed without these.)
- [ ] Add `boarded_passenger_ids: list[str] = Field(default_factory=list)`,
      `alighted_passenger_ids: list[str] = Field(default_factory=list)`,
      `revenue_delta: float = Field(default=0.0, ge=0.0)`; extend
      `build_occupancy_event(...)` to accept them.
- [ ] Test: optional fields default to empty/0.0 when omitted; round-trip with
      populated lists; negative `revenue_delta` rejected.
- [ ] Commit: `passenger_service: add per-passenger and revenue fields to occupancy event`

---

## Phase 5 — Orchestration

### Task 5.1 — Detector orchestration
> **Depends on:** Task 4.5 (the full `build_occupancy_event` signature
> — the orchestrator calls it with `boarded_passenger_ids`,
> `alighted_passenger_ids`, `revenue_delta`). Do not start this task
> against the Task 4.4 signature.
- [ ] Create `passenger_service/detection/orchestrator.py` with
      `ArrivalOrchestrator`. Given a `PositionEvent` and its collaborators
      (`state_store`, `route_cache`, `vehicle_map`, `sequence_client`,
      `pool_fetcher`, `publisher`, `settings`), it runs the detection loop and
      emits an occupancy event on arrival, following design §3 pseudocode.
      Pure logic, no MQTT wiring — takes already-parsed inputs. It:
      - owns `self._globally_on_board: set[str]` (instance attribute, shared by
        all vehicles)
      - on a vehicle's first sight, calls `sequence_client.fetch_latest_sequence`
        and builds a `VehicleSeed` with `VehicleInfo.current_occupancy`; if the
        call raises, **skips the event** (no guessing 0)
      - on `get_or_create`, removes `released_ids` from the global set
      - on arrival: increments `arrival_sequence`, updates `last_stop_id`,
        `last_arrival_ts`, `armed=False`, calls `simulate_passengers(...)` with
        `passenger_pool=pool_fetcher.cached_ids()` and
        `excluded_ids=self._globally_on_board`, applies `passengers`/`onboard`,
        clears `needs_synthesis`, updates the global set (remove `alighted_ids`,
        add `boarded_ids`), calls `build_occupancy_event(...)` with the returned
        IDs and `revenue_delta`, and publishes
      - after every event, re-arms when the bus is beyond the radius of the last
        stop, and updates `last_*` observations
- [ ] Test: inject mocked collaborators; occupancy event published on detected
      arrival with expected fields; no publish on non-arrival; first-sight
      seeding applies sequence and onboard; sequence-client failure skips the
      event; route change releases IDs and keeps the sequence; two vehicles sharing one orchestrator never hold the same real passenger ID at the same time; global set updated from the result; `release_vehicle(id)` removes the vehicle's state and releases its real IDs from the global set (returns them).
- [ ] Commit: `passenger_service: add detection orchestrator`

### Task 5.2 — Periodic refresh
- [ ] Add a background task that refreshes the vehicle map **and** the passenger
      pool every `VEHICLE_REFRESH_INTERVAL` seconds, mirroring
      `gps_service/api/app.py`'s `_sync_loop`. For vehicles that disappeared from
      the map, call `orchestrator.release_vehicle(vehicle_id)` — it owns both
      `state_store.remove` and the global-set subtraction. Do not reach into
      `_globally_on_board` directly.
- [ ] The refresh loop takes a `stop_event: asyncio.Event` parameter (created by
      the app lifespan in Task 6.1) and waits via
      `asyncio.wait_for(stop_event.wait(), timeout=interval)` so shutdown is
      immediate rather than delayed by up to one interval.
- [ ] Test: mock fetchers; assert periodic calls; vehicles that left the map are
      removed and their IDs released; shutdown event stops the loop.
- [ ] Commit: `passenger_service: add periodic vehicle map and pool refresh`

---

## Phase 6 — Service entry point

### Task 6.1 — FastAPI app with lifespan
- [ ] Create `passenger_service/api/app.py` with `create_app()` and a
      `lifespan` that:
      - resolves tenant
      - connects MQTT publisher and subscriber
      - builds route cache, vehicle map fetcher, passenger pool fetcher and
        sequence client, and the orchestrator
      - does the initial vehicle-map and passenger-pool fetch
      - subscribes to `gps/+/+/position`
      - starts the periodic refresh task
      - on shutdown: stops refresh, unsubscribes, disconnects MQTT, closes route cache
      (per-vehicle sequence/onboard seeding happens lazily inside the orchestrator)
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

## Phase 7 — Backend consumption

Cutover rule (design §10): the legacy simulation and the new pipeline must never
both be live. The subscriber is registered **last** (Task 7.5), after the legacy
loop is disabled (Task 7.4).

### Task 7.1 — Occupancy MQTT subscriber
- [ ] `backend/app/services/occupancy_mqtt_subscriber.py`, mirroring
      `gps_mqtt_subscriber.py`. Subscribes to `gps/+/+/occupancy`, validates
      against `OccupancyEvent`, hands to `OccupancyService.record(...)`.
- [ ] Test: mocked client + mocked service; invalid payload is logged and
      dropped; valid payload calls service.
- [ ] Commit: `backend: add occupancy MQTT subscriber`

### Task 7.2 — Occupancy service
- [ ] `backend/app/services/occupancy_service.py` with
      `record(db, event: OccupancyEvent) -> None`:
      1. Look up the vehicle (tenant-scoped); unknown → log WARNING and skip.
      2. `INSERT INTO occupancy_events ... ON CONFLICT (idempotency_key) DO NOTHING`.
         Track `inserted` (bool) via `RETURNING id`.
      3. If `inserted`:
         - Bulk `INSERT INTO boarding_passenger_events` for each
           `boarded_passenger_ids` (event_type='boarded') and
           `alighted_passenger_ids` (event_type='alighted').
         - `UPDATE vehicles SET current_occupancy = event.onboard, updated_at = now()`.
         - If `event.revenue_delta > 0`: `upsert_daily_analytics(...)`.
         - If `event.onboard >= seating_capacity * CAPACITY_ALERT_THRESHOLD`
           (0.9), emit a `capacity` alert, deduplicated per
           `(vehicle_id, 'capacity')` for `CAPACITY_ALERT_DEDUP_SECONDS` (300).
           Constants live next to the existing alert thresholds. If the alert
           type is a DB enum, include the migration here.
      All writes in one transaction. A duplicate delivery skips everything in
      step 3, including the alert.
- [ ] Test: dedup on idempotency key (children, vehicle update, revenue, alert all
      skipped on duplicate); capacity alert at threshold; no alert below
      threshold; second alert within 5 minutes suppressed; unknown vehicle is
      logged and skipped; per-passenger child rows cascade-delete with parent;
      revenue accumulates.
- [ ] Commit: `backend: add occupancy service with idempotent writes`

### Task 7.3 — WebSocket broadcast
- [ ] After each **inserted** occupancy commit, call `manager.publish_to_tenant(...)`
      with the existing `vehicle_occupancy_updated` message shape
      (`vehicleId`, `currentOccupancy`, `seatingCapacity`,
      `remainingSeats = max(0, seatingCapacity - currentOccupancy)`). Today this
      broadcast fires from `passenger_simulation.py`, which is deleted in Phase 8,
      so the new service must emit the same message.
- [ ] Test: mocked broadcaster; commit triggers a broadcast with the expected
      envelope; duplicate delivery does not.
- [ ] Commit: `backend: broadcast occupancy updates over WebSocket`

### Task 7.4 — Cutover: disable legacy simulation
- [ ] Disable the legacy simulation loop (feature flag, or remove its scheduler
      registration), confirming the exact mechanism in code. Do not delete the
      module yet.
- [ ] Test: with the flag off, the legacy tick does not run and nothing else in
      the backend suite changes.
- [ ] Commit: `backend: disable legacy passenger simulation loop`

### Task 7.5 — Wire subscriber into app startup
- [ ] Register the occupancy subscriber in the backend's FastAPI lifespan,
      alongside the existing GPS subscriber.
- [ ] Test: app starts, both subscriptions are registered.
- [ ] Commit: `backend: wire occupancy subscriber into app lifespan`

---

## Phase 8 — Verification and cleanup

### Task 8.1 — Cutover verification (gate before deletion)
- [ ] `docker compose down && docker compose up --build`; wait for one full route loop.
- [ ] `SELECT COUNT(*) FROM occupancy_events;` grows.
- [ ] `SELECT COUNT(*) FROM boarding_passenger_events;` grows.
- [ ] `SELECT vehicle_id, current_occupancy FROM vehicles;` plausible non-zero values.
- [ ] `analytics_daily.revenue` grows once per stop (legacy writer is really off).
| `backend/app/services/boarding_service.py` | `record_single_boarding` / `record_stop_events` — writes the legacy `boarding_records` table | Same, **after** the Task 8.1 equivalence check: for a sampled vehicle+stop, boardings/alightings counts in `boarding_records` and in `boarding_passenger_events` agree over the same `arrival_sequence` range |
- [ ] Commit: `docs: record cutover verification` — paste the query outputs (counts, occupancy snapshot, revenue delta, equivalence-check results) into the commit message.

### Task 8.2 — Delete the legacy simulation and boarding pipeline
- [ ] Before deleting, `rg` for `completed_loops` / `planned_loops` writes in
      `passenger_simulation.py`; list them in the commit message (they stop
      updating — see the loop-counting disclaimer in design §10).
- [ ] Remove `backend/app/services/passenger_simulation.py` (confirm exact path).
- [ ] Remove any scheduled task or background loop that drove it (the one
      disabled in Task 7.4).
- [ ] Remove `backend/app/services/boarding_service.py`
      (`record_single_boarding`, `record_stop_events`).
- [ ] Remove `backend/app/models/boarding_record.py`.
- [ ] Alembic migration dropping `boarding_records`, `boarding_event_type_enum`,
      and `idx_boarding_*` indexes.
- [ ] Remove `backend/tests/test_passenger_simulation.py` and any
      `test_boarding_*` tests.
- [ ] Add a comment in `backend/app/models/trip.py` noting the table is
      vestigial in v1.
- [ ] Test: full backend suite passes; `alembic downgrade`/`upgrade` round-trip clean;
      `rg "passenger_simulation|boarding_records" backend/ --glob '!**/alembic/versions/**'` has no hits.
- [ ] Commit: `backend: remove legacy passenger simulation and boarding records`

### Task 8.3 — Documentation
- [ ] Add `docs/architecture.md` explaining the full system: backend,
      gps_service, passenger_service, MQTT topics, data flow, the
      occupancy → `occupancy_events` / `boarding_passenger_events` → WebSocket
      pipeline, and the reasoning behind the split.
- [ ] Include a **Known limitations** section carrying forward design §12, and a
      **loop-counting disclaimer**: gps_service has no loop counting today, so
      `planned_loops` / `completed_loops` are stale or unset until it does.
- [ ] Update root `README.md` to reflect the three-service layout and the
      `docker compose up` demo flow.
- [ ] Commit: `docs: add architecture overview`

---

## Phase 9 — Trip lifecycle **(deferred — do not start; out of scope for the demo)**

Not part of the demo. `state.current_trip_id` is threaded through the
simulation in v1 but stays `None`. When this phase is picked up:

- [ ] Define trip start/end conditions (first stop of a route vs. last).
- [ ] `passenger_service/simulation/trip.py` — start a trip on terminus
      departure, end on last-stop arrival.
- [ ] Add `trip_id: str | None` to `OccupancyEvent` (optional, default None).
- [ ] Backend: `trips` table gets populated again; `occupancy_events.trip_id`
      FK added.
- [ ] Frontend: trip history view.

---

## Testing checklist (run before declaring the project complete)

- [ ] `cd passenger_service && pytest -q` — all green
- [ ] `cd gps_service && pytest -q` — all green
- [ ] `cd backend && ./.venv/Scripts/python.exe -m pytest -q` — all green
- [ ] `docker compose down && docker compose up --build` — all services healthy
- [ ] `curl http://localhost:8001/health` — GPS service up
- [ ] `curl http://localhost:8002/health` — Passenger service up
- [ ] Subscribe to `gps/+/+/occupancy` — events flow within one route loop
- [ ] Query `SELECT COUNT(*) FROM occupancy_events;` — grows over time
- [ ] Query `SELECT COUNT(*) FROM boarding_passenger_events;` — grows over time
- [ ] Query `SELECT vehicle_id, current_occupancy FROM vehicles;` — plausible non-zero
- [ ] Frontend: occupancy indicators update live
- [ ] `rg "passenger_simulation|boarding_records" backend/ --glob '!**/alembic/versions/**'` — no hits
- [ ] Ctrl+C on `docker compose` — clean shutdown, no orphaned processes

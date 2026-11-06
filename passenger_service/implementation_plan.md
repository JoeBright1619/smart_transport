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
- [x] Add `GET /api/v1/vehicles/{vehicle_id}/latest-arrival-sequence`
      (requires Task 2.1's `occupancy_events` table).
- [x] Returns `{"data": {"arrival_sequence": N}}` with `N = MAX(arrival_sequence)`
      from `occupancy_events` for that vehicle, scoped to the caller's tenant.
- [x] 404 with error code `vehicle_not_found` for an unknown vehicle or one
      belonging to another tenant; 404 with error code `no_arrival_records` for a
      known vehicle with no events yet.
- [x] Test: returns max sequence; both 404 variants; tenant scoping.
- [x] Commit: `backend: add latest-arrival-sequence endpoint`

### Task 2.3a — Confirm universal passenger pool endpoint
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

### Task 2.3b — Universal service-token principal

The machine consumer (`passenger_service`, Task 3.4) needs `GET /api/v1/passengers`, but every `ServiceToken` today is bound to a `tenant_id`, and `_resolve_service_token` always returns a `Tenant`. This task adds a tenant-agnostic service-token path so the consumer stops impersonating a superadmin JWT.

- [x] Migration: make `service_tokens.tenant_id` nullable. `downgrade` must `raise RuntimeError` if any `tenant_id IS NULL` rows exist (do not delete them).
- [x] `ServiceToken.tenant_id` → `Mapped[str | None]`, `nullable=True`. Docstring notes NULL = universal token.
- [x] `issue_token(..., universal: bool = False)` — `universal=True` sets `tenant_id=None`. No change to `hash_token` / `generate_plaintext_token` / `verify_token` / `has_scope`.
- [x] New dependency `require_superadmin_or_universal_service(scope)` in `app/core/dependencies.py`, returning `Principal(kind="superadmin" | "universal_service", tenant: Tenant | None)`:
  - `X-Service-Token` + scope match + `tenant_id IS NULL` → `universal_service`.
  - `X-Service-Token` + scope match + `tenant_id NOT NULL` → 403 (a tenant-bound token must not become universal by accident).
  - JWT + `role == "superadmin"` → `superadmin`.
  - Anything else → 401/403 via `_raise_error`.
  - Do **not** modify `get_tenant_or_service` or `_resolve_service_token` — existing callers must be unaffected.
- [x] `list_passengers` dependency changes from `require_role("superadmin")` to `Depends(require_superadmin_or_universal_service("passengers:read_universal"))`. Handler body unchanged. Docstring line added: "Auth: superadmin JWT, or universal service token scoped `passengers:read_universal`."
- [x] `conftest.py`: add `make_service_token` fixture wrapping `issue_token` (kwargs: `tenant_id`, `universal`, `name`, `scopes`, `dev`; returns `(row, plaintext)`). Existing `test_service_token.py` must keep passing unchanged.
- [x] Test: universal token → `GET /api/v1/passengers` returns 200 with all passengers.
- [x] Test: universal token missing `passengers:read_universal` scope → 403.
- [x] Test: tenant-bound token (with that scope) → 403 (rejects accidental upgrade).
- [x] Test: tenant-bound token on `GET /api/v1/vehicles` still 200 (regression: `get_tenant_or_service` unchanged).
- [x] Test: superadmin JWT on `GET /api/v1/passengers` still 200 (regression: 2.3a unchanged).
- [x] Commit: `backend: add universal service-token principal and allow passenger pool access`

**Notes for the implementer.**

- Token format stays `stk_live_` / `stk_dev_` — no distinct universal prefix.
- `passengers:read_universal` is a sensitive scope; document that in `service_token_service.py`'s `issue_token` docstring.
- Grep for `service_token.tenant_id` usages after applying; only `_resolve_service_token` reads it today and it's deliberately untouched, but confirm nothing else assumes non-null.

### Task 2.4 — Phase 1: Extract shared error helpers

**Scope.** Extract the duplicated `_error_detail` / `_raise_error` helpers
into a shared module and consolidate redundant raise call sites. No
code-string changes.

**Deliverable.**

- [x] Create `backend/app/core/errors.py` with `_error_detail` (returns
      `dict[str, Any]`) and `_raise_error` (returns `NoReturn`).
- [x] Delete duplicate `def _error_detail` from 15 files and
      `def _raise_error` from 3 files (`core/dependencies.py`,
      `routers/auth.py`, `services/tenant_service.py`); import from
      `app.core.errors`.
- [x] `main.py`'s `_error_response` uses `_error_detail` (the builder, not
      the raiser) — the one legitimate builder call site.
- [x] `alert_service.py`'s inline `{"error": {...}}` dict replaced with
      `_raise_error(...)`.
- [x] Consolidate redundant raise sites:
      `raise HTTPException(..., detail=_error_detail(...))` →
      `_raise_error(...)`. Behavior-preserving.
- [x] `pytest backend/tests -q` — 460 passed.
- [x] Commit: `backend: extract shared error helpers and consolidate raise call sites`


**Commit.**

```
backend: extract shared error helpers and consolidate raise call sites

_error_detail was duplicated in 15 files with only cosmetic annotation
drift. _raise_error was duplicated in 3 files with a real annotation
inconsistency (NoReturn vs None despite both raising unconditionally).
Both now live in app/core/errors.py and are imported everywhere.

Redundant raise call sites
(raise HTTPException(..., detail=_error_detail(...))) consolidated to
_raise_error(...). Behavior-preserving: the emitted HTTPException detail
is byte-identical. main.py's _error_response continues to use
_error_detail (it builds a JSONResponse, does not raise) — this is the
one legitimate builder call site.

No status, message, response-model, or router-signature changes.
alert_service's inline {"error": {...}} dict now routes through
_raise_error so the wire shape cannot drift.

Refs: Task 2.4 (phase 1 of 3)
```

**Risk.** Single large mechanical diff (~18 files). Mitigated by per-file
incremental test runs, `_raise_error` vs `_error_detail` greps, and a
manual 500-handler test.

### Task 2.4 — Phase 2: `error_codes` module

**Scope.** Add `backend/app/core/error_codes.py` with named snake_case
constants. Pure addition — no caller changes, no behavior change.

**Deliverable.**

- [x] Create `backend/app/core/error_codes.py` with the constants below.
- [x] No imports, no caller changes elsewhere. The module is standalone.
- [x] `pytest backend/tests -q` — 460 passed (unchanged).
- [x] Commit: `backend: add error_codes module for resource-specific error identifiers`

**Module contents.**

- **404 — resource not found:**
  `STOP_NOT_FOUND`, `DRIVER_NOT_FOUND`, `ROUTE_NOT_FOUND`,
  `TRIP_NOT_FOUND`, `USER_NOT_FOUND`, `TENANT_NOT_FOUND`,
  `TENANT_ADMIN_NOT_FOUND`, `ALERT_NOT_FOUND`,
  `MAINTENANCE_RECORD_NOT_FOUND`, `PASSENGER_NOT_FOUND`,
  `ACCOUNT_NOT_FOUND`, `STOPS_NOT_FOUND`, `VEHICLE_NOT_FOUND`,
  `NO_ARRIVAL_RECORDS`.
- **Specific conditions:**
  `EMAIL_ALREADY_EXISTS`, `ALREADY_VERIFIED`, `INVALID_OTP`,
  `INVALID_TOKEN`, `TENANT_INACTIVE`, `TENANT_REQUIRED`.
- **Generic HTTP-class codes** (`FORBIDDEN`, `CONFLICT`, `BAD_REQUEST`,
  `UNAUTHORIZED`) documented in a header comment as unchanged and
  intentionally absent from the module.

**Module docstring should state:**
- Codes are snake_case identifiers.
- Codes are the client-facing discriminator in `{"error": {"code": ..., "message": ...}}`.
- Renaming a code requires client coordination.
- Generic HTTP-class codes are deliberately not named here — client outcome
  is identical regardless of casing, so renaming gains nothing.

**File list.**

- `backend/app/core/error_codes.py` (new)

**Commit.**

```
backend: add error_codes module for resource-specific error identifiers

Pure addition: defines snake_case constants for 404s and specific
conditions so service call sites can reference them instead of literals
in phase 3. Generic HTTP-class codes (FORBIDDEN, CONFLICT, BAD_REQUEST,
UNAUTHORIZED) are deliberately omitted — renaming them gains no
information for clients and would require per-site decisions.

No caller changes, no behavior change.

Refs: Task 2.4 (phase 2 of 3)
```

**Risk.** None. New file, no imports, no callers yet.


### Task 2.4 — Phase 3: Replace code literals with constants

**Scope.** Replace `"NOT_FOUND"` and specific-condition literals with the
constants from phase 2. Generic HTTP-class codes stay unchanged.

**Deliverable.**

- [x] Replace every `"NOT_FOUND"` at a resource-specific site with the
      corresponding `error_codes.X_NOT_FOUND`.
- [x] Replace specific-condition literals with constants.
- [x] Promote "email already exists" everywhere to `EMAIL_ALREADY_EXISTS`.
- [x] Retroactively switch `vehicle_service.py`'s `"vehicle_not_found"` /
      `"no_arrival_records"` to constants.
- [x] Leave generic codes unchanged.
- [x] Leave `gps_handler.py:54` unchanged.
- [x] Update tests asserting on changed codes.
- [x] `pytest backend/tests -q` — expect 460 passed.
- [x] Commit: `backend: use named error codes throughout services and routers`

**Call-site mapping.**

404s:
- `arrival_service.py:102`, `:189` → `STOP_NOT_FOUND`
- `driver_service.py:65` → `DRIVER_NOT_FOUND`
- `fleet_assignment.py:52` → `VEHICLE_NOT_FOUND`; `:70` → `DRIVER_NOT_FOUND`
- `maintenance_service.py:71` → `MAINTENANCE_RECORD_NOT_FOUND`;
  `:87` → `VEHICLE_NOT_FOUND`
- `passenger_report_service.py:36` → `PASSENGER_NOT_FOUND`
- `passenger_service.py:105`, `:154` → `ACCOUNT_NOT_FOUND`
- `route_service.py:105` → `STOP_NOT_FOUND`; `:186` → `STOPS_NOT_FOUND`;
  `:265`, `:288` → `ROUTE_NOT_FOUND`
- `superadmin_service.py:90`, `:116`, `:143` → `TENANT_NOT_FOUND`;
  `:156` → `TENANT_ADMIN_NOT_FOUND`; `:269` → `PASSENGER_NOT_FOUND`
- `trip_service.py:73` → `TRIP_NOT_FOUND`; `:93` → `VEHICLE_NOT_FOUND`;
  `:116` → `DRIVER_NOT_FOUND`
- `user_service.py:80`, `:204` → `USER_NOT_FOUND`
- `vehicle_service.py:71` → `VEHICLE_NOT_FOUND`; `"no_arrival_records"`
  → `NO_ARRIVAL_RECORDS`; `:266` stays `"CONFLICT"` (generic, unchanged)
- `alert_service.py`'s `"alert_not_found"` → `ALERT_NOT_FOUND`

Specific conditions:
- `passenger_service.py:111`, `:160` → `ALREADY_VERIFIED`
- `passenger_service.py:125` → `INVALID_OTP`
- `user_service.py:195`, `:216` → `INVALID_TOKEN`
- `tenant_service.py:49` → `EMAIL_ALREADY_EXISTS`
- `user_service.py:106`, `:126`, `:150` → `EMAIL_ALREADY_EXISTS`
  (was `"CONFLICT", "Email already exists"` — unification)

Leave unchanged:
- `FORBIDDEN` at `users.py:81`, `passenger_report_service.py:41`,
  `superadmin_service.py:274`, `user_service.py:241`, `:261`
- `CONFLICT` at `route_service.py:348`, `trip_service.py:121`,
  `vehicle_service.py:266`
- `BAD_REQUEST` at `user_service.py:290`
- `UNAUTHORIZED` and other generic codes in `core/dependencies.py`
- `gps_handler.py:54`'s `"vehicle_not_found"` (internal status, not HTTP
  error code)

**Test updates.**
- `tests/test_tenant_service.py:86`: `"NOT_FOUND"` → `"tenant_not_found"`.
- Any other assertions surfaced by the run — paste failures, do not guess.

**File list.**
- `backend/app/core/error_codes.py` (import only — no change if phase 2
  already created it)
- 13 service files: `alert_service.py`, `arrival_service.py`,
  `driver_service.py`, `fleet_assignment.py`, `maintenance_service.py`,
  `passenger_report_service.py`, `passenger_service.py`, `route_service.py`,
  `superadmin_service.py`, `tenant_service.py`, `trip_service.py`,
  `user_service.py`, `vehicle_service.py`
- `backend/tests/test_tenant_service.py`
- any other tests surfaced

**Commit.**

```
backend: use named error codes throughout services and routers

Replaces "NOT_FOUND" and specific-condition literals with constants
from app.core.error_codes. Generic HTTP-class codes (FORBIDDEN,
CONFLICT, BAD_REQUEST, UNAUTHORIZED) stay as literals — client outcome
is identical regardless of casing, so renaming gains nothing.

"Email already exists" is unified to EMAIL_ALREADY_EXISTS at all four
sites (previously "CONFLICT" in user_service.py, already
EMAIL_ALREADY_EXISTS in tenant_service.py).

gps_handler.py's "vehicle_not_found" is unchanged — it is an internal
dict status, not an HTTP error code.

Client-visible change: consumers matching on "NOT_FOUND",
"ALREADY_VERIFIED", "INVALID_OTP", "INVALID_TOKEN", "TENANT_INACTIVE",
"TENANT_REQUIRED", or "EMAIL_ALREADY_EXISTS" must update in a
coordinated release.

No status, message, response-model, or router-signature changes.

Refs: Task 2.4 (phase 3 of 3)
```

**Risk.**
- Client compatibility: coordinate with frontend before merging.
- Test surface: expect ~1–10 mechanical assertion updates. Run the suite
  and paste failures as they appear.

---

## Phase 3 — passenger_service backend clients

### Task 3.1 — Route cache
- [x] Create `passenger_service/route_cache/cache.py`. Mirror
      `gps_service/route_cache/cache.py` (copy, don't import), with these
      **deliberate differences**:
      1. **Sort by `sequence` after fetch.** `_fetch_route_stops` returns
         `sorted(stops, key=lambda s: s.sequence)`. The detector and
         simulation rely on `stops` being sequence-sorted; this is the
         only place the data enters the process, so it is the only place
         the sort belongs.
      2. Keep the wire-to-model mapping `stop["order"] → sequence`
         exactly as gps_service does; add a one-line comment:
         `# backend wire field is "order"; model field is "sequence"`.
- [x] **Define `RouteStop` locally** in `passenger_service/models/route_stop.py`,
      mirroring `gps_service.models.gps_data.RouteStop` (same fields:
      `stop_id`, `latitude`, `longitude`, `sequence`; no `stop_index`).
      Do not import across the service boundary — the brief's original
      "re-export from gps_service" wording conflicts with the architectural
      boundary in the project context (§1). The local mirror keeps the
      two services decoupled.
- [x] Same API as gps_service: `get_route_stops(route_id, token) ->
      list[RouteStop]`, TTL 60s, `close()`.
- [x] Test: mocked aiohttp; cache hit avoids second HTTP call; TTL expiry
      triggers refetch; missing stops handled; **returned stops are sorted
      by `sequence` even when the mocked response is out of order**; the
      `order → sequence` mapping is exercised.
- [x] Commit: `passenger_service: add route cache`

### Task 3.2 — Vehicle map
- [x] Create `passenger_service/vehicle_map/fetcher.py` with
      `VehicleMapFetcher(base_url, service_token, ...)` exposing
      `fetch_active_vehicles() -> list[VehicleInfo]` where `VehicleInfo`
      carries `vehicle_id`, `tenant_id`, `route_id`, `seating_capacity`,
      `current_occupancy` (from `currentOccupancy` / `current_occupancy`;
      missing → 0).
      Reuse `gps_service/vehicle_tracker/wire.py`'s `normalize_keys` approach
      (copy, don't import).
- [x] Test: mocked HTTP; camelCase → snake_case; skips vehicles with no
      `route_id`; non-zero occupancy is read; missing field defaults to 0.
- [x] Commit: `passenger_service: add vehicle map fetcher`


### Task 3.0 — Universal fleet endpoints (backend)

**Why this task exists.** Tasks 3.3 and 3.5 are deferred on the same blocker: passenger_service operates cross-tenant (universal passenger pool, fleet-wide vehicle map per design §7), but the current `/api/v1/vehicles*` endpoints are tenant-anchored and user-JWT-only. A universal service token cannot call them; a tenant-scoped token can only see its own tenant. This task adds the universal, service-token-accessible fleet endpoints that unblock both.

Mirrors Task 2.3b's passenger pattern (`passengers:read_universal` + `require_superadmin_or_universal_service`).

- [x] Add three service-layer functions in `backend/app/services/vehicle_service.py`:
  - `get_all_active_vehicles(db, status_filter, page, page_size) -> tuple[list[Vehicle], int]` — same query as `get_vehicles` **minus the tenant filter**. Returns `(vehicles, total)` for pagination.
  - `get_vehicle_by_id_any_tenant(db, vehicle_id) -> Vehicle` — same as `get_vehicle_by_id` minus tenant filter; raises 404 `vehicle_not_found`.
  - `get_latest_arrival_sequence_any_tenant(db, vehicle_id) -> int` — same as `get_latest_arrival_sequence` minus tenant filter; same `vehicle_not_found` / `no_arrival_records` 404 behavior.
  - Scope string `"vehicles:read_universal"` used as a literal at call sites (matching `passengers:read_universal` — no constants module exists).

- [x] Create `backend/app/routers/service_vehicles.py`:
  - `router = APIRouter(prefix="/api/v1/service/vehicles", tags=["service"])`
  - `GET ""` → `PaginatedResponse[VehicleRead]`, guard `require_superadmin_or_universal_service(required_scope="vehicles:read_universal")`. Query params: `status`, `page`, `page_size` (mirror the user endpoint).
  - `GET "/{id}"` → `APIResponse[VehicleRead]`, same guard.
  - `GET "/{id}/latest-arrival-sequence"` → `APIResponse[LatestArrivalSequenceRead]`, same guard.

- [x] Register in `backend/main.py`:

  ```python
  app.include_router(service_vehicles.router)
  ```

  alongside the other `include_router` calls.

- [x] Tests in `backend/tests/service/test_service_vehicles.py` (create `tests/service/__init__.py` if absent):
  - **List endpoint**
    - superadmin JWT → 200
    - universal token with `vehicles:read_universal` → 200
    - universal token without scope → 403
    - tenant-bound token with scope → 403 (explicitly rejected per §5)
    - no auth → 401
    - cross-tenant: two tenants each with an active vehicle; both ids present in `data`
  - **Detail endpoint**
    - universal token → 200 with `tenantId` in the body
    - 404 `vehicle_not_found` for a missing id
    - scope gates (as above)
  - **Sequence endpoint**
    - 200 with `arrivalSequence` int
    - 404 `vehicle_not_found` for a missing id
    - 404 `no_arrival_records` for an existing vehicle with no occupancy events
    - scope gates (as above)

- [x] Commit split:
  1. `backend: add universal fleet service functions` — service layer + tests for the three functions, no endpoints yet.
  2. `backend: add /service/vehicles endpoints` — router + main.py wiring + endpoint tests.
  3. `docs: unblock Tasks 3.3 and 3.5 in passenger_service plan` — update `implementation_plan.md`; 3.3 and 3.5 lose the DEFERRED marker, add a note that both now call `/api/v1/service/vehicles*`.

**Backend contract (post-task):**

| **Endpoint** | **Auth** | **Response** | **Errors** |
| :--- | :--- | :--- | :--- |
| `GET /api/v1/service/vehicles?status=&page=&page_size=` | superadmin JWT or universal token `vehicles:read_universal` | `PaginatedResponse[VehicleRead]` (camelCase; includes `tenantId`) | 401 unauthenticated, 403 wrong-scope / tenant-bound |
| `GET /api/v1/service/vehicles/{id}` | same | `APIResponse[VehicleRead]` | 404 `vehicle_not_found` |
| `GET /api/v1/service/vehicles/{id}/latest-arrival-sequence` | same | `APIResponse[LatestArrivalSequenceRead]` | 404 `vehicle_not_found`, 404 `no_arrival_records` |

**Follow-on (unblocked, not in this task):**

- Re-issue passenger_service's universal token with `scopes="passengers:read_universal,vehicles:read_universal"` (`.env` + DB change only; `has_scope` supports comma-lists).
- Task 3.2 follow-up: point `VehicleMapFetcher` at `/api/v1/service/vehicles` (one-line URL change + test fixture update).
- Task 3.5 becomes writable.
- Task 3.3 becomes writable (per your call — see below).

**Test count target:** current 460 + ~13–16 new tests → **473–476 passed** in `backend/tests`.

### Task 3.3 — Tenant identity
- [x] Create `passenger_service/identity.py` with `resolve_tenant_id(...)`,
      mirroring `gps_service/vehicle_tracker/identity.py`.
- [x] Test: mocked HTTP; parses `{data: {tenant_id: ...}}`.
- [x] Commit: `passenger_service: add tenant identity resolver`

Backend endpoints in Task 3.0. Client implementation unblocked.

### Task 3.4 — Passenger pool fetcher
- [x] Add `passenger_service/passenger_pool/fetcher.py` — a **single universal**
      `PassengerPoolFetcher` with `fetch_passenger_ids() -> list[str]` (calls
      Task 2.3's endpoint **without** `tenant_id` — passengers are not
      tenant-bound; see design §7 "Universal passengers") and
      `cached_ids() -> Sequence[str]`, refreshed on the same
      `VEHICLE_REFRESH_INTERVAL` as the vehicle map. There is no per-vehicle
      copy and no per-tenant copy of the pool.
      GET /api/v1/passengers?page=N&page_size=M — paginated.

#### Backend Contract (Confirmed in Task 2.3a + 2.3b):

##### Endpoint

`GET /api/v1/passengers?page=N&page_size=M`

- Supports pagination using `page` and `page_size` query parameters.

##### Authentication

**Interim authentication:**
- Header: `X-Service-Token: <universal token>`. Universal tokens are tenant-agnostic service tokens issued via    `issue_token(db, universal=True, scopes="passengers:read_universal", ...)`.
- Response: `{"data": [{"id": str, ...}], "meta": {"total": int, "page": int, "pageSize": int}}`.
- Fetcher must paginate until `len(accumulated) >= meta.total`, then project `id` from each item.
- No `tenant_id` parameter — passengers are universal.
- `passenger_service` config needs: `BACKEND_BASE_URL` (already exists for other calls), `PASSENGER_POOL_SERVICE_TOKEN` (the plaintext universal token, secret-managed like other service tokens).

##### Response Format

```json
{
  "data": [
    {
      "id": "string"
    }
  ],
  "meta": {
    "total": 100,
    "page": 1,
    "pageSize": 20
  }
}
```
- [x] Test: mocked HTTP returns the expected list; **the request URL contains
      no `tenant_id` query parameter**; cache hit avoids a second call; refresh
      after the interval.
- [x] Commit: `passenger_service: add passenger pool fetcher`

### Task 3.5 — Arrival-sequence client
- [x] Create `passenger_service/vehicle_map/sequence_client.py` with
      `SequenceClient.fetch_latest_sequence(vehicle_id) -> int` calling
      Task 2.2's endpoint.
- [x] Both 404 variants (`vehicle_not_found`, `no_arrival_records`) → `0`.
      Network errors and 5xx **raise** (the caller must not guess 0 on a
      transient failure).
- [x] Test: mocked HTTP; 200 → value; both 404s → 0; 5xx / timeout raises.
- [x] Commit: `passenger_service: add arrival-sequence client`

---

## Phase 4 — Detection and simulation

### Task 4.1 — Vehicle arrival state and store
- [x] Create `passenger_service/detection/state.py` with the
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
- [x] Test: initialises with and without a seed; persists across calls; seeded
      `arrival_sequence`/`onboard` applied; route change keeps the sequence,
      returns released IDs and sets `needs_synthesis`; `remove` returns IDs.
- [x] Commit: `passenger_service: add per-vehicle arrival state`

### Task 4.2 — Stop arrival detection
- [x] Create `passenger_service/detection/detector.py` with
      `detect_arrival(position, stops, state, now_mono, settings) -> RouteStop | None`.
      **Pure**: it does not mutate `state` (the orchestrator updates
      `arrival_sequence`, `last_stop_id`, `last_arrival_ts`, `armed`).
      `stops` is assumed sorted by `sequence` (Task 3.1 guarantees it);
      the detector iterates in that order and returns the **first**
      `RouteStop` satisfying near + slow and not suppressed. There is no
      index in the return value — callers use `stop.sequence`.
      Haversine distance, speed threshold, cooldown, and re-arm
      (`state.armed`); first match in `sequence` order.
- [x] Test: near+slow → returns the `RouteStop` (assert on `stop_id`);
      near+fast → None; far+slow → None; repeat within cooldown → None;
      same stop after cooldown but `armed=False` → None; different stop
      → returns; **gapped sequence data (`[0, 1, 3]`) returns the stop
      whose `sequence` matches, not the array index**; state is not
      mutated.
- [x] Commit: `passenger_service: add stop arrival detector`

### Task 4.3 — Passenger simulation
- [x] Create `passenger_service/simulation/engine.py` implementing design §7:
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
- [x] Test cases (each with a named seed):
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
- [x] Commit: `passenger_service: add passenger simulation engine`

### Task 4.4 — Occupancy event model
- [x] Create `passenger_service/models/occupancy.py` with `OccupancyEvent`
      Pydantic model per design §5. Include `build_occupancy_event(...)`
      helper that constructs it with both timestamps and the derived
      `idempotency_key`.
- [x] Test: field validation, idempotency key format, timestamp serialisation.
- [x] Commit: `passenger_service: add occupancy event model`

### Task 4.5 — Occupancy event: per-passenger and revenue fields
Folded into 4.4's reconcile commit. Kept in the plan for history; no
separate work remains.
- [x] Add `boarded_passenger_ids: list[str] = Field(default_factory=list)`,
      `alighted_passenger_ids: list[str] = Field(default_factory=list)`,
      `revenue_delta: float = Field(default=0.0, ge=0.0)`; extend
      `build_occupancy_event(...)` to accept them.
- [x] Test: optional fields default to empty/0.0 when omitted; round-trip with
      populated lists; negative `revenue_delta` rejected.
- [x] Commit: `passenger_service: add per-passenger and revenue fields to occupancy event`

---

## Phase 5 — Orchestration

### Task 5.1 — Detector orchestration
> **Depends on:** Task 4.5 (the full `build_occupancy_event` signature
> — the orchestrator calls it with `boarded_passenger_ids`,
> `alighted_passenger_ids`, `revenue_delta`). Do not start this task
> against the Task 4.4 signature.
- [x] Create `passenger_service/detection/orchestrator.py` with
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
- [x] Test: inject mocked collaborators; occupancy event published on detected
      arrival with expected fields; no publish on non-arrival; first-sight
      seeding applies sequence and onboard; sequence-client failure skips the
      event; route change releases IDs and keeps the sequence; two vehicles sharing one orchestrator never hold the same real passenger ID at the same time; global set updated from the result; `release_vehicle(id)` removes the vehicle's state and releases its real IDs from the global set (returns them).
- [x] Commit: `passenger_service: add detection orchestrator`

### Task 5.2 — Periodic refresh
- [x] Add a background task that refreshes the vehicle map **and** the passenger
      pool every `VEHICLE_REFRESH_INTERVAL` seconds, mirroring
      `gps_service/api/app.py`'s `_sync_loop`. For vehicles that disappeared from
      the map, call `orchestrator.release_vehicle(vehicle_id)` — it owns both
      `state_store.remove` and the global-set subtraction. Do not reach into
      `_globally_on_board` directly.
- [x] The refresh loop takes a `stop_event: asyncio.Event` parameter (created by
      the app lifespan in Task 6.1) and waits via
      `asyncio.wait_for(stop_event.wait(), timeout=interval)` so shutdown is
      immediate rather than delayed by up to one interval.
- [x] Test: mock fetchers; assert periodic calls; vehicles that left the map are
      removed and their IDs released; shutdown event stops the loop.
- [x] Commit: `passenger_service: add periodic vehicle map and pool refresh`

---

## Phase 6 — Service entry point

### Task 6.1 — FastAPI app with lifespan

**Preconditions** (land before this task):
- vehicle_map/fetcher.py points at /api/v1/service/vehicles (not /api/v1/vehicles)
- PASSENGER_POOL_SERVICE_TOKEN carries both passengers:read_universal
  and vehicles:read_universal scopes

- [x] Create `passenger_service/api/__init__.py` (empty) and
      `passenger_service/api/app.py` with `create_app()` and a `lifespan`
      that:
      - ~~resolves tenant~~ — REMOVED. passenger_service is cross-tenant;
        no startup tenant resolution. Tenant comes from each inbound
        position event's payload (§3).
      - constructs the MQTT publisher and subscriber
      - builds route cache, vehicle map fetcher, passenger pool fetcher
        and sequence client (all take base_url=settings.BACKEND_BASE_URL,
        service_token=settings.PASSENGER_POOL_SERVICE_TOKEN), and the
        orchestrator
      - ~~does the initial vehicle-map and passenger-pool fetch~~ — REMOVED.
        refresh_loop fetches at t=0; no duplicate. To avoid dropping the
        very first positions, start the loop and await its first iteration
        before subscribing.
      - subscribes to `gps/+/+/position`
      - starts the periodic refresh task
      - on shutdown: stops refresh (stop_event.set(), await task with
        timeout), unsubscribes + disconnects MQTT, closes route cache,
        vehicle map fetcher, sequence client, and pool fetcher.
      (per-vehicle sequence/onboard seeding happens lazily inside the
      orchestrator)
- [x] Add `/health` returning `{"data": {"status": "ok"}, "meta": null,
      "error": null}` (envelope-wrapped per §5; not bare).
- [x] Add `/status` returning
      `{"data": {"mqtt_connected": bool, "vehicles_tracked": int,
      "events_published": int, "uptime_seconds": float}, "meta": null,
      "error": null}` — DROPPED `tenant` (no single tenant).
      Optionally add `vehicles_with_state` and `globally_on_board`
      if those accessors are added to the orchestrator/state store.
      Requires an `events_published` counter on ArrivalOrchestrator.
- [x] Test: mocked collaborators AND mocked MQTT; app starts, subscribes,
      starts refresh, both endpoints return envelope shapes, shutdown
      completes cleanly.
- [x] Commit: `passenger_service: add FastAPI app with health endpoints`

### Task 6.2 — Entry point
- [x] Create `passenger_service/main.py` as a thin uvicorn runner
      mirroring `gps_service/main.py`.
- [x] Commit: `passenger_service: add service entry point`

---

## Phase 7 — Backend consumption

Cutover rule (design §10): the legacy simulation and the new pipeline must never
both be live. The subscriber is registered **last** (Task 7.5), after the legacy
loop is disabled (Task 7.4).

### Task 7.1 — Occupancy MQTT subscriber
- [x] `backend/app/services/occupancy_mqtt_subscriber.py`, mirroring
      `gps_mqtt_subscriber.py`. Subscribes to `gps/+/+/occupancy`, validates
      against `OccupancyEvent`, hands to `OccupancyService.record(...)`.
- [x] Test: mocked client + mocked service; invalid payload is logged and
      dropped; valid payload calls service.
- [x] Commit: `backend: add occupancy MQTT subscriber`

### Task 7.2 — Occupancy service
- [x] `backend/app/services/occupancy_service.py` with
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
- [x] Test: dedup on idempotency key (children, vehicle update, revenue, alert all
      skipped on duplicate); capacity alert at threshold; no alert below
      threshold; second alert within 5 minutes suppressed; unknown vehicle is
      logged and skipped; per-passenger child rows cascade-delete with parent;
      revenue accumulates.
- [x] Commit: `backend: add occupancy service with idempotent writes`

### Task 7.3 — WebSocket broadcast
- [x] After each **inserted** occupancy commit, call `manager.publish_to_tenant(...)`
      with the existing `vehicle_occupancy_updated` message shape
      (`vehicleId`, `currentOccupancy`, `seatingCapacity`,
      `remainingSeats = max(0, seatingCapacity - currentOccupancy)`). Today this
      broadcast fires from `passenger_simulation.py`, which is deleted in Phase 8,
      so the new service must emit the same message.
- [x] Test: mocked broadcaster; commit triggers a broadcast with the expected
      envelope; duplicate delivery does not.
- [x] Commit: `backend: broadcast occupancy updates over WebSocket`

### Task 7.4 — Cutover: disable legacy simulation
- [x] Disable the legacy simulation loop (feature flag, or remove its scheduler
      registration), confirming the exact mechanism in code. Do not delete the
      module yet.
- [x] Test: with the flag off, the legacy tick does not run and nothing else in
      the backend suite changes.
- [x] Commit: `backend: disable legacy passenger simulation loop`

### Task 7.5 — Wire subscriber into app startup
- [x] Register the occupancy subscriber in the backend's FastAPI lifespan,
      alongside the existing GPS subscriber.
- [x] Test: app starts, both subscriptions are registered.
- [x] Commit: `backend: wire occupancy subscriber into app lifespan`

---

## Phase 8 — Verification and cleanup

### Task 8.1 — Cutover verification (gate before deletion)
- [x] `docker compose down && docker compose up --build`; wait for one full route loop.
- [x] `SELECT COUNT(*) FROM occupancy_events;` grows.
- [x] `SELECT COUNT(*) FROM boarding_passenger_events;` grows.
- [x] `SELECT vehicle_id, current_occupancy FROM vehicles;` plausible non-zero values.
- [x] `analytics_daily.revenue` grows once per stop (legacy writer is really off).
| `backend/app/services/boarding_service.py` | `record_single_boarding` / `record_stop_events` — writes the legacy `boarding_records` table | Same, **after** the Task 8.1 equivalence check: for a sampled vehicle+stop, boardings/alightings counts in `boarding_records` and in `boarding_passenger_events` agree over the same `arrival_sequence` range |
- [x] Commit: `docs: record cutover verification` — paste the query outputs (counts, occupancy snapshot, revenue delta, equivalence-check results) into the commit message.

### Task 8.2 — Remove legacy passenger simulation [DONE]
- [x] `rg` for `completed_loops` / `planned_loops` writes in
      `passenger_simulation.py`. **Result: no hits** — loop counting lives
      in `route_simulation.advance_vehicle`, unaffected by this task.
- [x] Remove `backend/app/websocket/passenger_simulation.py` (path is
      `websocket/`, not `services/` — brief was wrong).
- [x] Remove `passenger_simulation` imports and no-op call sites from
      `backend/app/websocket/route_simulation.py` and
      `backend/app/services/route_tracking_service.py` (the latter's
      `_handle_stop_arrival` becomes unreachable; removed with the import).
- [x] Trim `backend/app/services/boarding_service.py`: remove
      `record_single_boarding` and `record_stop_events` (only callers were
      the deleted module). **Keep** `list_boardings` and
      `list_my_boardings` — `routers/boardings.py` serves
      `GET /api/v1/boardings` and `/me`, consumed by
      `frontend/src/app/services/boarding.service.ts:18`.
- [x] Remove `backend/tests/test_passenger_simulation.py`.
- [x] Remove `backend/tests/test_websocket_occupancy.py` (targeted only
      the deleted `simulate_passengers_at_stop`; equivalent behavior
      tested in `passenger_service/tests/simulation/test_engine.py`).
- [x] Strip the now-inert `_PUBLISH` patches
      (`app.websocket.passenger_simulation.manager.publish_to_tenant`)
      from `test_journey_rounds.py`, `test_fuel_model.py`,
      `test_simulation_trip_dedup.py`. The `route_simulation.advance_vehicle`
      loops remain live; only the dead patch wrapper is removed.
- [x] Remove `record_stop_events`-dependent tests from
      `test_capacity_alerts.py` and `passengers/test_stats.py`.
- [x] Test: full backend suite passes; `rg "passenger_simulation" backend/app/`
      returns no hits.
- [x] Commit: `backend: remove legacy passenger simulation`

**Deferred (out of scope for 8.2):**
- **`boarding_records` table drop** — `routers/boardings.py` still serves
  `/api/v1/boardings` and `/me`; the frontend consumes `/me`. The table is
  now frozen historical data (4,753 rows). Dropping requires either a data
  migration to `boarding_passenger_events` or a frontend change to retire
  `/boardings/me`. Tracked as a future cleanup once that decision is made.
- **`boarding_record.py` model** — still read by `list_boardings` and
  `list_my_boardings`.
- **`trip.py` vestigial-table comment** — cosmetic; not added.

**Related work in other services:**
- **`route_simulation.py` / `simulation_runner.py` removal + consumer
  rewires** (arrival_service, tracking, trip_service) lives in
  **gps_service's implementation plan, Phase 5** — the cutover that
  originated when gps_service replaced the vehicle simulation. Not
  duplicated here. See `gps_service/implementation_plan.md` (or wherever
  it lives) Tasks 5.1–5.6.
- **Documentation** (architecture overview, README update) is Task 8.3
  below.

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

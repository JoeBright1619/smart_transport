# Frontend & Backend Feature Enhancements

> **How to use this document:**
> - Work through tasks **strictly in order** — each phase depends on the previous.
> - After completing a task, tick its checkbox: `[ ]` → `[x]`
> - Keep the **Current Task Pointer** below updated after each completed task.
> - **DO NOT proceed to the next task without explicit user approval.**
> - Use the `master` branch for all tasks and use commit messages exactly as provided.
> - **File size rule:** No implementation file should exceed 250–300 lines. If a file grows beyond this, split it using named imports/exports rather than adding more code to the same file.
> - **Tests rule:** Every backend task ships its tests in the same change (pytest-asyncio, in-memory SQLite) — not as a follow-up.
> - **Verification gate (every task):** Before ticking a task complete, run the **full** backend suite from `backend/` — `./.venv/Scripts/python.exe -m pytest -q` — and confirm **all tests green** (baseline: 298 passing). For any task touching frontend code, also run `npm run build` in `frontend/` and confirm zero new errors. Do not tick a task if the full suite is not green.

---

## Current Task Pointer

**Next task:** All tasks complete (Phases 6 & 7 done).

After completing any task, update this pointer to the next unchecked task before stopping to report.

---

> [!IMPORTANT]
> **Agent Rule:** After completing each task, stop and report:
> 1. What was implemented
> 2. Any decisions made or problems encountered
> 3. A commit message for what was implemented
> 4. Then ask: _"Ready to proceed to the next task?"_
> Do not move forward until the user confirms.

---

## Background — Why These Tasks Exist

An investigation of the fleet subsystem found that **`vehicles.status == "active"` is being used as an implicit, unguarded shared state that four screens (Fleet, Dispatch, Drivers, Route Management) all read and write with different rules.** There is no single owner of the journey lifecycle, so the screens conflict:

- **Fleet** starts a journey by flipping `status = "active"` via `PATCH /vehicles` with **no validation** (no driver, no route, no GPS, no double-booking check).
- **Dispatch** starts a journey by creating and activating a `Trip` — this path *is* guarded.
- **The simulation** reads `status == "active"` and independently mints its *own* `Trip` rows, which it may never complete (in-memory loop state, no crash recovery), leaving orphaned `active` trips.
- **Route Management** toggles `route.is_active`, but that flag is enforced **nowhere** — disabled routes still appear on the map and stay assignable.

These phases make the **trip/journey lifecycle the single source of truth**, fix the concrete data-integrity bugs, and unblock car registration.

---

## Test Coverage & Safety Net

**Current baseline: 26 backend test files, 298 tests, all passing** (~110s), run with `./.venv/Scripts/python.exe -m pytest -q` from `backend/`. Coverage of the areas these phases touch:

| Area | Existing tests | Strength for our work |
|------|----------------|-----------------------|
| Vehicles CRUD + auth/roles | `test_vehicles.py` (18), `test_vehicle_capacity.py` (7) | Strong on create/patch/delete, roles, 422s, capacity, occupancy-on-completion. **No** GPS assertions, **no** driver-assignment-conflict test. |
| Drivers CRUD + status | `test_drivers.py` (19) | Strong on roles/validation and delete-while-on-trip. **No** double-assignment or off-duty-block test. |
| Trips lifecycle | `test_trips.py` (14) | Covers create/activate/invalid-transition. **No** orphaned-trip / simulation-dedup test. |
| Routes CRUD | `test_routes.py` (16) | Covers CRUD + roles. **No** `is_active` enforcement test. |
| Tenant isolation | `test_tenant_isolation.py` (20) | Strong cross-tenant guard coverage. |
| Simulation / occupancy | `test_websocket_occupancy.py`, `test_passenger_simulation.py` | Occupancy + boarding paths covered. |

**Important blind spot (this is why the registration 500 slipped through):** the test suite builds its schema from the **models** (`Base.metadata.create_all` on in-memory SQLite in `tests/conftest.py`), **not** from the Alembic migration chain. So a green suite does **not** prove the real Postgres DB matches the models — schema/migration drift (exactly Issue 5) is invisible to `pytest`. Task 6.1 therefore also verifies against a **migrated** DB, and each task adds new tests to close the gaps marked "No…" above.

**Frontend:** there is **no** JS test runner configured (only `dev`/`build`/`preview` scripts). Frontend verification is `npm run build` (zero new type/build errors) plus manual spot-check.

---

## Phase 6 — Critical Fleet Bugs (Blocking & Data Integrity)

---

### Task 6.1 — Fix Vehicle Registration 500 (Apply Pending Migrations & Harden Create)

**Files:** `backend/alembic/versions/*` (apply, do not rewrite history), `backend/app/services/vehicle_service.py`, `backend/main.py`, `backend/app/routers/vehicles.py` (read only)

**Root cause (confirmed):** The running database is at Alembic revision `0013_add_vehicle_capacity_fields`, but the code expects head `0017`. The `vehicles.capacity` column is still `NOT NULL` with no default, while the current `Vehicle` model no longer writes `capacity` on INSERT (commit `f3e90ee` dropped it and added migration `0017`). Every `POST /api/v1/vehicles` therefore raises `NotNullViolation` → unhandled `IntegrityError` → 500. Because Starlette's 500 handler sits **outside** `CORSMiddleware` (`main.py`), the 500 carries no `Access-Control-Allow-Origin` header, so the browser mislabels it a CORS error. Migrations `0014`–`0017` are all unapplied (missing capacity-alert enum, notification threshold, boarding `route_id`, and the capacity drop).

Fix steps:
1. **Apply migrations to head:** run `alembic upgrade head` against `smart_transport_system_db` and verify `alembic_version` = `0017` and the `capacity` column is gone. Document this as the required deploy step. Confirm seeded rows still load and `POST /vehicles` now succeeds.
2. **Make 500s CORS-safe (so real errors surface instead of a misleading CORS message):** ensure error/500 responses carry CORS headers. Either move the catch-all exception handling so it runs inside the CORS layer, or add the `Access-Control-Allow-Origin` header on the 500 `JSONResponse`. Keep the `DEBUG`-gated message behaviour intact.
3. **Fix the tenant-scoped duplicate check:** `vehicle_service.create_vehicle` checks `registration_number` uniqueness **without** filtering by `tenant_id`, contradicting "unique within the tenant" and producing spurious cross-tenant 409s. Add `Vehicle.tenant_id == tenant_id` to the existence query.
4. **Guardrail:** add a lightweight startup log/warning (or a note in the README/run docs) that fails loudly if the DB is behind head, so schema drift is caught before it 500s in the browser again.
5. Tests: a backend test that `create_vehicle` succeeds and returns an `idle`, no-GPS vehicle; a test that a duplicate registration **within the same tenant** 409s while the **same registration in a different tenant** is allowed.

**Note on the `401 on /drivers/drv-005`:** this is a *separate* problem — an expired 15-minute access token whose refresh also failed (not CORS, not the vehicles bug). It is addressed as a session/token concern in Task 6.4's notes, not here.

**Branch:** `master`
**Commit:** `fix: vehicle registration 500 via db migration, tenant-scoped duplicate check and cors-safe errors`

**Verify:** full backend suite green — `./.venv/Scripts/python.exe -m pytest -q` (298+ passing). Also confirm `POST /vehicles` succeeds against the migrated DB.

- [x] Task 6.1 complete

---

### Task 6.2 — GPS Coordinate Policy for Non-Offline Vehicles

**Files:** `backend/app/services/vehicle_service.py`, `backend/app/services/trip_service.py`, `backend/app/models/vehicle.py` (read only), a small stop-picking helper (new, e.g. `backend/app/services/fleet_position.py`)

**Current behaviour / issue:** New vehicles are created with `lat = lng = NULL` (no GPS). GPS is only ever populated when a trip activates (seeded from the route's first stop) or by the seed. Two problems: (a) idle/maintenance vehicles that have never run a trip have **no** GPS at all; (b) `current_location` is `null` for any vehicle that has never run, so the fleet map cannot show it.

**Decision (FINAL — agreed with product owner):** *Every vehicle always retains a GPS position — including `offline`.* GPS represents the vehicle's **last-known position**, never cleared. This is deliberate for safety/security: if a vehicle goes `offline` because of an accident, a disabled tracker, or a breakdown, the **last coordinates before it went dark are exactly what we need to keep.** `offline` therefore means "not transmitting / last-known" — not "no position." GPS is never nulled by any code path.

Fix steps:
1. Add a helper that returns a starting position near a random active bus stop for a tenant (pick a `Stop`, optionally jitter a few metres). Reuse the existing `Stop` model (`backend/app/models/route.py`).
2. **On create** (`create_vehicle`): assign a starting GPS near a bus stop for **every** vehicle regardless of status (a brand-new vehicle's "last-known position" is its depot/starting stop). `lat/lng` are never left NULL.
3. **On status transition** (`update_vehicle`): GPS is **never cleared** on any transition, including `→ offline`. It stays at its last value.
4. **On trip completion/cancellation** (`trip_service.update_trip`): the vehicle drops to `idle` and keeps its last position (snap to the nearest/last stop is acceptable), rather than leaving mid-route stale coordinates. Never null it.
5. Confirm `advance_vehicle`/`simulation_runner` still only move `active` vehicles with a route — idle/offline vehicles with GPS must remain stationary at their last-known point (the map may render non-active vehicles dimmed/"last seen", a frontend concern).
6. Backfill: existing rows with NULL GPS (e.g. current seed vehicles that never ran) should receive a starting position — do this in the seed's idempotent path and/or a one-off in the create/update flow so no live vehicle is positionless.
7. Tests: a created vehicle of **any** status (including `offline`) has non-null GPS; setting an active vehicle offline **retains** its GPS (does not null it); an idle vehicle with GPS is not moved by the simulation.

**Branch:** `master`
**Commit:** `feat: vehicles always retain a last-known bus-stop gps position across all statuses`

**Verify:** full backend suite green — `./.venv/Scripts/python.exe -m pytest -q` (298+ passing).

- [x] Task 6.2 complete

---

### Task 6.3 — Prevent Assigning a Driver Already Bound to Another Vehicle

**Files:** `backend/app/services/driver_service.py`, `backend/app/services/vehicle_service.py`, `backend/app/models/driver.py` / `vehicle.py` (read only)

**Current behaviour / issue:** `Driver.vehicle_id` and `Vehicle.driver_id` are two independent, unconstrained nullable FKs with no reciprocal sync. Assignment happens via **two** unguarded paths — `driver_service.update_driver` (sets `driver.vehicle_id`) and `vehicle_service.update_vehicle` (sets `vehicle.driver_id`) — and **neither checks whether the driver is already assigned to another car**. The same driver can be bound to two vehicles at once. A driver cannot physically drive two cars simultaneously, so this is a real integrity bug.

Fix steps:
1. On assigning a driver to a vehicle (both paths), reject with a 409 if that driver already has a non-deleted `vehicle_id` pointing at a **different** vehicle (and/or another vehicle already has `driver_id` == this driver). Return a clear message (translatable code, e.g. `DRIVER_ALREADY_ASSIGNED`).
2. Keep both FK sides **in sync**: assigning driver→vehicle also sets vehicle→driver (and vice-versa); unassigning clears both sides. Consider centralising this in one helper used by both services so the two screens can't drift.
3. Allow re-assigning the **same** pairing (idempotent) and allow moving a driver once they are unassigned/off-duty.
4. Tests: assigning a driver already bound to another vehicle 409s; assigning to the same vehicle is idempotent; a successful assignment sets both `driver.vehicle_id` and `vehicle.driver_id`; unassigning clears both.

**Branch:** `master`
**Commit:** `fix: reject assigning a driver already bound to another vehicle and keep both fk sides in sync`

**Verify:** full backend suite green — `./.venv/Scripts/python.exe -m pytest -q` (298+ passing).

- [x] Task 6.3 complete

---

### Task 6.4 — Reconcile Orphaned Trips Blocking Driver Off-Duty

**Files:** `backend/app/services/driver_service.py`, `backend/app/websocket/route_trip_records.py`, `backend/app/core/seed.py` or a new startup reconcile step, `backend/app/services/trip_service.py`

**Current behaviour / issue:** `update_driver` blocks off-duty when any `Trip` for the driver is `scheduled`/`active` — correct in intent. But the simulation (`route_trip_records.start_trip`) creates `active` trips out of band and **never** completes them if the process restarts or the vehicle is deactivated mid-loop (`complete_trip` depends on volatile in-memory `state["current_trip_id"]`), and it never resets `driver.status`/`driver.vehicle_id`. The result: **orphaned `active` trips block a driver from ever going off-duty** — exactly the "Diane Ingabire / Emmanuel Ntwali cannot be set to off-duty" report, even after trips and assignments were removed.

Fix steps:
1. **Fix the simulation completion path** so `complete_trip` (and vehicle deactivation) resets the driver (`status → available`, `vehicle_id → None`) and vehicle links, matching the dispatch `update_trip` cleanup — the two producers must leave the same consistent end state.
2. **Add orphan reconciliation:** on startup (and/or in the simulation tick), mark `active`/`scheduled` trips whose vehicle is no longer `active` (or no longer has that route/driver) as `cancelled`/`completed`, and reset the affected driver/vehicle. This removes stale rows that permanently block off-duty.
3. Make the off-duty check resilient: it should only be blocked by trips whose vehicle is genuinely running that driver — not by orphaned rows. (Depends on step 1/2 keeping data consistent.)
4. **Session/token note (the `401`):** document that the observed 401 on driver edits is an expired 15-minute access token with a failed refresh, not a driver bug. If desired, add a lightweight frontend guard that redirects to login on a failed refresh instead of surfacing a raw error. (Keep scope small — token lifetime tuning is out of scope here.)
5. Tests: a driver with an orphaned `active` trip (vehicle not active) can be set off-duty after reconciliation; a driver with a genuinely running trip cannot; simulation trip completion resets driver + vehicle.

**Branch:** `master`
**Commit:** `fix: reconcile orphaned simulation trips so drivers can return to off-duty`

**Verify:** full backend suite green — `./.venv/Scripts/python.exe -m pytest -q` (298+ passing).

- [x] Task 6.4 complete

---

## Phase 7 — Unified Journey Lifecycle (Single Source of Truth)

> Goal: make the **trip/dispatch layer the single owner** of starting and stopping journeys, so Fleet, Dispatch, Drivers and Route Management stop fighting over `vehicles.status`. Do not start Phase 7 until Phase 6 lands.

---

### Task 7.1 — Make Journey Start/Stop a Single Guarded Operation; Enforce `active ⇒ driver + route + GPS`

**Files:** `backend/app/services/vehicle_service.py`, `backend/app/services/trip_service.py`, `frontend/src/app/components/pages/fleet-management/*`, `frontend/src/app/components/pages/dispatch/*`

**Current behaviour / issue:** `active` means "on a journey" (the simulation and the map both key off `status == "active"` + `route_id` + GPS). But Fleet can flip `status = "active"` via `PATCH /vehicles` with **no** driver/route/GPS/double-booking validation, producing an "active" vehicle the simulation silently ignores (null GPS). Two independent "start journey" mechanisms exist for the same vehicle row.

**Decision (recommended):** starting/stopping a journey goes through **one** guarded operation owned by the trip lifecycle. Fleet no longer sets `active` directly.

Fix steps:
1. In `update_vehicle`, **reject setting `status = "active"` directly** (or route it through the trip-activation service) unless the vehicle has a driver, an active route, and GPS. The clean way to become active is to have/activate a `Trip`.
2. Expose a single "start journey" action (create+activate trip) usable from **both** Fleet and Dispatch, so Fleet's "start" button and Dispatch's scheduler call the same guarded backend path. Fleet's status dropdown stops being a journey trigger.
3. Ensure stopping a journey (idle/offline) always goes through the same lifecycle cleanup (trip closed, driver/vehicle reset) — no divergent paths.
4. Tests: `PATCH /vehicles {status:"active"}` on a vehicle with no driver/route is rejected; starting a journey via the unified action activates a trip, sets driver `on-trip`, vehicle `active` with GPS; double-start on the same vehicle is rejected from **both** entry points.

**Branch:** `master`
**Commit:** `feat: single guarded journey start/stop, active status requires driver route and gps`

**Verify:** full backend suite green — `./.venv/Scripts/python.exe -m pytest -q` (298+ passing); plus `npm run build` in `frontend/` with zero new errors.

- [x] Task 7.1 complete

---

### Task 7.2 — De-duplicate Simulation Trip Records & Sync State on Completion

**Files:** `backend/app/websocket/route_trip_records.py`, `backend/app/websocket/route_simulation.py`, `backend/app/services/trip_service.py`

**Current behaviour / issue:** When Dispatch activates a trip, an `active` `Trip` already exists. Once the vehicle runs, the simulation crosses stop index 0 and `start_trip` inserts a **second** `Trip` with no dedup, while `complete_trip` only closes the simulation's own in-memory trip id — so the original dispatch trip can stay `active` forever and analytics double-count.

Fix steps:
1. `start_trip` must **reuse** an existing open (`scheduled`/`active`) trip for that vehicle+route instead of minting a new one; only create a trip if none exists (e.g. a Fleet-started journey with no dispatch trip).
2. `complete_trip` must close the actual owning trip and run the shared cleanup (driver + vehicle reset from Task 6.4).
3. Verify Dispatch's "active trips" list and analytics no longer double-count.
4. Tests: running a dispatched journey through a full simulated loop results in exactly **one** trip transitioning `scheduled → active → completed`; no duplicate active rows remain.

**Branch:** `master`
**Commit:** `fix: simulation reuses the owning trip instead of creating duplicate trip records`

**Verify:** full backend suite green — `./.venv/Scripts/python.exe -m pytest -q` (298+ passing).

- [x] Task 7.2 complete

---

### Task 7.3 — Enforce `route.is_active` Across Map, Assignment & Dispatch

**Files:** `backend/app/services/route_service.py`, `backend/app/services/vehicle_service.py`, `backend/app/services/trip_service.py`, `frontend/src/app/components/pages/VehicleTracking.tsx`, `frontend/src/app/components/pages/**/VehicleMapView.tsx`, `frontend/src/app/components/pages/fleet-management/*`

**Current behaviour / issue:** `route.is_active` is toggled in Route Management but enforced **nowhere**. Disabled routes are still returned by the unfiltered map/list query, still drawn as polylines, and still selectable in Fleet's route-assignment dropdown; the backend never rejects assigning or dispatching an inactive route. Only Dispatch filters client-side (cosmetic).

Fix steps:
1. **Backend:** reject assigning an `is_active = false` route to a vehicle (`update_vehicle`) and reject creating/activating a trip on an inactive route (`create_trip`). Return a translatable code (e.g. `ROUTE_INACTIVE`).
2. **Map:** filter disabled routes out of the tracking/map query (or pass `isActive=true`) so disabled routes are not drawn. Decide whether a disabled route should still be *viewable* for reference — if so, render it visually distinct (dimmed) but never assignable; otherwise omit it.
3. **Fleet assignment dropdown:** populate only active routes (mirror Dispatch's `schedulableRoutes`), sourced from a single shared helper so all screens agree.
4. Tests: assigning an inactive route 409s; creating a trip on an inactive route 409s; the map/list query excludes inactive routes (or flags them per the chosen decision).

**Branch:** `master`
**Commit:** `feat: enforce route is_active across map, assignment and dispatch`

**Verify:** full backend suite green — `./.venv/Scripts/python.exe -m pytest -q` (298+ passing); plus `npm run build` in `frontend/` with zero new errors.

- [x] Task 7.3 complete

---

## Implementation Summary

| Phase | Title | Tasks | Status |
|-------|-------|-------|--------|
| 6 | Critical Fleet Bugs (Blocking & Data Integrity) | 6.1, 6.2, 6.3, 6.4 | Complete |
| 7 | Unified Journey Lifecycle (Single Source of Truth) | 7.1, 7.2, 7.3 | Complete |

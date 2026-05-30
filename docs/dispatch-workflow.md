# Dispatch Workflow — Analysis & Gap Report

> Written as part of Task 9.4. Updated after Task 9.5 to reflect implemented fixes.
> Remaining open items are tracked under Task 9.6 (tracking status ownership).

---

## How the Workflow Works Today

### 1. Data Loading

`useDispatchManagement` fetches all four collections in parallel on mount:
- `GET /api/v1/trips?pageSize=100` — all non-deleted trips for the tenant
- `GET /api/v1/vehicles?pageSize=100` — all vehicles
- `GET /api/v1/drivers?pageSize=100` — all drivers
- `GET /api/v1/routes?pageSize=100` — all routes (including inactive)

Derived lists are computed via `useMemo`:
- `activeTrips` — trips with `status === 'active'`
- `scheduledTrips` — trips with `status === 'scheduled'`
- `availableVehicles` — vehicles with `status === 'idle'`
- `availableDrivers` — drivers with `status === 'available'`

### 2. Resource Eligibility

The `ScheduleTripDialog` is passed only `availableVehicles` and `availableDrivers`, so only
`idle` vehicles and `available` drivers are selectable. This is correct in principle, but the
eligibility check happens purely on the vehicle/driver `status` field — it does not consider
whether a resource already has a **scheduled** (future) trip assigned.

### 3. Scheduling a Trip

`ScheduleTripDialog` collects: vehicle, route, driver, scheduled start, scheduled end.
It validates that `scheduledEnd > scheduledStart` before submitting.
Only active routes appear in the route dropdown.
On submit it calls `createTrip(payload)` which hits `POST /api/v1/trips`.

Backend (`trip_service.create_trip`):
- Validates the selected vehicle belongs to the tenant, is not deleted, and has `status === 'idle'`.
- Validates the selected driver belongs to the tenant, is not deleted, and does not have `status === 'on-trip'`.
- Rejects with `409 CONFLICT` if either resource already has a `scheduled` or `active` trip.
- Creates a `Trip` row with `status = 'scheduled'`.
- **Reserves** the resources: sets `vehicle.driver_id`, `vehicle.route_id`, and `driver.vehicle_id`.
- Writes an audit log entry.

Frontend after creation: calls `loadDispatch()` to refresh all resources, so the booked vehicle
and driver immediately disappear from the available-resource lists.

### 4. Trip Lifecycle

Valid transitions (enforced in `VALID_TRANSITIONS` dict in `trip_service`):

| From | To | Side-effects |
|---|---|---|
| `scheduled` | `active` | Sets `driver.status = 'on-trip'`, `vehicle.status = 'active'`, stamps `actual_start` |
| `scheduled` | `cancelled` | Resets driver → `available` (if was `on-trip`), vehicle → `idle` (if was `active`) |
| `active` | `completed` | Resets driver → `available`, vehicle → `idle`, stamps `actual_end`, increments `driver.total_trips` |
| `active` | `cancelled` | Same resets as `completed` but no `total_trips` increment |
| `completed` | — | Terminal, no further transitions |
| `cancelled` | — | Terminal, no further transitions |

`TripsPanel` surfaces one action button per trip:
- Scheduled → **Start Trip** button + **Cancel** button
- Active → **Complete** button + **Cancel** button

### 5. Refresh Behaviour

- `updateTripStatus` calls `loadDispatch()` after the API response, so vehicles/drivers/trips all
  refresh to reflect side-effect changes (driver now `on-trip`, vehicle now `active`, etc.).
- `createTrip` now also calls `loadDispatch()` after success, so booked resources immediately
  disappear from the available lists.

### 6. Backend Side-Effects Consistency

On trip creation (`→ scheduled`):
- Vehicle: `driver_id` and `route_id` set to reserve the resource ✓
- Driver: `vehicle_id` set to reserve the resource ✓
- Statuses remain `idle`/`available` (no "scheduled" value in the DB enum)

On trip start (`scheduled → active`):
- `driver.status = 'on-trip'` ✓
- `vehicle.status = 'active'` ✓

On trip end (`active → completed` or `active → cancelled`):
- Driver reset to `available` if `driver.status == 'on-trip'` ✓
- Vehicle reset to `idle` if `vehicle.status == 'active'` ✓
- Assignment fields cleared: `driver.vehicle_id = None`, `vehicle.driver_id = None`, `vehicle.route_id = None` ✓
- `driver.total_trips` incremented on completion ✓

On trip cancellation from `scheduled` (driver was never `on-trip`):
- Status reset is a no-op (correct), but assignment fields are still cleared ✓

Manual status overrides:
- `vehicle_service.update_vehicle`: rejects setting `maintenance`/`offline` if vehicle has a
  scheduled or active trip ✓
- `driver_service.update_driver`: rejects setting `off-duty` if driver has a scheduled or active trip ✓
- Setting `on-trip` manually still rejected (pre-existing) ✓

### 7. Edge Cases — Status After Task 9.5

| # | Edge Case | Status |
|---|---|---|
| A | Schedule two trips for same vehicle back-to-back | **Fixed** — backend rejects with `409`; frontend booked-ID filter removes resource immediately after first schedule |
| B | Inactive routes appear in Schedule dialog | **Fixed** — `schedulableRoutes` filters to `isActive === true` |
| C | No end-after-start validation in dialog | **Fixed** — dialog validates before submit |
| D | `createTrip` does not reload resources | **Fixed** — calls `loadDispatch()` after success |
| E | Completed/cancelled trips have no panel | **Open** — they are not rendered; history view is out of scope for this phase |
| F | `listTrips` loads all statuses into memory | **Open** — minor performance concern; acceptable at current scale |
| G | `updateTripStatus` called without `await` in `TripsPanel` | **Open** — low risk; toast handles errors |

---

## Changes from Task 9.6

- **GPS initialization on trip start**: when a trip transitions `scheduled → active`, if the vehicle has no GPS coordinates, it is placed at the first route stop. The simulation loop picks it up on the next tick and it appears immediately on the tracking map.
- **Vehicle status protection tightened**:
  - Active trip → block ALL manual status changes (`idle`, `maintenance`, `offline`); use trip cancel/complete instead.
  - Scheduled trip → block only `maintenance`/`offline`; `idle` still allowed as an emergency manual override.
  - Vehicles with no formal trip (e.g. seeded active vehicles) remain controllable manually.
- **Map note**: the tracking map header shows a count of vehicles without GPS and instructs dispatchers to start a trip to place them on the map.

## About Seeded Active Vehicles

Vehicles seeded with `status = 'active'` and GPS coordinates are moved by the simulation independently of the Trip model — they have no formal trip record. They continue to work as before for demo purposes. To bring them into the proper dispatch lifecycle, re-seed the database and dispatch trips through the Dispatch screen; clicking "Start Trip" will activate the vehicle and initialize its GPS at the first route stop.

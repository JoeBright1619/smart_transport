# Route-Following Vehicle Simulation Plan

> **How to use this document:**
> - Work through tasks **strictly in order** — each phase depends on the previous.
> - After completing a task, tick its checkbox: `[ ]` → `[x]`
> - Keep the **Current Task Pointer** below updated after each completed task.
> - **DO NOT proceed to the next task without explicit user approval.**
> - Keep implementation files to approximately **200 lines**. If a file would grow much larger,
>   split the functionality into focused modules wherever practical.

---

## Current Task Pointer

**Next task:** Task 4.2 — Extend Frontend WebSocket Types

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

## Background — What This Plan Replaces

The current `_simulate_vehicle_positions` function in `backend/app/websocket/tracking.py` moves
vehicles by applying a **random ±0.0002° delta** to lat/lng every 5 seconds. This causes buses to:

- Drift off their route and wander randomly across the map
- Never actually approach a stop, making ETA meaningless
- Change heading randomly regardless of actual travel direction

This plan replaces that with a **route-following simulation** that moves each vehicle along
its assigned route stops in order, loops at the end, varies speed realistically, consumes fuel,
and creates real trip records — making the system indistinguishable from live GPS tracking.

---

## Architecture Overview

```
backend/app/websocket/
  tracking.py          ← existing broadcast loop (minimal changes)
  route_simulation.py  ← NEW: all route-following logic lives here
  manager.py           ← unchanged

backend/app/core/
  geo_math.py          ← NEW: haversine distance, bearing, position interpolation

frontend/src/app/lib/
  api-types.ts         ← extend WsVehiclePosition with nextStopName, progressPct
  ws-client.ts         ← map new fields through

frontend/src/app/components/pages/
  VehicleTracking.tsx  ← rotate marker by heading, show next stop in detail panel
  PassengerApp.tsx     ← show route number + next stop name in arrival card
```

**Key design decision:** Route state (which stop each vehicle is heading toward) is stored in a
**Python in-memory dict** inside `route_simulation.py`. This avoids a database migration, and it is
acceptable because state rebuilds itself automatically when the server restarts — vehicles simply
resume from the nearest stop on their route.

---

## Reference: Existing Files Changed Per Phase

| File | Phase |
|------|-------|
| `backend/app/websocket/tracking.py` | 2 |
| `backend/app/core/seed.py` | 2 |
| `backend/app/models/alert.py` | 3 |
| `backend/app/models/trip.py` | 3 |
| `frontend/src/app/lib/api-types.ts` | 4 |
| `frontend/src/app/lib/ws-client.ts` | 4 |
| `frontend/src/app/components/pages/VehicleTracking.tsx` | 5 |
| `frontend/src/app/components/pages/PassengerApp.tsx` | 5 |

---

## Phase 1 — Geo Math & Route State Foundation

---

### Task 1.1 — Geo Math Utilities (`backend/app/core/geo_math.py`)

**Description:**
Create a pure-Python module with three geographic calculation functions that the route-following
engine depends on. No third-party geo libraries — pure math using the haversine formula.

1. Create `backend/app/core/geo_math.py` with these three functions:

   **`haversine_distance(lat1, lng1, lat2, lng2) -> float`**
   Returns the great-circle distance in **metres** between two GPS coordinates.
   ```
   R = 6_371_000  # Earth radius in metres
   φ1, φ2 = radians of lat1, lat2
   Δφ = radians(lat2 - lat1)
   Δλ = radians(lng2 - lng1)
   a = sin²(Δφ/2) + cos(φ1)·cos(φ2)·sin²(Δλ/2)
   return R · 2 · atan2(√a, √(1−a))
   ```

   **`bearing(lat1, lng1, lat2, lng2) -> float`**
   Returns the initial bearing in degrees (0–360, clockwise from north) from point 1 to point 2.
   ```
   Δλ = radians(lng2 - lng1)
   x = cos(lat2)·sin(Δλ)
   y = cos(lat1)·sin(lat2) − sin(lat1)·cos(lat2)·cos(Δλ)
   return (degrees(atan2(x, y)) + 360) % 360
   ```

   **`move_along_bearing(lat, lng, bearing_deg, distance_m) -> tuple[float, float]`**
   Returns the new `(lat, lng)` after moving `distance_m` metres from `(lat, lng)` in the
   given compass direction.
   ```
   R = 6_371_000
   δ = distance_m / R          # angular distance
   θ = radians(bearing_deg)
   φ1, λ1 = radians(lat), radians(lng)
   φ2 = asin(sin(φ1)·cos(δ) + cos(φ1)·sin(δ)·cos(θ))
   λ2 = λ1 + atan2(sin(θ)·sin(δ)·cos(φ1), cos(δ) − sin(φ1)·sin(φ2))
   return degrees(φ2), degrees(λ2)
   ```

2. Add a small `if __name__ == "__main__"` smoke-test at the bottom of the file that prints
   the distance between Nyabugogo (`-1.9396, 30.0585`) and Kimironko (`-1.9441, 30.1341`).
   Expected result: approximately **7 600 metres**.

**Suggested commit:** `Add geo math utilities: haversine distance, bearing, position interpolation`

- [x] Task 1.1 complete

---

### Task 1.2 — Route Simulation Module (`backend/app/websocket/route_simulation.py`)

**Description:**
Create `backend/app/websocket/route_simulation.py`. This module owns the in-memory state that
tracks where each vehicle is on its route, and provides the single public function that
`tracking.py` will call each tick.

1. Define the in-memory state dict at module level:
   ```python
   # Maps vehicle_id -> { next_stop_index, trip_started_at, loop_count }
   _state: dict[str, dict] = {}
   ```

2. Define a dataclass or TypedDict `StopPoint` with fields `id: str`, `name: str`,
   `lat: float`, `lng: float` for convenience.

3. Write `async def load_route_stops(db, route_id: str) -> list[StopPoint]`:
   - Query `RouteStop` joined to `Stop` where `route_id == route_id` and `stop.is_deleted == False`
   - Order by `RouteStop.stop_order` ascending
   - Return a list of `StopPoint` objects
   - Return `[]` if the route has no stops

4. Write `def get_or_init_state(vehicle_id: str, stop_count: int) -> dict`:
   - If `vehicle_id` not in `_state`, insert `{ next_stop_index: 1, trip_started_at: now(), loop_count: 0 }`
   - Clamp `next_stop_index` to valid range `[0, stop_count-1]`
   - Return the state dict

5. Write `def clear_vehicle_state(vehicle_id: str) -> None`:
   - Removes the entry from `_state` if it exists
   - Called when a vehicle is deactivated or unassigned from a route

6. Write `def get_next_stop_name(vehicle_id: str, stops: list[StopPoint]) -> str`:
   - Returns `stops[state['next_stop_index']].name` for the given vehicle, or `""` if no state

7. Write `def compute_progress_pct(vehicle: Vehicle, stops: list[StopPoint], state: dict) -> int`:
   - Gets the **previous** stop (index before `next_stop_index`, wrapping) and the next stop
   - Computes `segment_length = haversine_distance(prev_stop, next_stop)` in metres
   - Computes `remaining = haversine_distance(vehicle.lat, vehicle.lng, next_stop)` in metres
   - Returns `int(max(0, min(100, (1 - remaining / segment_length) * 100)))` — percent of the
     current segment the vehicle has completed

**Suggested commit:** `Add route simulation module with in-memory vehicle route state`

- [x] Task 1.2 complete

---

## Phase 2 — Route-Following Engine (Layer 1)

---

### Task 2.1 — Segment-Following Movement

**Description:**
Implement the core movement logic inside `route_simulation.py`. Add a function
`async def advance_vehicle(db, vehicle, now: datetime) -> dict | None` that moves a vehicle
one tick along its route and returns a dict of fields to persist on the `Vehicle` row.
Returns `None` if the vehicle has no route or its route has no stops.

1. Inside `advance_vehicle`:

   a. Return `None` if `vehicle.route_id` is `None`.

   b. Load route stops: `stops = await load_route_stops(db, vehicle.route_id)`. Return `None`
      if `len(stops) < 2`.

   c. Get or initialise state: `state = get_or_init_state(vehicle.id, len(stops))`.

   d. Get the next stop: `target = stops[state['next_stop_index']]`.

   e. Compute distance to target:
      `dist_m = haversine_distance(vehicle.lat, vehicle.lng, target.lat, target.lng)`.

   f. Compute metres to advance this tick (5-second interval):
      `advance_m = (vehicle.speed or 20) * 1000 / 3600 * TICK_SECONDS`
      where `TICK_SECONDS = 5`.

   g. If `dist_m <= advance_m` **or** `dist_m < 30` (arrived at stop):
      - Snap `lat, lng` to `target.lat, target.lng`
      - Advance `state['next_stop_index'] = (state['next_stop_index'] + 1) % len(stops)`
      - Set `speed = 0` (momentarily stopped at the stop)
      - If `state['next_stop_index'] == 0`: increment `state['loop_count']`,
        reset `state['trip_started_at'] = now`

   h. Else (still travelling toward next stop):
      - `brg = bearing(vehicle.lat, vehicle.lng, target.lat, target.lng)`
      - `new_lat, new_lng = move_along_bearing(vehicle.lat, vehicle.lng, brg, advance_m)`
      - Update `lat, lng, heading = new_lat, new_lng, int(brg)`

   i. Return a dict: `{ "lat": ..., "lng": ..., "speed": ..., "heading": ... }` with all
      updated values ready to be assigned back onto the `Vehicle` ORM object.

2. Import `BROADCAST_INTERVAL_SECONDS` from `tracking.py` — or define `TICK_SECONDS = 5`
   as a constant at the top of `route_simulation.py` and keep it in sync.

**Suggested commit:** `Implement segment-following movement along route stops`

- [x] Task 2.1 complete

---

### Task 2.2 — Wire Simulation into `tracking.py`

**Description:**
Replace the random-walk body of `_simulate_vehicle_positions` in `tracking.py` with calls to
the new `advance_vehicle` function. The rest of `tracking.py` (connection handling, broadcast
loop, telemetry recording) stays **unchanged**.

1. In `tracking.py`, add the import:
   ```python
   from app.websocket.route_simulation import advance_vehicle
   ```

2. Replace the entire `for vehicle in vehicles:` body inside `_simulate_vehicle_positions` with:
   ```python
   for vehicle in vehicles:
       now = datetime.now(timezone.utc)
       updates = await advance_vehicle(db, vehicle, now)
       if updates:
           vehicle.lat     = updates["lat"]
           vehicle.lng     = updates["lng"]
           vehicle.speed   = updates["speed"]
           vehicle.heading = updates["heading"]
       # fallback: if no route assigned keep vehicle stationary (no random walk)
   ```

3. Remove the four `uniform(...)` lines that applied the random walk.

4. Keep `await db.commit()` at the end of the function — unchanged.

5. Manually test: restart the backend Docker service, open Vehicle Tracking in the browser,
   and confirm that `veh-001` (Route 101, Nyabugogo → Kimironko) moves visibly toward
   Kacyiru rather than drifting randomly.

**Suggested commit:** `Replace random-walk simulation with route-following movement`

- [x] Task 2.2 complete

---

### Task 2.3 — Seed Vehicles at Route Start Positions

**Description:**
The new simulation starts each vehicle from wherever its `lat`/`lng` is stored in the DB.
For the route-following to look correct from the first broadcast, each active vehicle should
start at the **first stop of its assigned route**.

1. In `backend/app/core/seed.py`, update `_seed_vehicles` so the lat/lng for active vehicles
   match the first stop of their route exactly:

   | Vehicle | Route | First stop | lat | lng |
   |---------|-------|------------|-----|-----|
   | veh-001 | route-001 | Nyabugogo | -1.9396 | 30.0585 |
   | veh-003 | route-002 | CBD (City Hall) | -1.9500 | 30.0588 |
   | veh-006 | route-003 | Remera | -1.9553 | 30.1127 |
   | veh-007 | route-004 | Kicukiro | -1.9742 | 30.0904 |
   | veh-008 | route-005 | Gikondo | -1.9726 | 30.0642 |

2. In `_seed_vehicles`, for vehicles that already exist (`created = False`), **also update**
   `lat`, `lng`, and `heading` to the new values so re-running the seed repositions them.
   Change `_get_or_create` calls for active vehicles to: after calling `_get_or_create`,
   always set `vehicle.lat = lat`, `vehicle.lng = lng`, `vehicle.heading = heading`.

3. Run `python -m app.core.seed` and confirm the five active vehicles are repositioned.

4. Restart the tracking WebSocket and confirm each vehicle begins travelling from its
   correct first stop.

**Suggested commit:** `Reset active vehicle positions to route start stops in seed`

- [x] Task 2.3 complete

---

## Phase 3 — Realistic Physics (Layer 2)

---

### Task 3.1 — Speed Variation Near Stops

**Description:**
Currently vehicles move at a constant `speed`. Real buses decelerate as they approach a stop
and accelerate as they leave. Implement smooth speed variation inside `advance_vehicle`.

1. Add this logic in `advance_vehicle` **before** computing `advance_m` (step f in Task 2.1):

   ```python
   OPEN_ROAD_SPEED  = 35   # km/h cruising speed
   STOP_SPEED       = 0    # km/h at stop
   DECEL_START_DIST = 250  # metres: start braking
   ACCEL_END_DIST   = 150  # metres: finish accelerating after stop

   current_speed = vehicle.speed or 0
   dist_to_next = haversine_distance(vehicle.lat, vehicle.lng, target.lat, target.lng)

   if current_speed == 0:
       # Just departed a stop — begin accelerating
       new_speed = min(OPEN_ROAD_SPEED, current_speed + 8)
   elif dist_to_next < DECEL_START_DIST:
       # Approaching stop — linearly ramp down toward 5 km/h
       ratio = dist_to_next / DECEL_START_DIST         # 0 (at stop) → 1 (far)
       new_speed = max(5, int(OPEN_ROAD_SPEED * ratio))
   else:
       # Open road — small random variation ±3 km/h
       variation = round(uniform(-3, 3))
       new_speed = max(15, min(50, current_speed + variation))

   vehicle.speed = new_speed  # write before computing advance_m
   ```

2. Use `new_speed` for `advance_m` computation so the movement distance and the displayed
   speed always match.

3. After the speed change, keep the existing segment-following movement logic from Task 2.1
   unchanged.

**Suggested commit:** `Add speed variation: decelerate approaching stops, accelerate leaving`

- [x] Task 3.1 complete

---

### Task 3.2 — Fuel Consumption and Low-Fuel Alert

**Description:**
Decrease fuel as vehicles move, generate a low-fuel alert when fuel drops below 15 %, and
refuel the vehicle automatically when it completes a loop back to its first stop (depot).

1. In `advance_vehicle`, after the position is updated, add fuel logic:

   ```python
   FUEL_CONSUMPTION_PCT_PER_KM = 1.0   # 1% per km (50-seat bus, 50L tank approx)
   LOW_FUEL_THRESHOLD = 15             # percent

   km_this_tick = new_speed * TICK_SECONDS / 3600
   fuel_drop = km_this_tick * FUEL_CONSUMPTION_PCT_PER_KM
   prev_fuel = vehicle.fuel or 100
   new_fuel  = max(0, prev_fuel - fuel_drop)

   # Auto-refuel at depot when starting a new loop
   if state['next_stop_index'] == 0 and state['loop_count'] > 0:
       new_fuel = 100.0

   vehicle.fuel = int(new_fuel)
   ```

2. Include `"fuel": int(new_fuel)` in the returned updates dict from `advance_vehicle`.

3. In `_simulate_vehicle_positions` inside `tracking.py`, after applying `updates`, add
   low-fuel alert creation:

   ```python
   if updates.get("fuel", 100) < LOW_FUEL_THRESHOLD:
       prev_fuel_before = vehicle.fuel  # value before update
       if prev_fuel_before >= LOW_FUEL_THRESHOLD:
           # Crossed threshold this tick — create alert once
           db.add(Alert(
               tenant_id=tenant_id,
               type="maintenance",
               severity="high",
               title=f"Low Fuel: {vehicle.registration_number}",
               message=f"{vehicle.registration_number} fuel is below {LOW_FUEL_THRESHOLD}%.",
               vehicle_id=vehicle.id,
               is_acknowledged=False,
           ))
   ```

4. Import `Alert` from `app.models.alert` at the top of `tracking.py`.

5. Add `"fuel"` to `LOW_FUEL_THRESHOLD` as a module constant in `route_simulation.py`.

**Suggested commit:** `Add fuel consumption with low-fuel alert and depot auto-refuel`

- [x] Task 3.2 complete

---

### Task 3.3 — Automatic Trip Record Creation

**Description:**
Each time a vehicle completes a full route loop (reaches the last stop and wraps back to
stop index 0), automatically create a completed `Trip` record. This populates the Dispatch
page trip history and feeds the analytics tables with live data going forward.

1. Add `async def _create_completed_trip(db, vehicle, state: dict, now: datetime) -> None`
   in `route_simulation.py`:

   ```python
   from random import randint
   from app.models.trip import Trip

   async def _create_completed_trip(db, vehicle, state: dict, now: datetime) -> None:
       started_at = state.get("trip_started_at") or now
       if vehicle.route_id is None or vehicle.driver_id is None:
           return
       passengers = randint(20, vehicle.capacity)
       scheduled_duration_min = 35  # default — a refinement could load from Route.duration
       scheduled_end = started_at + timedelta(minutes=scheduled_duration_min)
       actual_duration = (now - started_at).total_seconds() / 60
       delay = max(0, int(actual_duration - scheduled_duration_min))
       trip = Trip(
           tenant_id=vehicle.tenant_id,
           vehicle_id=vehicle.id,
           route_id=vehicle.route_id,
           driver_id=vehicle.driver_id,
           scheduled_start=started_at,
           actual_start=started_at,
           scheduled_end=scheduled_end,
           actual_end=now,
           status="completed",
           passengers=passengers,
           delay=delay,
           is_deleted=False,
           created_at=started_at,
           updated_at=now,
       )
       db.add(trip)
   ```

2. In `advance_vehicle`, inside the "arrived at stop" branch where `next_stop_index` wraps
   to `0`, call:
   ```python
   await _create_completed_trip(db, vehicle, state, now)
   state["trip_started_at"] = now
   ```

3. Since `advance_vehicle` now writes to the DB (adds a Trip), pass `db` to it.
   Update the call in `tracking.py` accordingly — `db` is already available in
   `_simulate_vehicle_positions`.

4. Import `timedelta` from `datetime` at the top of `route_simulation.py`.

**Suggested commit:** `Auto-create completed trip records on each route loop`

- [x] Task 3.3 complete

---

## Phase 4 — WebSocket Protocol Extension

---

### Task 4.1 — Broadcast Next-Stop Info

**Description:**
Extend the vehicle position broadcast message to include `nextStopName` and `progressPct` so
the frontend can show "heading to X (72%)" in real time without an extra API call.

1. In `_build_vehicle_update_message` in `tracking.py`, for each vehicle in the response list,
   add two fields:

   ```python
   from app.websocket.route_simulation import get_next_stop_name, compute_progress_pct, _state

   # Inside the list comprehension that builds each vehicle entry:
   stops = await load_route_stops(db, vehicle.route_id) if vehicle.route_id else []
   state  = _state.get(vehicle.id, {})

   {
       ...existing fields...,
       "nextStopName":  stops[state["next_stop_index"]].name if stops and state else "",
       "progressPct":   compute_progress_pct(vehicle, stops, state) if stops and state else 0,
   }
   ```

2. To avoid loading stops twice per tick (once in broadcast, once in simulate), introduce a
   module-level `_route_stops_cache: dict[str, list[StopPoint]] = {}` in `route_simulation.py`
   with a helper `async def get_stops_cached(db, route_id: str) -> list[StopPoint]` that
   loads and caches. Cache is cleared on server restart (acceptable — it rebuilds from DB).

3. Export `get_stops_cached` so `tracking.py` can use it for both `_build_vehicle_update_message`
   and `_simulate_vehicle_positions` without duplicate DB queries.

**Suggested commit:** `Include nextStopName and progressPct in WebSocket vehicle broadcast`

- [x] Task 4.1 complete

---

### Task 4.2 — Extend Frontend WebSocket Types

**Description:**
Update the TypeScript types and the WebSocket client mapper so the new fields flow through
to the components.

1. In `frontend/src/app/lib/api-types.ts`, extend `WsVehiclePosition`:
   ```typescript
   export type WsVehiclePosition = {
     vehicleId: string;
     lat: number;
     lng: number;
     speed: number;
     heading: number;
     fuel: number;
     status: VehicleStatus;
     timestamp: string;
     engineStatus?: string;   // already present
     nextStopName?: string;   // NEW
     progressPct?: number;    // NEW (0–100)
   };
   ```

2. In `frontend/src/app/lib/ws-client.ts`, in the `vehicle_update` mapping block, add:
   ```typescript
   nextStopName: v.nextStopName ?? '',
   progressPct:  v.progressPct  ?? 0,
   ```

**Suggested commit:** `Extend WsVehiclePosition type with nextStopName and progressPct`

- [ ] Task 4.2 complete

---

## Phase 5 — Frontend Tracking & Passenger Enhancements

---

### Task 5.1 — Directional Vehicle Markers

**Description:**
Replace the static coloured-circle map marker with an SVG bus icon that **rotates to face
the vehicle's current heading**. This makes the movement direction immediately obvious.

1. In `frontend/src/app/components/pages/VehicleTracking.tsx`, update `createVehicleIcon`
   to accept `heading: number` as a second parameter and embed it in the SVG `transform`:

   ```typescript
   const createVehicleIcon = (status: string, heading: number) => {
     const color = ...;  // unchanged
     const svg = `
       <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
         <g transform="rotate(${heading}, 16, 16)">
           <circle cx="16" cy="16" r="12" fill="${color}" stroke="white" stroke-width="2"/>
           <!-- Arrow pointing north (up) — rotation handles actual direction -->
           <polygon points="16,6 20,20 16,17 12,20" fill="white" opacity="0.9"/>
         </g>
       </svg>`;
     return new Icon({ iconUrl: `data:image/svg+xml;base64,${btoa(svg)}`, ... });
   };
   ```

2. Pass `vehicle.heading ?? 0` as the second argument wherever `createVehicleIcon` is called
   (there are two call sites in the file — the sidebar list markers don't use icons, only the
   Leaflet `<Marker>` components do).

3. Because the WebSocket updates `heading` every 5 seconds, the icon will automatically
   re-render with the new rotation on each message.

**Suggested commit:** `Rotate vehicle map markers to face heading direction`

- [ ] Task 5.1 complete

---

### Task 5.2 — Next Stop Display in Tracking Sidebar

**Description:**
Show "Next stop: Kacyiru (72%)" in the vehicle list sidebar and in the selected-vehicle
detail panel so operators can see progress at a glance.

1. In `VehicleTracking.tsx`, the WsMessage handler already merges updates onto `vehicles`
   state via `setVehicles`. Extend that merge to include `nextStopName` and `progressPct`
   from `WsVehiclePosition` onto the `VehicleRead` object.
   Since `VehicleRead` doesn't have those fields, use a local extended type:

   ```typescript
   type TrackedVehicle = VehicleRead & {
     nextStopName?: string;
     progressPct?: number;
   };
   ```
   Change the `vehicles` state type from `VehicleRead[]` to `TrackedVehicle[]` in this file only.

2. In the vehicle card in the sidebar (the `filteredVehicles.map(...)` block), add below the
   route badge:
   ```tsx
   {vehicle.nextStopName && (
     <div className="mt-1">
       <p className="text-xs text-slate-500">Next: {vehicle.nextStopName}</p>
       <div className="mt-0.5 h-1 w-full rounded-full bg-slate-200">
         <div
           className="h-full rounded-full bg-blue-500"
           style={{ width: `${vehicle.progressPct ?? 0}%` }}
         />
       </div>
     </div>
   )}
   ```

3. In the selected-vehicle detail panel (bottom of the map column), add a fourth stat box:
   ```tsx
   <div>
     <p className="text-xs text-slate-500">Next Stop</p>
     <p className="font-medium text-sm mt-1">
       {selectedVehicle.nextStopName || '—'}
     </p>
     {selectedVehicle.progressPct !== undefined && (
       <p className="text-xs text-slate-400">{selectedVehicle.progressPct}% to stop</p>
     )}
   </div>
   ```

**Suggested commit:** `Show next stop and progress in tracking sidebar and detail panel`

- [ ] Task 5.2 complete

---

### Task 5.3 — Passenger App Arrival Improvements

**Description:**
The Passenger App's arrival card currently shows registration number and ETA minutes. Extend
it to show the route number and "heading to [next stop]" so passengers understand which bus
to board and where it is on the route.

1. In `frontend/src/app/components/pages/PassengerApp.tsx`, the `ArrivalEstimate` type
   already has `routeName` and `routeId`. Extend the arrival card UI to show:
   - Route number/name badge (already in `ArrivalEstimate.routeName`)
   - ETA minutes or "Arriving" if `etaMinutes < 2`
   - Distance in km (already shown)

2. In the arrival card, replace the existing distance/ETA layout with:
   ```tsx
   <div className="flex items-center justify-between">
     <div>
       <p className="font-semibold text-sm">{arrival.registrationNumber}</p>
       <p className="text-xs text-slate-500">{arrival.routeName}</p>
     </div>
     <div className="text-right">
       {arrival.etaMinutes !== null && arrival.etaMinutes < 2 ? (
         <span className="text-green-600 font-bold text-sm">Arriving now</span>
       ) : arrival.etaMinutes !== null ? (
         <span className="font-bold text-sm">{arrival.etaMinutes} min</span>
       ) : (
         <span className="text-slate-400 text-sm">Stopped</span>
       )}
       {arrival.distanceToStopKm != null && (
         <p className="text-xs text-slate-500">{arrival.distanceToStopKm.toFixed(1)} km away</p>
       )}
     </div>
   </div>
   ```

3. Add a subtle "Live" indicator dot that pulses (CSS `animate-pulse` on a green dot) to
   signal real-time data to the passenger.

**Suggested commit:** `Improve Passenger App arrival cards with route info and live indicator`

- [ ] Task 5.3 complete

---

## Implementation Summary

| Phase | Tasks | Status |
|---|---|---|
| Phase 1 — Geo Math & Route State | 2 tasks | 0 / 2 |
| Phase 2 — Route-Following Engine (Layer 1) | 3 tasks | 0 / 3 |
| Phase 3 — Realistic Physics (Layer 2) | 3 tasks | 0 / 3 |
| Phase 4 — WebSocket Protocol Extension | 2 tasks | 0 / 2 |
| Phase 5 — Frontend Enhancements | 3 tasks | 0 / 3 |
| **Total** | **13 tasks** | **0 / 13** |

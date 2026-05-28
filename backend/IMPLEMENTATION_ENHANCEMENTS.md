# Route Management & Simulation Enhancements

> **How to use this document:**
> - Work through tasks **strictly in order** — each phase depends on the previous.
> - After completing a task, tick its checkbox: `[ ]` → `[x]`
> - Keep the **Current Task Pointer** below updated after each completed task.
> - **DO NOT proceed to the next task without explicit user approval.**
> - for now ignore the provided branch, we will use `master` branch instead of the branches given in the tasks and commit messages exactly as provided.

---

## Current Task Pointer

**Next task:** Task 1.1 — Analytics Upsert Utility

---

> [!IMPORTANT]
> **Agent Rule:** After completing each task, stop and report:
> 1. What was implemented
> 2. Any decisions made or problems encountered
> 3. A commit message for what was implemented
> 4. Then ask: _"Ready to proceed to the next task?"_
> Do not move forward until the user confirms.

---

## Phase 1 — Live Simulation & Analytics

---

### Task 1.1 — Analytics Upsert Utility (`crud/analytics.py` or `services/analytics_service.py`)

**Description:**
Implement an upsert function to safely add `fuel_consumed` and `revenue` to the current day's `AnalyticsRecord`. This should use an atomic `INSERT ... ON CONFLICT DO UPDATE` or equivalent mechanism to prevent race conditions during frequent simulation ticks.

**Branch:** `feat/analytics-upsert`
**Commit:** `Add daily analytics upsert utility for live simulation data`

- [x] Task 1.1 complete

---

### Task 1.2 — Live Simulation Revenue & Passenger Logic (`websocket/route_simulation.py`)

**Description:**
Update the vehicle simulation to track passengers boarding and alighting at every stop:
1. Initialize a `passengers` list in the vehicle's state. Each passenger object tracks their origin stop, destination stop, and the route distance between them.
2. When the vehicle reaches a stop:
   - Passengers whose destination is the current stop alight.
   - For each alighted passenger, calculate their individual ticket price: `distance_in_km * 60 RWF` (pro-rated down to meters, e.g., 60 RWF / 1000m).
   - Sum the revenue of all alighting passengers.
   - New passengers board with random destination stops ahead.
3. Call the analytics upsert utility to add the calculated revenue to today's `AnalyticsRecord`.

**Branch:** `feat/live-revenue-simulation`
**Commit:** `Implement stop-by-stop passenger simulation and live revenue tracking`

- [x] Task 1.2 complete

---

### Task 1.3 — Live Simulation Fuel Consumption (`services/simulation_runner.py`)

**Description:**
In `simulation_runner.py`, accumulate the `fuel_drop` across all active vehicles during each tick. Call the analytics upsert utility to add the total fuel consumed during this tick to today's `AnalyticsRecord.total_fuel_consumption`.

**Branch:** `feat/live-fuel-simulation`
**Commit:** `Track live vehicle fuel consumption in daily analytics`

- [ ] Task 1.3 complete

---

## Phase 2 — Interactive Route Management

---

### Task 2.1 — Interactive Route Management UI (`frontend/...`)

**Description:**
Overhaul the route creation and editing UI:
1. Create a shared `RouteForm` component used by both `CreateRouteModal` and a new `EditRouteModal`.
2. Integrate `react-leaflet` into `RouteStopsEditor`.
3. Map functionality:
   - Click the map to add a new stop at the clicked coordinates.
   - Allow dragging existing stop markers. Prompt the user with `window.confirm` ("Are you sure you want to update this stop's location?") before applying the dragged coordinates.
4. Auto-calculation:
   - When stops are added or moved, automatically calculate the total route distance (summing the Haversine distance between consecutive stops).
   - Auto-calculate the route duration assuming a constant speed of 60km/h (`duration_minutes = (distance_km / 60) * 60`).

**Branch:** `feat/interactive-route-management`
**Commit:** `Add map-based route editor with automatic distance and duration calculation`

- [ ] Task 2.1 complete

---

## Implementation Summary

| Phase | Tasks | Status |
|---|---|---|
| Phase 1 — Live Simulation & Analytics | 3 tasks | 0 / 3 |
| Phase 2 — Interactive Route Management | 1 task | 0 / 1 |
| **Total** | **4 tasks** | **0 / 4** |

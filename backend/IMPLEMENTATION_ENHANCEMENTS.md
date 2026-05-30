# Frontend Bug Fixes & Feature Enhancements

> **How to use this document:**
> - Work through tasks **strictly in order** — each phase depends on the previous.
> - After completing a task, tick its checkbox: `[ ]` → `[x]`
> - Keep the **Current Task Pointer** below updated after each completed task.
> - **DO NOT proceed to the next task without explicit user approval.**
> - Use the `master` branch for all tasks and use commit messages exactly as provided.

---

## Current Task Pointer

**Next task:** (all Phase 9 tasks complete)

---

> [!IMPORTANT]
> **Agent Rule:** After completing each task, stop and report:
> 1. What was implemented
> 2. Any decisions made or problems encountered
> 3. A commit message for what was implemented
> 4. Then ask: _"Ready to proceed to the next task?"_
> Do not move forward until the user confirms.

----

## Phase 9 — Branding, Tracking UX, Header Interactions & Dispatch Clarity

---

### Task 9.1 — Tenant Logo Storage, Placeholders, and Seeded Logo Path

**Files:** `backend/app/models/tenant.py`, `backend/app/schemas/auth.py`, `backend/app/schemas/superadmin.py`, `backend/app/core/seed.py`, `backend/alembic/versions/` _(new migration)_, `frontend/public/tenant-logos/` _(new directory)_, `frontend/src/app/lib/api-types.ts`, `frontend/src/app/lib/auth-context.tsx`, `frontend/src/app/lib/types.ts`, `frontend/src/app/components/layout/Sidebar.tsx`, `frontend/src/app/components/pages/analytics/analytics-pdf.ts`

**Description:**
Tenants need a logo attribute that stores the logo image location. The app should have a dedicated logo directory with placeholder assets, the seed data should assign EcoFleet a placeholder logo, and branded UI/PDF surfaces should use the tenant logo when present.

Fix steps:
1. Create `frontend/public/tenant-logos/` and add at least one placeholder logo asset, e.g. `ecofleet-placeholder.svg` and/or `default-tenant.svg`.
2. Add nullable `logo_path` to the backend `Tenant` model and create an Alembic migration.
3. Seed EcoFleet with `logo_path="/tenant-logos/ecofleet-placeholder.svg"`.
4. Expose `tenantLogoPath` from auth responses and access tokens, alongside existing tenant branding fields.
5. Add `tenantLogoPath` to frontend API/auth/user types.
6. Show the logo in `Sidebar` next to the tenant name, falling back to the bus icon when absent.
7. Pass the tenant logo path into `exportAnalyticsPDF`; if feasible, render it in the PDF header, otherwise render the tenant name placeholder cleanly.

**Branch:** `master`
**Commit:** `feat: add tenant logo path and seeded logo placeholder`

- [x] Task 9.1 complete

---

### Task 9.2 — Vehicle Tracking Map Highlights Selected Vehicle, Route Stops, and All Statuses

**Files:** `frontend/src/app/components/pages/VehicleTracking.tsx`

**Description:**
When a user clicks a vehicle in the Fleet Vehicles side panel, the matching vehicle indicator on the map should be visually highlighted so it is obvious which marker corresponds to the selected row. The map should also highlight the route stops the selected vehicle is heading toward. The map currently appears to emphasize active vehicles and does not clearly show every vehicle status.

Fix steps:
1. Keep rendering all vehicles with `currentLocation`, regardless of status, when the status filter is `all`.
2. Make marker colors/status treatment explicit for `active`, `idle`, `maintenance`, and `offline`.
3. Add a selected-marker variant: larger icon, ring/outline, higher z-index, and/or popup auto-open when selected from the side panel.
4. When `selectedVehicle.routeId` exists, highlight that route polyline and route stops on the map; make non-selected route lines more subtle.
5. Highlight the next stop when `selectedVehicle.nextStopName` matches a route stop name.
6. Ensure clicking a map marker also selects/highlights the side-panel row.
7. Add a map legend explaining vehicle status colors and selected/next-stop treatment.

**Branch:** `master`
**Commit:** `feat: highlight selected tracking vehicle and route stops on map`

- [x] Task 9.2 complete

---

### Task 9.3 — Interactive Global Header: Notifications, Date/Weather, and Search Strategy

**Files:** `frontend/src/app/components/layout/Header.tsx`, `frontend/src/app/components/layout/MainLayout.tsx`, `frontend/src/app/services/alerts.service.ts`, `frontend/src/app/components/ui/` _(dropdown/popover components if needed)_

**Description:**
The header currently has mock/static data: weather text, a hard-coded date, a passive notification count, and a global search input that competes with page-specific search fields. Make the header useful and decide the correct search behavior.

Recommended approach:
Use the header as a compact global command/search surface only on pages without strong local search. On pages that already have dedicated search/filter controls (Fleet, Tracking, Passenger, Route Stop editor, etc.), hide or collapse global search into a command icon to avoid duplicate search bars.

Fix steps:
1. Replace the hard-coded date with the real current date using `currentTime`.
2. Remove mock weather or replace it with a tenant/location-aware widget only if real data exists; do not keep fake weather.
3. Make the notification bell interactive using a dropdown/popover that loads recent unacknowledged alerts.
4. Show alert title, severity, relative time, and a link/action to `/alerts`.
5. Refresh notification count periodically or after opening the dropdown.
6. Decide global search behavior:
   - hide search on pages with local search/filter controls, or
   - convert it into a command palette that searches across vehicles, routes, drivers, and pages.
7. If keeping global search, implement real results and navigation; otherwise remove the inert input and document why.

**Branch:** `master`
**Commit:** `feat: make global header notifications and search interactive`

- [x] Task 9.3 complete

---

### Task 9.4 — Dispatch Workflow Documentation and UX Review

**Files:** `frontend/src/app/components/pages/Dispatch.tsx`, `frontend/src/app/components/pages/dispatch/useDispatchManagement.ts`, `frontend/src/app/components/pages/dispatch/ScheduleTripDialog.tsx`, `frontend/src/app/components/pages/dispatch/TripsPanel.tsx`, `frontend/src/app/components/pages/dispatch/dispatch-helpers.ts`, `backend/app/routers/trips.py`, `backend/app/services/trip_service.py`

**Description:**
Analyze the Dispatch workflow end to end and document how scheduling, starting, completing, and cancelling trips currently work. Identify UX/API gaps before changing behavior.

Review points:
1. Data loading: `useDispatchManagement` loads trips, vehicles, drivers, and routes in parallel.
2. Resource eligibility: only `idle` vehicles and `available` drivers are offered when scheduling.
3. Scheduling: `ScheduleTripDialog` posts `TripCreate` with vehicle, route, driver, start, and end.
4. Trip lifecycle: scheduled trips can be started or cancelled; active trips can be completed or cancelled.
5. Refresh behavior: trip status updates reload dispatch resources after the API call.
6. Backend side effects: confirm whether trip lifecycle updates also update vehicle/driver statuses consistently.
7. Edge cases: overlapping trips, inactive routes, unavailable drivers/vehicles, invalid date ranges, and completed/cancelled trip visibility.

**Branch:** `master`
**Commit:** `docs: document dispatch workflow and review gaps`

- [x] Task 9.4 complete

---

### Task 9.5 — Dispatch Resource Integrity: Prevent Double-Booking Drivers/Vehicles

**Files:** `backend/app/services/trip_service.py`, `backend/app/services/driver_service.py`, `backend/app/services/vehicle_service.py`, `frontend/src/app/components/pages/dispatch/useDispatchManagement.ts`, `frontend/src/app/components/pages/dispatch/ScheduleTripDialog.tsx`, `frontend/src/app/components/pages/drivers/DriversTable.tsx`

**Description:**
Dispatch currently allows inconsistent resource assignment in at least one real workflow: a driver can appear available even while assigned to or moving in another vehicle, and a new trip can be scheduled using that same driver. Driver `on-trip` is intentionally greyed out in the UI because the backend blocks manually setting it; it should be system-controlled through trip lifecycle. The bug is that the system is not consistently deriving and enforcing that status.

Fix steps:
1. In `trip_service.create_trip`, validate the selected driver and vehicle belong to the tenant and are not deleted.
2. Reject scheduling if the selected driver has:
   - any `scheduled` or `active` trip, or
   - `status == "on-trip"`, or
   - `vehicle_id` assigned to another active/moving vehicle where applicable.
3. Reject scheduling if the selected vehicle has:
   - any `scheduled` or `active` trip, or
   - `status in ("active", "maintenance", "offline")`.
4. On trip creation, reserve the resources by setting vehicle/driver assignment fields consistently:
   - `vehicle.driver_id = trip.driver_id`
   - `vehicle.route_id = trip.route_id`
   - `driver.vehicle_id = trip.vehicle_id`
   - keep status as `scheduled`/reserved equivalent if model supports it; otherwise document why status remains idle until start.
5. On trip start, set `driver.status = "on-trip"` and `vehicle.status = "active"`.
6. On trip completion/cancellation, release resource links where appropriate and set driver/vehicle status back to available/idle only if they are not blocked by maintenance/offline/manual state.
7. Update dispatch available-resource filters to use backend-safe availability, not only local `status === "idle"` / `status === "available"` assumptions.
8. Keep `on-trip` disabled in the driver status dropdown, but add a tooltip/helper text explaining it is controlled by active trips.

**Branch:** `master`
**Commit:** `fix: enforce dispatch resource availability and prevent double booking`

- [x] Task 9.5 complete

---

### Task 9.6 — Tracking Status Ownership and Newly Dispatched Vehicle Visibility

**Files:** `backend/app/services/vehicle_service.py`, `backend/app/services/trip_service.py`, `backend/app/websocket/route_simulation.py`, `backend/app/services/simulation_runner.py`, `frontend/src/app/components/pages/VehicleTracking.tsx`, `frontend/src/app/lib/ws-client.ts`

**Description:**
Vehicle status currently can be manually changed even while a vehicle is moving, which lets an active vehicle be set to `idle` or `maintenance`. Also, a newly dispatched/scheduled vehicle may not appear on the map because it has no current coordinates and/or is not active in the simulation yet.

Fix steps:
1. Decide ownership rules:
   - `active` should be controlled by active trips/simulation, not arbitrary manual changes.
   - `maintenance`/`offline` should block dispatch and should not be allowed while a trip is active unless there is a specific emergency/breakdown flow.
   - `idle` should mean no active/scheduled trip and no maintenance/offline block.
2. In `vehicle_service.update_vehicle`, reject manual status changes that conflict with active or scheduled trips.
3. If setting a vehicle to `maintenance` or `offline`, require no active/scheduled trip for that vehicle.
4. On scheduling a trip, ensure the vehicle has enough route/driver assignment data for tracking context.
5. On starting a trip, ensure the simulation/websocket includes the vehicle and initializes location from the first route stop if `current_location` is missing.
6. In `VehicleTracking.tsx`, show vehicles without coordinates in the side list with a clear “No GPS fix yet” state instead of implying they should be on the map.
7. Add a map/sidebar explanation that vehicles appear on the map only after a valid current location exists.
8. If desired, render scheduled vehicles at their first route stop with a distinct “scheduled/not live” marker so dispatchers can see the planned vehicle before movement begins.

**Branch:** `master`
**Commit:** `fix: protect vehicle status lifecycle and show dispatched tracking state`

- [x] Task 9.6 complete

---

## Implementation Summary

| Phase | Tasks | Status |
|---|---|---|
| Phase 9 — Branding, Tracking UX, Header Interactions & Dispatch Clarity | 6 tasks | 1 / 6 |
| **Total** | **6 tasks** | **4 / 6** |

# Frontend & Backend Feature Enhancements

> **How to use this document:**
> - Work through tasks **strictly in order** — each phase depends on the previous.
> - After completing a task, tick its checkbox: `[ ]` → `[x]`
> - Keep the **Current Task Pointer** below updated after each completed task.
> - **DO NOT proceed to the next task without explicit user approval.**
> - Use the `master` branch for all tasks and use commit messages exactly as provided.
> - **File size rule:** No implementation file should exceed 250–300 lines. If a file grows beyond this, split it using named imports/exports rather than adding more code to the same file.

---

## Current Task Pointer

**Next task:** Task 4.2 — Fix Passenger Profile: Favourite Stops Selection Returns 403

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

## Phase 4 — Passenger Data Integrity & Experience Fixes

---

### Task 4.1 — Passenger-Linked Simulation: Reserve Seats for Real Passenger Profiles

**Files:** `backend/app/websocket/route_simulation.py`, `backend/app/services/boarding_service.py`

**Description:**
The simulation currently fills buses with anonymous boardings — every `BoardingRecord` created has `passenger_id = NULL`. This means the superadmin passenger report always shows zero boardings for every passenger, and the passenger's own trip history is empty even after hours of simulation.

This task first seeds 20 realistic passenger accounts (tenant-less, role = `passenger`) and then makes the simulation "reserve" a portion of each boarding wave for real passenger profiles. When a bus boards N passengers at a stop, a random subset of those N seats are silently assigned to randomly-sampled real passenger users by writing their `passenger_id` into the `BoardingRecord`. The remaining seats stay anonymous (representing travellers without an account). The total vehicle occupancy count is unchanged — this is purely a data-enrichment step that links some of the simulated boardings to real accounts so that reports and history become meaningful.

Fix steps:
1. **Seed 20 passenger accounts** in `backend/app/core/seed.py`. Add a new `_seed_passengers` function (called from `seed()` after `_seed_users`) that creates 20 users with:
   - `id`: `user-passenger-{n:02d}` (e.g. `user-passenger-01` … `user-passenger-20`)
   - `full_name`: `name_{n}` (e.g. `name_1` … `name_20`)
   - `email`: `passenger_{n}@email.com` (e.g. `passenger_1@email.com` … `passenger_20@email.com`)
   - `password_hash`: `hash_password(_SEED_PASSWORD)` (same `Password123!` as all other seeded users)
   - `role`: `"passenger"`, `tenant_id`: `None`, `is_deleted`: `False`
   - Use `_get_or_create` so re-running seed is idempotent. Skip any that already exist.
2. At the start of each simulated trip (in `route_simulation.py`, in the function that initialises a trip), query the DB once for all `passenger`-role user IDs (`User.role == 'passenger'`, `User.is_deleted == False`). Store them as a list on the trip state or pass them down. If no passengers exist, the simulation continues unchanged (all anonymous).
3. When processing a boarding event at a stop (the block that currently calls `boarding_service.record_stop_events` with an aggregate count), split the boarding count: take `min(boarding_count, len(passenger_ids))` passengers from the sampled list, pick them randomly, and write one `BoardingRecord` per selected passenger with their `passenger_id`. Record the remaining seats as a single anonymous aggregate record (the existing call). Use `random.sample` so the same passenger is not double-boarded on the same trip.
4. Similarly for alighting: for passengers who boarded (were tracked by `passenger_id`), write an alighting `BoardingRecord` with the same `passenger_id` when they alight.
5. Ensure `boarding_service.record_stop_events` already accepts `passenger_id: str | None` (it does — confirm and use it). If a single-passenger record path does not exist, add a thin `record_single_boarding(db, trip_id, stop_id, passenger_id, tenant_id, occupancy_after)` helper to `boarding_service.py` rather than modifying the batch path.
6. Write one backend test: after simulating two stop events (board then alight) with a real passenger ID passed explicitly through the service helper, two `BoardingRecord` rows exist for that passenger — one with `event_type = 'boarded'` and one with `event_type = 'alighted'`.

**Branch:** `master`
**Commit:** `feat: passenger-linked simulation reserves seats for real passenger profiles`

- [x] Task 4.1 complete

---

### Task 4.2 — Fix Passenger Profile: Favourite Stops Selection Returns 403

**Files:** `frontend/src/app/components/pages/passenger-app/PassengerProfileSection.tsx`, `frontend/src/app/services/routes.service.ts` (read only — do not modify), `frontend/src/app/services/passenger.service.ts`

**Description:**
Passengers who self-register (role = `passenger`, `tenant_id = null`) get a 403 when the profile page tries to load available stops to choose favourites from. The profile section calls `GET /api/v1/routes?isActive=true` (a tenant-scoped endpoint) to get the stop list — this endpoint requires `admin`/`operator`/`dispatcher` and rightly blocks passengers.

The fix is entirely in the frontend: replace the routes call with `GET /api/v1/stops/public` (already built in Task 2.1) to populate the available stops list in the profile section. The seeded passenger appeared to work because its favourites were pre-populated; self-registered passengers have an empty profile and see no stops to choose from because the population call fails silently.

Fix steps:
1. In `PassengerProfileSection.tsx`, locate the effect or call that fetches available routes/stops for the favourite stops selector. Replace it with a call to `getPublicStops()` (from `arrivals.service.ts`). The returned `GlobalStopRead[]` array (`{ id, name, lat, lng }`) is the list the user picks from.
2. The favourite stops selector UI should render each stop by name. When the user selects or deselects a stop, update `preferredStops` (an array of stop IDs) in the profile update payload — this field already exists in `PassengerProfileUpdate`.
3. After saving, call `PATCH /api/v1/passengers/me` with the new `preferredStops` list. This endpoint already works for passengers (`require_role("passenger")`).
4. On the **Live Tracking** tab (if it also fetches routes for the favourite-stop display), apply the same fix — use public stops data, not the tenant-scoped routes endpoint.
5. Write no backend tests for this task (it is a pure frontend fix). Verify in the browser that a self-registered passenger can open the profile, see all available stops in the selector, pick favourites, save, and see them reflected on next load.

**Branch:** `master`
**Commit:** `fix: passenger profile favourite stops use public stops endpoint instead of tenant routes`

- [ ] Task 4.2 complete

---

### Task 4.3 — Fix Passenger Alerts: 403 Errors and Bus-Approaching Notifications

**Files:** `frontend/src/app/components/layout/Header.tsx`, `backend/app/routers/passengers.py`, `backend/app/services/passenger_service.py`, `frontend/src/app/components/pages/passenger-app/PassengerDashboard.tsx` (or equivalent alerts display component)

**Description:**
Two separate issues exist:

**Issue A — Global 403 spam:** The `Header` component calls `listAlerts()` for every authenticated user, including passengers. Passengers are blocked by the tenant-scoped alerts endpoint. This produces repeated 403 errors in the console and may cause the header alert badge to show an error state.

**Issue B — No passenger notifications:** Even when the header is fixed, passengers have no way to receive notifications about buses approaching their favourite stops. The tenant alerts system is not designed for cross-tenant passengers.

Fix steps:
1. **Fix the header (Issue A):** In `Header.tsx`, guard the `listAlerts()` call so it only fires when `currentUser.role` is one of `admin`, `operator`, `dispatcher`. For `passenger` and `superadmin` roles, skip the call entirely and render the bell icon without a badge. This eliminates the 403 console errors.
2. **Add passenger notifications endpoint (Issue B):** In `backend/app/routers/passengers.py`, add `GET /api/v1/passengers/me/notifications`. This endpoint requires `require_role("passenger")`. It reads the authenticated passenger's `preferred_stops` from their profile, then calls `get_cross_tenant_arrivals` (already in `arrival_service.py`) for each favourite stop, and returns a flat list of arrivals at those stops. Response shape: `{ stopName: string, arrivals: ArrivalEstimate[] }[]` — one entry per favourite stop that has at least one approaching bus (stops with zero arrivals are omitted). If the passenger has no favourite stops or no buses are approaching any of them, return `[]`.
3. **Wire the frontend:** In the passenger app (check `PassengerDashboard.tsx` or the live-tracking component that currently shows favourite stops), call `GET /api/v1/passengers/me/notifications` on mount and every 30 seconds. Display a notification card per favourite stop that has approaching buses, showing the stop name and a compact arrival list (registration number, route name, ETA). If the list is empty, show "No buses approaching your favourite stops right now."
4. **Passenger service schema:** Add a `PassengerNotification` Pydantic schema (`stop_name: str`, `arrivals: list[PublicArrivalRead]`) to `backend/app/schemas/passenger.py` and a corresponding TypeScript interface `PassengerNotification` to `frontend/src/app/lib/api-types.ts`.
5. Write one backend test: a passenger with one favourite stop that has an active vehicle on a route serving that stop receives a non-empty notifications response.

**Branch:** `master`
**Commit:** `fix: passenger alerts 403 and bus-approaching notifications for favourite stops`

- [ ] Task 4.3 complete

---

## Implementation Summary

| Phase | Title | Tasks | Status |
|-------|-------|-------|--------|
| 4 | Passenger Data Integrity & Experience Fixes | 4.1, 4.2, 4.3 | Not started |

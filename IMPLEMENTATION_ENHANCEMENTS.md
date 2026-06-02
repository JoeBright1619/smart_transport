# Frontend & Backend Feature Enhancements

> **How to use this document:**
> - Work through tasks **strictly in order** — each phase depends on the previous.
> - After completing a task, tick its checkbox: `[ ]` → `[x]`
> - Keep the **Current Task Pointer** below updated after each completed task.
> - **DO NOT proceed to the next task without explicit user approval.**
> - Use the `master` branch for all tasks and use commit messages exactly as provided.

---

## Current Task Pointer

**Next task:** Task 10.1 — Backend: Report Filter Parameters and Endpoint Enhancements

---

> [!IMPORTANT]
> **Agent Rule:** After completing each task, stop and report:
> 1. What was implemented
> 2. Any decisions made or problems encountered
> 3. A commit message for what was implemented
> 4. Then ask: _"Ready to proceed to the next task?"_
> Do not move forward until the user confirms.

---

## Phase 10 — Advanced Reporting & Filtered Analytics

---

### Task 10.1 — Backend: Report Filter Parameters and Endpoint Enhancements

**Files:** `backend/app/routers/analytics.py`, `backend/app/services/analytics_service.py`, `backend/app/schemas/analytics.py`, `backend/app/crud/analytics.py`

**Description:**
Extend analytics endpoints with optional filter parameters: route_id, vehicle_id, driver_id, date_from, date_to, report_type (route/daily/fleet/driver). Add GET /analytics/report returning { report_type, filters_applied, generated_at, data }. Add pytest cases.

Fix steps:
1. Add optional query params: route_id, vehicle_id, driver_id, date_from (default -30d), date_to, report_type enum.
2. Branch analytics_service logic on report_type: route (on-time rate, avg duration, total passengers, revenue per route), daily (trips/day, completed vs cancelled, passengers, revenue), fleet (per-vehicle utilisation %, maintenance events, total km, status counts), driver (trips completed, on-time rate, avg duration, passengers per driver).
3. All queries must enforce tenant_id isolation.
4. Return envelope: { report_type, filters_applied, generated_at, data: [...] }.
5. Add GET /analytics/report endpoint; keep existing endpoints untouched.
6. Write two pytest cases: route-filtered and daily aggregation.

**Branch:** `master`
**Commit:** `feat: add filtered analytics report endpoint with route, daily, fleet, and driver views`

- [ ] Task 10.1 complete

---

### Task 10.2 — Frontend: Filtered Report UI with Export

**Files:** `frontend/src/app/components/pages/Analytics.tsx`, `analytics/AnalyticsChartsTabs.tsx`, `analytics/AnalyticsDateRange.tsx`, `analytics/analytics-helpers.ts`, `analytics/analytics-pdf.ts`, `frontend/src/app/services/analytics.service.ts`

**Description:**
Expose new filter parameters in the Analytics UI with a Report Type selector and context-sensitive filters for each type. Results rendered in appropriate tables/charts. Export as CSV and PDF.

Fix steps:
1. Add Report Type selector tabs: Route, Daily, Fleet, Driver.
2. Show context-sensitive filter controls: Route → route picker, Daily → date range, Fleet → vehicle multi-select, Driver → driver picker.
3. Wire all filters to GET /analytics/report, debounced 400ms.
4. Render data: Route/Driver → sortable table; Daily → bar chart + summary row; Fleet → table with status badge column.
5. Export PDF button using exportAnalyticsPDF with active filters and data.
6. Export CSV button serialising data to downloadable .csv.
7. Loading skeleton while in-flight; empty-state card when no data.

**Branch:** `master`
**Commit:** `feat: add filtered report UI with route, daily, fleet, and driver views and CSV/PDF export`

- [ ] Task 10.2 complete

---

### Task 10.3 — Passenger Trip History Report

**Files:** `backend/app/routers/analytics.py`, `backend/app/services/analytics_service.py`, `backend/app/schemas/analytics.py`, `frontend/src/app/components/pages/Analytics.tsx`, `frontend/src/app/services/analytics.service.ts`

**Description:**
Admin report showing every journey a specific passenger made in a date range. Returns route, boarding stop, alighting stop, date/time. If journey data doesn't exist yet, returns empty list with informational message.

Fix steps:
1. Add GET /analytics/passenger-report with params: passenger_id (uuid) or card_id (str), date_from, date_to.
2. Return list: { journey_id, trip_date, route_name, boarding_stop, alighting_stop, duration_minutes }.
3. If journey table does not exist, return empty list with message field.
4. Add Passenger report tab in Analytics UI: passenger search input, date range, results table, total journeys summary.
5. Export CSV named passenger-<id>-report.csv.

**Branch:** `master`
**Commit:** `feat: add passenger trip history report endpoint and UI`

- [ ] Task 10.3 complete

---

## Phase 11 — Authentication, Invitation & Registration Overhaul

---

### Task 11.1 — Gmail SMTP Email Service for Staff Invitations

**Files:** `backend/app/core/email.py` (new), `backend/app/routers/users.py`, `backend/app/services/user_service.py`, `backend/app/schemas/auth.py`, `backend/.env.example`

**Description:**
When an admin invites a staff user, send a real invitation email via Gmail SMTP. Email contains a personalised invite link. Accept-invite endpoint lets recipient set password.

Fix steps:
1. Create backend/app/core/email.py with EmailService class reading SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM_NAME from env. Use smtplib+ssl with Gmail smtp.gmail.com:465. Expose send_invitation(to_email, to_name, invite_link, tenant_name) and send_verification(to_email, to_name, otp_code).
2. Add SMTP_* variables to .env.example with placeholder values and comment about Gmail App Passwords.
3. In user_service.create_invitation: generate signed JWT (48h expiry), store hash with status=invited, call EmailService.send_invitation, remove raw token from API response.
4. Add POST /users/accept-invite accepting { token, new_password }: verify JWT, set password hash, status=active, invalidate token.
5. Document Gmail App Password requirement in comment.

**Branch:** `master`
**Commit:** `feat: add Gmail SMTP email service and staff invitation flow`

- [ ] Task 11.1 complete

---

### Task 11.2 — Passenger Self-Registration with Email OTP Verification

**Files:** `backend/app/routers/auth.py`, `backend/app/services/user_service.py`, `backend/app/models/user.py`, `backend/app/schemas/auth.py`, `backend/alembic/versions/` (new migration), `backend/app/core/email.py`, `frontend/src/app/components/pages/RegisterPage.tsx`, `frontend/src/app/services/auth.service.ts`

**Description:**
Passengers register themselves (not invited by admin). Registration requires email OTP verification before account is activated.

Fix steps:
1. Add to User model: otp_code (hashed str), otp_expires_at (datetime), email_verified (bool default False). Status pending_verification for unverified passengers. Create Alembic migration.
2. Add POST /auth/register/passenger accepting { full_name, email, phone, password }: create user role=passenger status=pending_verification, generate 6-digit OTP, hash+store with 15min expiry, call EmailService.send_verification, return { message: "Verification OTP sent to your email." }.
3. Add POST /auth/verify-email accepting { email, otp }: verify hash, check not expired, set email_verified=True status=active, clear OTP fields, return login token pair.
4. Add POST /auth/resend-otp accepting { email } with 60-second rate limit.
5. In RegisterPage.tsx: Step 1 — Full Name, Email, Phone, Password, Confirm Password. Step 2 — 6-digit OTP input with countdown timer and Resend OTP link (disabled 60s). On success redirect to passenger login.

**Branch:** `master`
**Commit:** `feat: passenger self-registration with email OTP verification`

- [ ] Task 11.2 complete

---

### Task 11.3 — Improved Registration UX: Multi-Step Form

**Files:** `frontend/src/app/components/pages/RegisterPage.tsx`, `frontend/src/app/components/ui/PasswordStrengthMeter.tsx` (new), `frontend/src/app/components/ui/OtpInput.tsx` (new)

**Description:**
Redesign RegisterPage as a 3-step wizard with visual progress, inline validation, password strength meter, and mobile-responsive layout.

Fix steps:
1. Replace flat form with 3-step wizard: Step 1 — Account Details (Full Name, Email, Phone with +250 prefix, Password, Confirm Password). Step 2 — Email Verification (6 OTP digit boxes, auto-advance focus, MM:SS countdown, Resend link). Step 3 — Success screen with animation and Go to Login button.
2. Create PasswordStrengthMeter component: coloured progress bar (Weak/Fair/Strong/Very Strong) based on length, uppercase, lowercase, digits, symbols.
3. Validate all fields on blur: email RFC format, phone must start 07 or +2507 (10 digits Rwanda mobile), password min 8 chars with uppercase and digit, confirm password must match.
4. Add step progress indicator at top (numbered circles or step bar).
5. Disable Next button until all Step 1 fields pass validation.
6. Make page responsive for mobile (passengers register on phones).
7. Add footer note: "Are you a staff member? Contact your administrator for an invitation."

**Branch:** `master`
**Commit:** `feat: multi-step passenger registration UX with password strength and OTP input`

- [ ] Task 11.3 complete

---

## Phase 12 — Passenger Profile, Occupancy Simulation & Journey Statistics

---

### Task 12.1 — Passenger profile preferences — preferred routes, favourite stops, and notification opt-ins stored server-side

**Files:** `backend/app/models/passenger_profile.py` (new), `backend/app/schemas/passenger_profile.py` (new), `backend/app/services/passenger_profile_service.py` (new), `backend/app/routers/passengers.py` (new), `backend/alembic/versions/` (new migration), `frontend/src/app/services/passengers.service.ts`, `frontend/src/app/lib/api-types.ts`, `frontend/src/app/components/pages/PassengerApp.tsx`

**Description:**
Add a `passenger_profiles` table that extends the existing `User` model for users with role `passenger`. The table stores: `preferred_route_ids` (JSON array of route IDs), `favourite_stop_ids` (JSON array of stop IDs), and `notify_on_delay` / `notify_on_crowding` boolean flags. Expose four endpoints under `/api/v1/passengers/me`: GET (read own profile), PUT (full replace), PATCH (partial update), and a dedicated PATCH `/api/v1/passengers/me/favourites` for toggling a single stop or route. All endpoints require the `passenger` role and are scoped to the caller's own record — no cross-user access is possible. On the frontend, replace the current `localStorage`-only favourite-stops logic in `PassengerApp.tsx` with calls to the new API so favourites survive across devices and browser clears. The profile panel is a collapsible section at the top of the Passenger App page, showing the logged-in user's name, a route multi-select for preferred routes, and toggle switches for the two notification flags.

Fix steps:
1. Create `/backend/app/models/passenger_profile.py` with a `PassengerProfile` SQLAlchemy model: `id` (PK, `prof-<uuid>`), `user_id` (FK `users.id`, unique), `tenant_id` (FK `tenants.id`), `preferred_route_ids` (JSON), `favourite_stop_ids` (JSON), `notify_on_delay` (Boolean, default False), `notify_on_crowding` (Boolean, default False), `updated_at` (DateTime, server-managed). Add the relationship back-reference on `User` using a lazy string reference so there is no circular import.
2. Add a Pydantic schema file `/backend/app/schemas/passenger_profile.py` with `PassengerProfileRead`, `PassengerProfileUpdate` (all fields optional), and `PassengerFavouriteToggle` (fields: `type: Literal['route','stop']`, `id: str`, `action: Literal['add','remove']`).
3. Create `/backend/app/services/passenger_profile_service.py` with `get_or_create_profile(db, user_id, tenant_id)`, `update_profile(db, user_id, tenant_id, data: PassengerProfileUpdate)`, and `toggle_favourite(db, user_id, tenant_id, toggle: PassengerFavouriteToggle)`. The toggle function reads the JSON array, adds or removes the ID, and writes back; it validates that the referenced route/stop ID belongs to the caller's tenant.
4. Create `/backend/app/routers/passengers.py` with the four endpoints described above, all guarded by `require_role('passenger')`. Wire the router into `main.py`.
5. Generate an Alembic migration for the `passenger_profiles` table.
6. In `/frontend/src/app/services/passengers.service.ts` add `getMyProfile()`, `updateMyProfile(data)`, and `toggleFavourite(toggle)` API calls.
7. Update `api-types.ts` with `PassengerProfileRead`, `PassengerProfileUpdate`, and `PassengerFavouriteToggle` interfaces.
8. In `PassengerApp.tsx`, replace the `loadFavoriteStops` / `localStorage.setItem` calls with `getMyProfile()` on mount and `toggleFavourite()` on heart-click. Wrap in a try/catch so the component degrades to local state if the user is unauthenticated.
9. Add the collapsible profile preferences panel above the stop search bar. It should show `fullName`, a `RouteSelect` multi-select pre-populated from `preferredRouteIds`, and two toggle switches for `notifyOnDelay` and `notifyOnCrowding`. Save triggers `updateMyProfile()`.
10. Write backend unit tests: GET profile for new passenger creates a blank profile; PATCH preferred routes replaces the list; toggle add/remove a favourite stop; cross-tenant stop ID is rejected with 404.

**Branch:** `master`
**Commit:** `feat(12.1): add passenger profile preferences API and wire PassengerApp favourites to server-side storage`

- [ ] Task 12.1 complete

---

### Task 12.2 — Simulated boarding counts — real-time occupancy on active trips exposed via WebSocket and arrival API

**Files:** `backend/app/websocket/route_simulation.py`, `backend/app/models/vehicle.py`, `backend/alembic/versions/` (new migration), `backend/app/schemas/vehicles.py`, `backend/app/services/arrival_service.py`, `backend/app/schemas/arrivals.py`, `backend/app/routers/trips.py`, `backend/app/schemas/trip.py`, `frontend/src/app/lib/api-types.ts`, `frontend/src/app/components/pages/PassengerApp.tsx`, `frontend/src/app/components/pages/VehicleTracking.tsx`

**Description:**
Surface the passenger count that the simulation already computes in memory (in `_simulate_passengers_at_stop` inside `route_simulation.py`) as a first-class, real-time data field. Currently the in-memory `state['passengers']` list is computed every tick but is never broadcast to clients. This task: (1) exposes `current_passengers` and `available_seats` on the WebSocket vehicle-position payload so the tracking map can show a live occupancy badge on each vehicle marker; (2) adds `currentPassengers` and `availableSeats` to the `ArrivalEstimate` schema so passengers waiting at a stop can see whether the next bus has room; (3) adds a `PATCH /api/v1/trips/{id}/passengers` endpoint that lets a dispatcher manually override the passenger count on an active trip (integer 0..capacity), enabling dispatchers to correct the simulation when they have ground truth data. No financial logic is introduced — this is purely an operational count.

Fix steps:
1. In `route_simulation.py`, update `get_or_init_state` to initialise `state['current_passengers'] = 0`. At the end of `_simulate_passengers_at_stop`, set `state['current_passengers'] = len(remaining_passengers)` and also write the value back to the associated `Vehicle` record via a new `Vehicle.current_passengers` column (see next step).
2. Add `current_passengers: Mapped[int]` (Integer, default 0, nullable=False) to the `Vehicle` model. Generate an Alembic migration.
3. Update the WebSocket broadcast: in the vehicle-positions message builder (wherever `WsVehiclePosition` dicts are assembled), add `currentPassengers: vehicle.current_passengers` and `availableSeats: max(0, vehicle.capacity - vehicle.current_passengers)`.
4. Update `api-types.ts`: add `currentPassengers: number` and `availableSeats: number` to `WsVehiclePosition`, and add them to `ArrivalEstimate`.
5. Update `arrival_service.py`: read `vehicle.current_passengers` when building each `ArrivalRead` object and include it in the response.
6. Update `ArrivalRead` schema (both Pydantic and `api-types.ts`) to include `currentPassengers: int` and `availableSeats: int`.
7. Add `PATCH /api/v1/trips/{id}/passengers` to `trips.py` router. Accept body `{ passengers: int }`. Validate 0 <= value <= vehicle.capacity; update `Trip.passengers` and `Vehicle.current_passengers` atomically. Require `dispatcher` or `admin` role. Audit-log the change.
8. Add the Pydantic schema `TripPassengerUpdate` (field: `passengers: int = Field(ge=0)`) to `schemas/trip.py`.
9. In `PassengerApp.tsx`, update the arrival card to show an occupancy pill: e.g. '34/60 seats' coloured green (< 70 %), amber (70–90 %), red (> 90 %). Use a `getOccupancyColour(current, capacity)` helper.
10. In `VehicleTracking` page/map popup, display the occupancy badge ('34/60') and a mini progress bar for the active vehicle's current load using the `currentPassengers` / `availableSeats` fields from the WebSocket message.
11. Write backend unit tests: passenger count increases when boarding is simulated; PATCH endpoint rejects values above capacity; PATCH endpoint updates both Trip and Vehicle records; arrival response includes correct availableSeats.

**Branch:** `master`
**Commit:** `feat(12.2): expose real-time simulated occupancy on WebSocket and arrivals API, add dispatcher manual passenger-count override`

- [ ] Task 12.2 complete

---

### Task 12.3 — Passenger journey statistics dashboard — per-passenger trip history and route usage summary

**Files:** `backend/app/models/passenger_boarding_intent.py` (new), `backend/alembic/versions/` (new migration), `backend/app/routers/passengers.py`, `backend/app/schemas/passenger_profile.py`, `backend/app/services/arrival_service.py`, `backend/app/schemas/arrivals.py`, `frontend/src/app/lib/api-types.ts`, `frontend/src/app/services/passengers.service.ts`, `frontend/src/app/components/pages/PassengerApp.tsx`

**Description:**
Add a read-only statistics panel to the Passenger App that shows a logged-in passenger their personal travel history derived from completed `Trip` records. Because the simulation creates `Trip` rows (status='completed') with a `passengers` count and the trip belongs to a vehicle/route, individual passenger journeys cannot be tracked without a Tap&Go card — but the passenger can still see aggregate system-level statistics for routes they have marked as preferred: total completed trips on their preferred routes this week, average delay on those routes, and the on-time percentage. Additionally, provide an opt-in 'join trip' button on the Passenger App arrival card: when a passenger taps 'I'm boarding', a `PassengerBoardingIntent` record is created (user_id, trip_id, stop_id, boarded_at). This lightweight record does not affect fare calculation but allows the system to produce per-passenger trip counts. The new endpoint `GET /api/v1/passengers/me/stats` aggregates these intents plus completed trips on preferred routes and returns the dashboard payload.

Fix steps:
1. Create `/backend/app/models/passenger_boarding_intent.py` with `PassengerBoardingIntent`: `id` (PK), `user_id` (FK users.id), `tenant_id` (FK tenants.id), `trip_id` (FK trips.id), `stop_id` (FK stops.id), `boarded_at` (DateTime UTC). Index on `(user_id, tenant_id, boarded_at)`.
2. Generate an Alembic migration for `passenger_boarding_intents`.
3. Add `POST /api/v1/passengers/me/board` to `passengers.py` router. Body: `{ tripId: str, stopId: str }`. Validates the trip is active and the stop is on the trip's route and belongs to the tenant. Creates a `PassengerBoardingIntent` row. Rate-limited to one boarding intent per trip per user (409 if duplicate). Requires `passenger` role.
4. Add `GET /api/v1/passengers/me/stats` to `passengers.py`. Returns: `totalBoardings` (count of intents in last 30 days), `tripsThisWeek` (count of intent rows in last 7 days), `preferredRouteStats` (array of `{ routeId, routeName, totalTrips, onTimePercentage, avgDelayMinutes }` for each preferred route based on completed Trip rows), `mostUsedStopId` (stop_id with highest boarding intent count), `mostUsedStopName`. All data scoped to caller's tenant_id.
5. Add Pydantic schemas `PassengerBoardingIntentCreate`, `PassengerBoardingIntentRead`, and `PassengerStatsRead` to `schemas/passenger_profile.py`.
6. Add the corresponding TypeScript interfaces `PassengerBoardingIntentRead`, `PassengerStatsRead`, and `RouteStatSummary` to `api-types.ts`.
7. Add `boardTrip(tripId, stopId)` and `getMyStats()` to `passengers.service.ts`.
8. In `PassengerApp.tsx`, add a 'My Journey Stats' card below the favourites panel (visible only when logged in as passenger). Display: total boardings this month, trips this week, and a small table of preferred route stats (route number, on-time %, avg delay). If the passenger has no preferred routes, show a prompt to add some in the profile panel.
9. Add an 'I'm boarding' button to each arrival card. On click, call `boardTrip(arrival.vehicleId's active tripId, selectedStop)`. Show a toast confirmation 'Boarding recorded'. The button is disabled if already boarded on that trip (check against locally cached intent list). This requires the `ArrivalEstimate` to include `activeTripId: string | null` — add this field to the arrival schema and service.
10. Update `arrival_service.py` to join the active `Trip` for each vehicle and include `active_trip_id` in the `ArrivalRead` response.
11. Write backend unit tests: boarding intent creates record; duplicate boarding on same trip returns 409; stats endpoint returns zero counts for a new passenger; preferred route stats reflect completed trip data correctly; boarding intent on inactive trip returns 400.

**Branch:** `master`
**Commit:** `feat(12.3): add passenger boarding intent model and journey statistics dashboard endpoint`

- [ ] Task 12.3 complete

---

## Phase 13 — Passenger Capacity & Bus Occupancy Tracking

> **Note:** Since Phase 12 no longer uses tap-on/off as the occupancy trigger, occupancy is updated by the simulation system and by trip lifecycle events. The modifications below apply to all tasks in this phase:
>
> 1. **Occupancy source change.** Replace every reference to 'tap-on/tap-off event' with 'simulation boarding count (from `Vehicle.current_passengers`) or dispatcher manual override (from `PATCH /trips/{id}/passengers`)'. Task 12.2 now creates and maintains `Vehicle.current_passengers` as a persistent column that is updated each simulation tick, making it the authoritative live occupancy source Phase 13 reads from.
>
> 2. **Crowding alert trigger.** The crowding alert ('bus is full') should fire when `Vehicle.current_passengers >= Vehicle.capacity * 0.9` (90 % threshold) rather than when a tap-on event occurs. The alert generation logic in `simulation_runner.py` should be extended to check this condition after each tick, similar to the existing `LOW_FUEL_THRESHOLD` pattern. The alert type should be `'info'` with severity `'medium'`, title `'High Occupancy: {registration}'`, suppressed if an unacknowledged alert of the same type+vehicle already exists.
>
> 3. **Remaining seats display.** The 'remaining seats' value displayed in Phase 13 UI components is `vehicle.capacity - vehicle.current_passengers`, computed client-side from the two fields now present in the WebSocket payload (added in task 12.2). No new backend field is required.
>
> 4. **Passenger-facing occupancy (PassengerApp).** The occupancy badge added to `ArrivalEstimate` in task 12.2 (`currentPassengers`, `availableSeats`) is the data source for the Phase 13 passenger-facing 'seats available' display. Phase 13 does not need to add new API fields — it only needs to render the values task 12.2 already delivers.
>
> 5. **Analytics occupancy metric.** Phase 13 may have planned a 'peak occupancy' analytics chart. This can now use the `Trip.passengers` field (populated by the simulation on trip completion) and the new `PassengerBoardingIntent` count (from task 12.3) as the two data sources. No tap-card data is needed.
>
> 6. **No tasks removed from Phase 13.** All Phase 13 tasks remain valid; their internal references to 'tap events' simply become references to 'simulation tick updates' or 'dispatcher overrides'. The deliverables (capacity badge on map, seats-remaining on arrival card, crowding alert, occupancy chart in analytics) are all achievable with the new data model.

---

### Task 13.1 — Vehicle Capacity Model and Occupancy Fields

**Files:** `backend/app/models/vehicle.py`, `backend/alembic/versions/` (new migration), `backend/app/schemas/vehicles.py`, `backend/app/routers/vehicles.py`, `backend/app/services/vehicle_service.py`, `frontend/src/app/components/pages/fleet-management/AddVehicleDialog.tsx`

**Description:**
Add seating_capacity and current_occupancy to Vehicle model. Occupancy is updated by the simulation runner as the vehicle progresses along stops (simulated boarding/alighting), and reset to 0 on trip completion.

Fix steps:
1. Add to Vehicle model: seating_capacity (int, default 45), current_occupancy (int, default 0). Create Alembic migration.
2. Expose both fields in vehicle read schemas and GET /vehicles responses.
3. In simulation_runner.py, as the vehicle passes each stop: increment current_occupancy by a simulated value (random 0-5 passengers boarding, random 0-3 alighting, clamped to 0..seating_capacity).
4. On trip completion in trip_service.complete_trip, reset vehicle.current_occupancy = 0.
5. Add remaining_seats = seating_capacity - current_occupancy as computed field in vehicle schema (not stored).
6. Expose seating_capacity as editable field in AddVehicleDialog.tsx and fleet edit form.

**Branch:** `master`
**Commit:** `feat: add vehicle seating capacity and simulated real-time occupancy tracking`

- [ ] Task 13.1 complete

---

### Task 13.2 — Real-Time Occupancy via WebSocket and Tracking UI

**Files:** `backend/app/websocket/route_simulation.py`, `backend/app/services/simulation_runner.py`, `frontend/src/app/components/pages/VehicleTracking.tsx`, `frontend/src/app/components/pages/vehicle-tracking/VehicleListPanel.tsx`, `frontend/src/app/components/pages/vehicle-tracking/VehicleMapView.tsx`, `frontend/src/app/lib/ws-client.ts`

**Description:**
Broadcast occupancy changes over existing WebSocket so tracking map and vehicle list update in real time.

Fix steps:
1. When simulation updates current_occupancy, emit WebSocket event vehicle_occupancy_updated with { vehicle_id, current_occupancy, seating_capacity, remaining_seats }.
2. In ws-client.ts, handle vehicle_occupancy_updated and update the tracked vehicle object.
3. In VehicleListPanel.tsx: show occupancy bar (thin, green→yellow→red as fills) and text {current}/{max} seats, {remaining} remaining.
4. In VehicleMapView.tsx: add occupancy to selected-vehicle popup: X / Y seats occupied.
5. Change map marker tint when >80% full (yellow) or 100% full (red).
6. Hide occupancy bar and show "Not in service" if vehicle has no active trip.

**Branch:** `master`
**Commit:** `feat: real-time occupancy broadcast and tracking UI seat availability`

- [ ] Task 13.2 complete

---

### Task 13.3 — Capacity Alerts and Passenger-Facing Seat Availability

**Files:** `backend/app/services/alert_service.py`, `backend/app/services/simulation_runner.py`, `backend/app/routers/alerts.py`, `backend/app/routers/vehicles.py`, `frontend/src/app/components/pages/Alerts.tsx`, `frontend/src/app/components/pages/PassengerApp.tsx`

**Description:**
Auto-generate alerts when a vehicle reaches or exceeds capacity. Passengers on the passenger app can see real-time seat availability for approaching buses.

Fix steps:
1. In simulation_runner.py after updating current_occupancy: if current_occupancy == seating_capacity, call alert_service.create_capacity_alert severity=warning, title=Bus Full: {plate}. If current_occupancy > seating_capacity, severity=critical, title=Excess Passengers: {plate}.
2. Ensure alert_service.create_capacity_alert creates Alert record and broadcasts via WebSocket new_alert event.
3. Add type=capacity to alert type enum if not present; migrate if needed.
4. In Alerts UI, add Capacity filter tab alongside existing type tabs.
5. Add GET /vehicles/{vehicle_id}/occupancy returning { vehicle_id, seating_capacity, current_occupancy, remaining_seats, status: available|nearly_full|full }. Thresholds: >=10 = available; 1-9 = nearly_full; 0 = full.
6. In PassengerApp.tsx, show occupancy badge on approaching vehicle detail: green (Seats available, X remaining), yellow (Nearly full, X remaining), red (Bus is full — wait for next bus).

**Branch:** `master`
**Commit:** `feat: capacity alerts for full buses with passenger-facing seat availability`

- [ ] Task 13.3 complete

---

## Implementation Summary

| Phase | Title | Tasks | Status |
|-------|-------|-------|--------|
| 10 | Advanced Reporting & Filtered Analytics | 10.1, 10.2, 10.3 | Not started |
| 11 | Authentication, Invitation & Registration Overhaul | 11.1, 11.2, 11.3 | Not started |
| 12 | Passenger Profile, Occupancy Simulation & Journey Statistics | 12.1, 12.2, 12.3 | Not started |
| 13 | Passenger Capacity & Bus Occupancy Tracking | 13.1, 13.2, 13.3 | Not started |

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

**Next task:** Task 10.3 — Passenger Trip History Report

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
The existing analytics endpoints return aggregated data for the whole tenant. Extend them to accept filter parameters so reports can be scoped to a specific route, date range, fleet subset, or individual driver. Also introduce two new report types: a **daily performance snapshot** and a **fleet status summary**.

Fix steps:
1. Add optional query parameters to existing analytics endpoints:
   - `route_id: Optional[uuid]` — filter metrics to a single route.
   - `vehicle_id: Optional[uuid]` — filter to a single vehicle.
   - `driver_id: Optional[uuid]` — filter to a single driver.
   - `date_from: Optional[date]` and `date_to: Optional[date]` — inclusive date range (default: last 30 days).
   - `report_type: Literal["route", "daily", "fleet", "driver"]` — selects the report shape returned.
2. In `analytics_service.py`, branch logic on `report_type`:
   - `route` — on-time rate, average trip duration, total passengers, utilisation per route.
   - `daily` — total trips, completed vs. cancelled, total passengers aggregated by calendar day within the range.
   - `fleet` — per-vehicle utilisation percentage, maintenance events, total km (from trips), current status counts.
   - `driver` — trips completed, on-time rate, average trip duration, total passengers carried per driver.
3. All filtered queries must respect the tenant isolation (`tenant_id`) already applied elsewhere.
4. Return a consistent envelope: `{ report_type, filters_applied, generated_at, data: [...] }`.
5. Add a new `GET /analytics/report` endpoint that accepts all the above parameters and returns the filtered report. Keep existing endpoints untouched for backwards compatibility.
6. Write at least two pytest cases: one for route-filtered output and one for daily aggregation.

**Branch:** `master`
**Commit:** `feat: add filtered analytics report endpoint with route, daily, fleet, and driver views`

- [x] Task 10.1 complete

---

### Task 10.2 — Frontend: Filtered Report UI with Export

**Files:** `frontend/src/app/components/pages/Analytics.tsx`, `frontend/src/app/components/pages/analytics/AnalyticsChartsTabs.tsx`, `frontend/src/app/components/pages/analytics/AnalyticsDateRange.tsx`, `frontend/src/app/components/pages/analytics/analytics-helpers.ts`, `frontend/src/app/components/pages/analytics/analytics-pdf.ts`, `frontend/src/app/services/analytics.service.ts`

**Description:**
Expose the new backend filter parameters in the Analytics UI so operators can generate specific reports instead of only seeing the global aggregate view.

Fix steps:
1. Add a **Report Type** selector (tabs or dropdown): `Route`, `Daily`, `Fleet`, `Driver`.
2. Show context-sensitive filter controls beneath the selector:
   - `Route` → route picker (dropdown of all tenant routes).
   - `Daily` → date-range picker (reuse `AnalyticsDateRange`).
   - `Fleet` → vehicle multi-select or "All Vehicles".
   - `Driver` → driver picker.
3. Wire all filter controls to `analytics.service.ts`, calling `GET /analytics/report` with the selected parameters on every filter change (debounced 400 ms).
4. Render the returned `data` array in a results table appropriate to the report type:
   - Route and Driver reports → sortable table.
   - Daily report → bar chart (trips per day) + summary row.
   - Fleet report → table with a status badge column.
5. Add an **Export PDF** button that passes the active filters and the returned data into `exportAnalyticsPDF`, replacing the current hard-coded export.
6. Add an **Export CSV** button that serialises `data` into a downloadable `.csv` file.
7. Show a loading skeleton while the request is in-flight and an empty-state card when no data matches the filters.

**Branch:** `master`
**Commit:** `feat: add filtered report UI with route, daily, fleet, and driver views and CSV/PDF export`

- [x] Task 10.2 complete

---

### Task 10.3 — Passenger Trip History Report

**Files:** `backend/app/routers/analytics.py`, `backend/app/services/analytics_service.py`, `backend/app/schemas/analytics.py`, `frontend/src/app/components/pages/Analytics.tsx`, `frontend/src/app/services/analytics.service.ts`

**Description:**
Admins should be able to pull a report showing every trip a specific passenger was recorded on during a date range, including the route taken, boarding stop, alighting stop, and timestamps. No fare or payment data is included — this is purely operational passenger information derived from trip and arrival records.

Fix steps:
1. Add `GET /analytics/passenger-report` with query parameters:
   - `passenger_id: uuid` (required) or lookup by name/email.
   - `date_from`, `date_to` (default: last 30 days).
2. Return a list of trip records: `{ trip_id, trip_date, route_name, boarding_stop, alighting_stop, scheduled_departure, actual_departure, scheduled_arrival, actual_arrival, on_time: bool }`.
3. If no trip records exist for the passenger, return an empty list with a `"message": "No trip records found for this passenger in the selected period."` field.
4. In the Analytics UI, add a fifth report type tab `Passenger` with:
   - A passenger search input (by name or email).
   - Date range picker.
   - Results table showing the journey history columns listed above.
   - Total trips and on-time rate summary row at the bottom.
5. Export CSV of the passenger report, named `passenger-<id>-report.csv`.

**Branch:** `master`
**Commit:** `feat: add passenger trip history report endpoint and UI`

- [ ] Task 10.3 complete

---

## Phase 11 — Authentication, Invitation & Registration Overhaul

---

### Task 11.1 — Gmail SMTP Email Service for Staff Invitations

**Files:** `backend/app/core/email.py` _(new)_, `backend/app/routers/users.py`, `backend/app/services/user_service.py`, `backend/app/schemas/auth.py`, `backend/.env.example`

**Description:**
When an admin invites a new staff user (operator, driver account, etc.) the system should send a real invitation email via Gmail SMTP instead of returning a raw token in the response. The email contains a personalised invitation link the recipient clicks to set their password and activate their account.

Fix steps:
1. Create `backend/app/core/email.py` with an `EmailService` class that:
   - Reads `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM_NAME` from environment variables.
   - Uses Python's `smtplib` + `ssl` with Gmail SMTP (`smtp.gmail.com:465` TLS or `587` STARTTLS).
   - Exposes `send_invitation(to_email, to_name, invite_link, tenant_name)` and `send_verification(to_email, to_name, otp_code)` helpers.
   - Uses `email.mime.multipart.MIMEMultipart` to send both plain-text and HTML variants.
   - Logs failures without crashing the request; raise a 500 only if the send is critical.
2. Add `SMTP_*` variables to `.env.example` with placeholder values and a comment explaining Gmail App Passwords (not account password).
3. In `user_service.create_invitation`, generate a signed JWT invitation token (expires 48 h), store the token hash in the user record (status `invited`), then call `EmailService.send_invitation`. Remove any code that returns the raw token in the API response.
4. Add `POST /users/accept-invite` that accepts `{ token, new_password }`, verifies the JWT, sets the password hash, changes status to `active`, and invalidates the token.
5. The invite email HTML should include the tenant name, recipient's name, and a clearly visible "Accept Invitation" button linking to `{FRONTEND_URL}/accept-invite?token=...`.

**Branch:** `master`
**Commit:** `feat: add Gmail SMTP email service and staff invitation flow`

- [ ] Task 11.1 complete

---

### Task 11.2 — Passenger Self-Registration with Email OTP Verification

**Files:** `backend/app/routers/auth.py`, `backend/app/services/user_service.py`, `backend/app/models/user.py`, `backend/app/schemas/auth.py`, `backend/alembic/versions/` _(new migration)_, `backend/app/core/email.py`, `frontend/src/app/components/pages/RegisterPage.tsx`, `frontend/src/app/services/auth.service.ts`

**Description:**
Passengers must register themselves — not be invited by an admin. The registration flow requires email verification via a 6-digit OTP before the account is activated. This is separate from the staff invitation flow in Task 11.1.

Fix steps:
1. In `user.py` model, add:
   - `otp_code: Optional[str]` — hashed 6-digit OTP.
   - `otp_expires_at: Optional[datetime]`.
   - `email_verified: bool` (default `False`).
   - Use `"pending_verification"` status for unverified passengers.
2. Create Alembic migration for the new columns.
3. Add `POST /auth/register/passenger` accepting `{ full_name, email, phone, password }`:
   - Create user with `role = "passenger"`, `status = "pending_verification"`.
   - Generate a 6-digit OTP, hash it, store with 15-minute expiry.
   - Call `EmailService.send_verification(email, name, otp)`.
   - Return `{ message: "Verification OTP sent to your email." }` — never return the OTP itself.
4. Add `POST /auth/verify-email` accepting `{ email, otp }`:
   - Look up the user by email, verify OTP hash, check not expired.
   - Set `email_verified = True`, `status = "active"`, clear OTP fields.
   - Return a login token pair so the user is immediately logged in after verification.
5. Add `POST /auth/resend-otp` accepting `{ email }` with a 60-second rate limit (track `otp_resent_at` timestamp, reject if within 60 s).
6. In `RegisterPage.tsx`:
   - Step 1 form: Full Name, Email, Phone, Password, Confirm Password — submit calls `POST /auth/register/passenger`.
   - Step 2 form: 6-digit OTP input. Show a countdown timer and "Resend OTP" link (disabled until 60 s elapsed).
   - On success, redirect to the passenger dashboard.
7. Existing staff registration via invitation (Task 11.1) is unaffected.

**Branch:** `master`
**Commit:** `feat: passenger self-registration with email OTP verification`

- [ ] Task 11.2 complete

---

### Task 11.3 — Improved Registration UX: Multi-Step Form with Validation

**Files:** `frontend/src/app/components/pages/RegisterPage.tsx`, `frontend/src/app/components/ui/PasswordStrengthMeter.tsx` _(new)_, `frontend/src/app/components/ui/OtpInput.tsx` _(new)_

**Description:**
The current RegisterPage is a minimal single-page form. Redesign it as a proper product registration experience with visual progress steps, inline validation, and clear feedback at every stage.

Fix steps:
1. Replace the flat form with a **3-step wizard**:
   - Step 1 — Account Details: Full Name, Email, Phone Number (with `+250` Rwanda prefix pre-filled), Password, Confirm Password.
   - Step 2 — Email Verification: 6 separate digit input boxes that auto-advance focus on each keystroke. MM:SS countdown timer. "Resend OTP" link (disabled until 60 s elapsed). "Back" link to restart if wrong email.
   - Step 3 — Success: Confirmation animation, "Welcome aboard" message, "Go to Dashboard" button.
2. Create a `PasswordStrengthMeter` component that shows a coloured progress bar labelled Weak / Fair / Strong / Very Strong, evaluated on: length ≥ 8, uppercase present, lowercase present, digit present, symbol present.
3. All fields validate on blur:
   - Email: RFC-5322 format.
   - Phone: must start with `07` or `+2507` and be 10 digits total (Rwanda mobile standard).
   - Password: minimum 8 characters, at least one uppercase letter and one digit.
   - Confirm Password: must match the Password field exactly.
4. Add a step progress indicator at the top of the card (three numbered circles connected by lines, current step highlighted).
5. The "Next" button in Step 1 is disabled until all fields pass inline validation.
6. The page must be fully responsive and usable on a 375 px mobile viewport (passengers primarily register on phones).
7. Add a footer note below the form: _"Are you a staff member? Contact your administrator for an invitation."_

**Branch:** `master`
**Commit:** `feat: multi-step passenger registration UX with password strength and OTP input`

- [ ] Task 11.3 complete

---

## Phase 12 — Passenger Profile, Simulated Boardings & Journey Statistics

---

### Task 12.1 — Passenger Profile Management and Preferences

**Files:** `backend/app/models/passenger_profile.py` _(new)_, `backend/app/schemas/passenger.py` _(new)_, `backend/app/routers/passengers.py` _(new)_, `backend/app/services/passenger_service.py` _(new)_, `backend/app/crud/passenger.py` _(new)_, `backend/alembic/versions/` _(new migration)_, `frontend/src/app/components/pages/PassengerApp.tsx`

**Description:**
Once a passenger is registered, they should have a profile where they can store preferred routes and stops for quick access, and configure notification preferences (e.g. which routes to watch for arrival alerts). This enriches the passenger information experience without involving any payment or fare system.

Fix steps:
1. Create `backend/app/models/passenger_profile.py`:
   ```
   PassengerProfile:
     id (uuid, PK)
     user_id (uuid, FK → users.id, unique)
     phone (str, nullable)
     preferred_routes (ARRAY of route_id uuid, default [])
     preferred_stops (ARRAY of stop_id uuid, default [])
     notify_on_arrival (bool, default True)
     notify_on_delay (bool, default True)
     total_trips_recorded (int, default 0)
     tenant_id (uuid, FK → tenants.id)
   ```
2. Create Alembic migration.
3. Auto-create a `PassengerProfile` row when a new passenger account is activated (call from `auth/verify-email`).
4. Add `GET /passengers/me` returning the full profile including preferred routes and stops with their names resolved.
5. Add `PATCH /passengers/me` accepting any subset of: `phone`, `preferred_routes`, `preferred_stops`, `notify_on_arrival`, `notify_on_delay`.
6. Add `GET /passengers` (admin only) returning a paginated list of all passengers with `total_trips_recorded` and registration date.
7. In `PassengerApp.tsx`, add a **My Profile** section with:
   - Display name and phone (editable inline).
   - A "Favourite Routes" multi-select that loads all tenant routes and saves selections via `PATCH /passengers/me`.
   - A "Favourite Stops" multi-select similarly.
   - Toggle switches for arrival and delay notifications.

**Branch:** `master`
**Commit:** `feat: passenger profile with preferred routes, stops, and notification preferences`

- [ ] Task 12.1 complete

---

### Task 12.2 — Simulated Passenger Boardings and Per-Trip Occupancy Records

**Files:** `backend/app/models/boarding_record.py` _(new)_, `backend/app/schemas/boarding.py` _(new)_, `backend/app/routers/boardings.py` _(new)_, `backend/app/services/boarding_service.py` _(new)_, `backend/app/services/simulation_runner.py`, `backend/alembic/versions/` _(new migration)_, `frontend/src/app/components/pages/PassengerApp.tsx`

**Description:**
To track how many passengers a bus carries on each trip and feed occupancy data to Phase 13, the simulation runner should generate plausible boarding and alighting events as the simulated vehicle moves through route stops. These events are stored as boarding records (no fare, no card) and used to compute `current_occupancy` on the vehicle in real time.

Fix steps:
1. Create `backend/app/models/boarding_record.py`:
   ```
   BoardingRecord:
     id (uuid, PK)
     trip_id (uuid, FK → trips.id)
     stop_id (uuid, FK → stops.id)
     passenger_id (uuid, FK → users.id, nullable — optional if passenger is logged in)
     event_type (enum: boarded, alighted)
     recorded_at (datetime)
     occupancy_after (int)
     tenant_id (uuid, FK → tenants.id)
   ```
2. Create Alembic migration.
3. In `simulation_runner.py`, when the simulated vehicle arrives at each stop:
   - Generate a random boarding count (0–5) and alighting count (0–3), clamped so `current_occupancy` never goes below 0 or above `vehicle.seating_capacity`.
   - Call `boarding_service.record_stop_events(trip_id, stop_id, boardings, alightings)` which persists individual `BoardingRecord` rows and updates `vehicle.current_occupancy`.
4. Expose `GET /boardings?trip_id=&stop_id=&date_from=&date_to=` (admin) returning boarding records with stop names resolved.
5. In `PassengerApp.tsx`, add a **My Trips** section showing trips the logged-in passenger was recorded on (where `passenger_id` is set), with the route name, stops, and date.
6. If the logged-in passenger is watching a live trip (their preferred route), show the current `current_occupancy` and `remaining_seats` for that vehicle.

**Branch:** `master`
**Commit:** `feat: simulated passenger boardings with per-stop occupancy records`

- [ ] Task 12.2 complete

---

### Task 12.3 — Passenger Journey Statistics Dashboard

**Files:** `backend/app/routers/passengers.py`, `backend/app/services/passenger_service.py`, `frontend/src/app/components/pages/PassengerApp.tsx`

**Description:**
Give logged-in passengers a personal statistics view that summarises their travel history derived from boarding records and arrival data. This fulfils the "passenger information" scope requirement and makes the passenger dashboard meaningfully useful.

Fix steps:
1. Add `GET /passengers/me/stats` returning:
   - `total_trips` — number of trips the passenger was recorded on.
   - `routes_used` — list of distinct routes with trip count per route (top 5).
   - `favourite_stop` — the stop they boarded at most often.
   - `on_time_rate` — percentage of recorded trips where the vehicle's actual departure was within 5 minutes of scheduled.
   - `avg_wait_minutes` — average difference between scheduled and actual arrival at their most-used stops.
   - `this_week_trips` and `last_week_trips` — trip counts for comparison.
2. In `PassengerApp.tsx`, add a **My Stats** panel:
   - Summary cards: Total Trips, On-Time Rate, Favourite Route, Average Wait.
   - A small bar chart showing trips per week over the last 4 weeks (reuse existing chart components).
   - A "Routes Used" list showing the top 5 routes with trip count badges.
3. If the passenger has fewer than 3 recorded trips, show an empty-state card: "Your travel statistics will appear here once you've taken a few trips."
4. Update `PassengerProfile.total_trips_recorded` whenever a new boarding record is created for that passenger.

**Branch:** `master`
**Commit:** `feat: passenger journey statistics dashboard`

- [ ] Task 12.3 complete

---

## Phase 13 — Passenger Capacity & Bus Occupancy Tracking

---

### Task 13.1 — Vehicle Capacity Model and Simulated Occupancy Fields

**Files:** `backend/app/models/vehicle.py`, `backend/alembic/versions/` _(new migration)_, `backend/app/schemas/vehicles.py`, `backend/app/routers/vehicles.py`, `backend/app/services/vehicle_service.py`, `frontend/src/app/components/pages/fleet-management/AddVehicleDialog.tsx`

**Description:**
Each vehicle has a fixed seating capacity. During a trip, `current_occupancy` is maintained by the simulation runner (Task 12.2) as it generates boarding and alighting events at each stop. Add the fields to the model, expose them in the API, and make `seating_capacity` configurable per vehicle in the fleet management UI.

Fix steps:
1. Add to `Vehicle` model:
   - `seating_capacity: int` (default 45, configurable).
   - `current_occupancy: int` (default 0, updated at runtime by simulation).
2. Create Alembic migration.
3. Expose `seating_capacity` and `current_occupancy` in vehicle read schemas and `GET /vehicles` responses.
4. Add a computed field `remaining_seats = seating_capacity - current_occupancy` to the vehicle schema (derived, not stored in DB).
5. On trip completion in `trip_service.complete_trip`, reset `vehicle.current_occupancy = 0` (all simulated passengers have alighted at end of route).
6. In `vehicle_service.update_vehicle`, prevent manual writes to `current_occupancy` — it is owned by the simulation and boarding service only.
7. Expose `seating_capacity` as an editable integer field in `AddVehicleDialog.tsx` (for new vehicles) and the fleet edit dialog (for existing vehicles).

**Branch:** `master`
**Commit:** `feat: add vehicle seating capacity and simulation-driven occupancy tracking`

- [ ] Task 13.1 complete

---

### Task 13.2 — Real-Time Occupancy via WebSocket and Tracking UI

**Files:** `backend/app/websocket/route_simulation.py`, `backend/app/services/simulation_runner.py`, `frontend/src/app/components/pages/VehicleTracking.tsx`, `frontend/src/app/components/pages/vehicle-tracking/VehicleListPanel.tsx`, `frontend/src/app/components/pages/vehicle-tracking/VehicleMapView.tsx`, `frontend/src/app/lib/ws-client.ts`

**Description:**
Broadcast occupancy changes over the existing WebSocket so the tracking map and vehicle list update in real time as the simulation runs. Dispatchers should see live seat availability without refreshing.

Fix steps:
1. When `boarding_service.record_stop_events` updates `current_occupancy`, emit a WebSocket event `vehicle_occupancy_updated` with `{ vehicle_id, current_occupancy, seating_capacity, remaining_seats }`.
2. In `ws-client.ts`, handle the `vehicle_occupancy_updated` event and merge it into the tracked vehicle object in the client-side store.
3. In `VehicleListPanel.tsx`, show an occupancy indicator on each active vehicle row:
   - A thin coloured bar (green → yellow → red as capacity fills, thresholds: <70% green, 70–90% yellow, >90% red).
   - Text: `{current_occupancy}/{seating_capacity} seats · {remaining_seats} remaining`.
4. In `VehicleMapView.tsx`, add occupancy to the selected-vehicle popup: `X / Y seats occupied · Z remaining`.
5. On the map marker, tint the marker amber when occupancy >80% and red when at or above `seating_capacity`.
6. If a vehicle has no active trip, hide the occupancy bar entirely and show "Not in service" in its place.

**Branch:** `master`
**Commit:** `feat: real-time occupancy broadcast and tracking UI seat availability`

- [ ] Task 13.2 complete

---

### Task 13.3 — Capacity Alerts and Passenger-Facing Seat Availability

**Files:** `backend/app/services/alert_service.py`, `backend/app/services/boarding_service.py`, `backend/app/routers/alerts.py`, `backend/app/routers/vehicles.py`, `frontend/src/app/components/pages/Alerts.tsx`, `frontend/src/app/components/pages/PassengerApp.tsx`

**Description:**
Generate automatic alerts when a vehicle reaches or exceeds its seating capacity. These appear in the existing alerts system and are broadcast to dispatchers in real time. Passengers on the passenger app see a live seat availability badge for approaching buses on their preferred routes.

Fix steps:
1. In `boarding_service.record_stop_events`, after updating `current_occupancy`:
   - If `current_occupancy == seating_capacity`: call `alert_service.create_alert` with `severity = "warning"`, `type = "capacity"`, title `"Bus Full: {vehicle.plate}"`, and message naming the vehicle, route, and current stop.
   - If `current_occupancy > seating_capacity`: same call with `severity = "critical"`, title `"Excess Passengers: {vehicle.plate}"`.
2. Ensure `alert_service` broadcasts capacity alerts over the `new_alert` WebSocket event (consistent with existing alert infrastructure).
3. Add `type = "capacity"` to the alert type enum/field if not already present; create Alembic migration if the enum is in the database.
4. In the Alerts UI (`Alerts.tsx`), add a **Capacity** filter tab alongside existing type tabs so dispatchers can isolate capacity events.
5. Add `GET /vehicles/{vehicle_id}/occupancy` returning:
   ```json
   {
     "vehicle_id": "...",
     "seating_capacity": 45,
     "current_occupancy": 38,
     "remaining_seats": 7,
     "status": "nearly_full"
   }
   ```
   Status thresholds: `remaining_seats >= 10` → `"available"`; `1–9` → `"nearly_full"`; `0` → `"full"`.
6. In `PassengerApp.tsx`, for each vehicle on a passenger's preferred routes that has an active trip, call `GET /vehicles/{vehicle_id}/occupancy` and display a badge:
   - Green: "Seats available (X remaining)"
   - Yellow: "Nearly full (X remaining)"
   - Red: "Bus is full — wait for next bus"

**Branch:** `master`
**Commit:** `feat: capacity alerts for full buses with passenger-facing seat availability`

- [ ] Task 13.3 complete

---

## Implementation Summary

| Phase | Tasks | Status |
|---|---|---|
| Phase 10 — Advanced Reporting & Filtered Analytics | 3 tasks | 0 / 3 |
| Phase 11 — Authentication, Invitation & Registration Overhaul | 3 tasks | 0 / 3 |
| Phase 12 — Passenger Profile, Simulated Boardings & Journey Statistics | 3 tasks | 0 / 3 |
| Phase 13 — Passenger Capacity & Occupancy Tracking | 3 tasks | 0 / 3 |
| **Total** | **12 tasks** | **0 / 12** |

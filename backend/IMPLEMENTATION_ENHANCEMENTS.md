# Frontend Bug Fixes & Feature Enhancements

> **How to use this document:**
> - Work through tasks **strictly in order** — each phase depends on the previous.
> - After completing a task, tick its checkbox: `[ ]` → `[x]`
> - Keep the **Current Task Pointer** below updated after each completed task.
> - **DO NOT proceed to the next task without explicit user approval.**
> - Use the `master` branch for all tasks and use commit messages exactly as provided.

---

## Current Task Pointer

**Next task:** Task 9.3 — Interactive Global Header: Notifications, Date/Weather, and Search Strategy

---

> [!IMPORTANT]
> **Agent Rule:** After completing each task, stop and report:
> 1. What was implemented
> 2. Any decisions made or problems encountered
> 3. A commit message for what was implemented
> 4. Then ask: _"Ready to proceed to the next task?"_
> Do not move forward until the user confirms.

---

## Phase 1 — Route Management Fixes

---

### Task 1.1 — Fix Route Stops Edit Bug (Duplicate Stops on Save)

**Files:** `frontend/src/app/components/pages/route-management/EditRouteModal.tsx`, `frontend/src/app/components/pages/route-management/RouteForm.tsx`

**Description:**
When saving an edited route, stops are duplicated instead of replaced. Root cause: the `RouteUpdate` payload sent to the API always includes a `stops` array (even existing ones), and the backend `update_route` service deletes all old stops and re-creates them from the payload — but the `EditRouteModal` initialises `form.stops` using `stop.id` as the `key`, which means the existing stop IDs leak into the payload as new stops on every save. Additionally, the `useEffect` in `RouteForm` that auto-calculates distance has `form.distance` and `form.duration` in its dependency array, creating a potential re-render loop that can re-trigger saves.

Fix steps:
1. In `EditRouteModal`, when building the initial form state, generate a **fresh** `crypto.randomUUID()` key for each stop instead of using `stop.id` as the key — the key is only for React reconciliation and must not carry over the DB ID.
2. In `RouteForm`'s `useEffect`, remove `form.distance` and `form.duration` from the dependency array (use `eslint-disable` comment if needed) to break the loop — only `form.stops` should trigger the recalculation.
3. Verify that clicking **Save Changes** on an unmodified route results in the same number of stops being returned, not doubled.

**Branch:** `master`
**Commit:** `fix: stop duplication bug in route edit modal`

- [x] Task 1.1 complete

---

### Task 1.2 — Global Stops Registry (Stops Are Permanent & Shared Across Routes)

**Files:** `backend/app/models/route.py`, `backend/app/services/route_service.py`, `backend/app/routers/routes.py`, `backend/app/schemas/route.py`, `frontend/src/app/services/routes.service.ts`, `frontend/src/app/lib/api-types.ts`, `frontend/src/app/components/pages/route-management/RouteStopsEditor.tsx`, `frontend/src/app/components/pages/route-management/route-helpers.ts`

**Description:**
Currently stops are created as children of a route and are deleted and re-created on every route update. The requirement is that stops are **global/permanent entities** — they exist independently, multiple routes can share the same stop, and no two stops may share the same name or the same coordinates.

Backend changes:
1. Add a new `GET /api/v1/stops` endpoint that returns all stops for the current tenant (id, name, lat, lng).
2. Add a `POST /api/v1/stops` endpoint that creates a new global stop, enforcing uniqueness by name **and** by coordinates (within ~10 m). Return `409 CONFLICT` with a meaningful error code if either constraint is violated.
3. Modify `create_route` and `update_route` in `route_service.py` so that the `stops` array in the payload carries **stop IDs** (not inline name/lat/lng) and the service only creates/updates `RouteStop` join-table rows — it never creates or deletes the `Stop` entity itself during a route save.

Frontend changes:
1. Add `listStops()` and `createStop()` to `routes.service.ts`.
2. Update `StopCreate` in `api-types.ts` to carry `{ stopId: string; order: number }` for route payloads.
3. Rewrite `RouteStopsEditor` so that:
   - It loads the global stops list on mount.
   - Users pick existing stops from a searchable dropdown/combobox to add them to the route.
   - A **"Create new stop"** inline form (name, lat, lng) allows creating a permanent stop which is then immediately added to the route.
   - Map markers display **all global stops** (greyed out) and **route stops** (highlighted), so operators can see what exists when building a route.
   - Attempting to create a stop with an already-used name or coordinates shows an inline error from the API.

**Branch:** `master`
**Commit:** `feat: global stops registry — permanent stops shared across routes`

- [x] Task 1.2 complete

---

### Task 1.3 — Deactivating a Route Hides It from Passenger & Arrival Views

**Files:** `frontend/src/app/components/pages/PassengerApp.tsx`, `frontend/src/app/components/pages/arrival-times/useArrivalTimes.ts`, `frontend/src/app/services/routes.service.ts`

**Description:**
When a route is deactivated (`isActive = false`), it should not appear in the Passenger App stop list or in the Arrivals screen. Currently both views call `listRoutes({ isActive: true })` but there is no backend filter wired to `isActive` in the query param on the `GET /api/v1/routes` call.

Fix steps:
1. Verify that the backend `GET /api/v1/routes?isActive=true` actually filters correctly (check `route_service.get_routes` — it already has the `is_active` filter but confirm the router passes it through).
2. In `PassengerApp.tsx`, confirm `listRoutes({ isActive: true })` is passed so deactivated routes and their stops are excluded.
3. In `useArrivalTimes.ts`, add `isActive: true` to the `listRoutes` call so that stops derived from inactive routes are excluded from the Arrivals stop list.
4. Also filter `RoutesTable` (admin view) to visually dim/disable inactive routes rather than hiding them — admins should still see them.

**Branch:** `master`
**Commit:** `fix: inactive routes hidden from passenger and arrivals screens`

- [x] Task 1.3 complete

---

## Phase 2 — Passenger App Fixes

---

### Task 2.1 — Persist Favourite Stops Across Page Reloads

**Files:** `frontend/src/app/components/pages/PassengerApp.tsx`

**Description:**
Favourite stops are stored only in React component state (`useState<string[]>([])`), so they are lost on every page reload. Fix by persisting them to `localStorage`.

Fix steps:
1. Replace `useState<string[]>([])` with a custom initialiser that reads from `localStorage.getItem('passenger-favourite-stops')` and parses the JSON (default to `[]` on parse failure or missing key).
2. Add a `useEffect` that calls `localStorage.setItem('passenger-favourite-stops', JSON.stringify(favoriteStops))` whenever `favoriteStops` changes.
3. Ensure the stop IDs stored are stable (they come from the DB, so they are), and that if a stop is later deleted from the DB the UI handles the missing stop gracefully (the `allStops.filter(s => favoriteStops.includes(s.id))` already handles this implicitly).

**Branch:** `master`
**Commit:** `fix: persist passenger favourite stops in localStorage`

- [x] Task 2.1 complete

---

## Phase 3 — Arrivals Screen Enhancement

---

### Task 3.1 — "All Stops" Option in Arrivals Stop Selector

**Files:** `frontend/src/app/components/pages/arrival-times/ArrivalStopSelector.tsx`, `frontend/src/app/components/pages/arrival-times/useArrivalTimes.ts`, `frontend/src/app/services/arrivals.service.ts`, `frontend/src/app/components/pages/arrival-times/ArrivalEstimateList.tsx`

**Description:**
The arrivals dropdown only allows selecting one stop at a time. An **"All Stops"** option should display arrivals aggregated across every stop.

Fix steps:
1. Add a sentinel value (e.g., `'__all__'`) as the first `<SelectItem>` in `ArrivalStopSelector`, labelled **"All Stops"**.
2. In `useArrivalTimes.ts`, when `selectedStopId === '__all__'`, fetch arrivals for every stop in parallel (`Promise.all`) and merge + de-duplicate the results by `vehicleId`.
3. Update `ArrivalEstimateList` to display the stop name alongside each arrival row when "All Stops" is selected, so the operator knows which stop each vehicle is heading to.
4. Set the initial `selectedStopId` to `'__all__'` so the screen is useful immediately without requiring the operator to pick a stop.
5. Update the `selectedStop` memo so it returns a synthetic `{ name: 'All Stops', ... }` object when the sentinel is active (to avoid `null` UI states).

**Branch:** `master`
**Commit:** `feat: all-stops option in arrivals screen`

- [x] Task 3.1 complete

---

## Phase 4 — Maintenance Screen Fix

---

### Task 4.1 — Single Context-Aware Action Button in Maintenance Table

**Files:** `frontend/src/app/components/pages/maintenance/MaintenanceTable.tsx`

**Description:**
The maintenance records table shows both **Start** and **Complete** buttons for `scheduled` records, meaning two buttons are visible at once when only one action makes sense at a time.

The required behaviour:
| Status | Button shown |
|---|---|
| `scheduled` | **Start** (transitions to `in-progress`) |
| `in-progress` | **Complete** (transitions to `completed`) |
| `completed` | _(no button)_ |

Fix steps:
1. In `MaintenanceTableRow`, replace the current two separate conditionals with a single block:
   ```tsx
   {record.status === 'scheduled' && (
     <Button size="sm" variant="outline" disabled={disabled}
       onClick={() => onUpdateStatus(record, 'in-progress')}>
       Start
     </Button>
   )}
   {record.status === 'in-progress' && (
     <Button size="sm" disabled={disabled}
       onClick={() => onUpdateStatus(record, 'completed')}>
       Complete
     </Button>
   )}
   ```
2. Confirm that `completed` records show no action button.

**Branch:** `master`
**Commit:** `fix: show single context-aware action button in maintenance table`

- [x] Task 4.1 complete

---

## Phase 5 — Analytics Formatting Fixes

---

### Task 5.1 — Fix Fractional Fuel & Revenue Display

**Files:** `frontend/src/app/components/pages/analytics/analytics-helpers.ts`, `frontend/src/app/components/pages/analytics/AnalyticsStatsCards.tsx`, `frontend/src/app/components/pages/analytics/TrendCharts.tsx`, `frontend/src/app/components/pages/analytics/analytics-pdf.ts`

**Description:**
Multiple formatting issues appear in the analytics screens:

1. **Fuel shows excessive decimals** — e.g. `959.1680555555564L`. `totalFuelConsumption` should always be displayed as a whole integer (`Math.round`).
2. **Revenue shows as fractions in the chart** — daily `revenue` in the bar chart tooltip/axis shows fractional RWF values. Revenue must always be a whole number (already an integer from the backend, but `recharts` auto-scales the axis). Add a `tickFormatter` to both YAxes that calls `Math.round`.
3. **Total Revenue stat card collapses small values to `0.0M`** — the current `formatRevenue` divides by 1,000,000 and always appends `M`. Replace with a tiered formatter:
   - `≥ 1,000,000` → `X.XM RWF`
   - `≥ 1,000` → `X,XXXK RWF`
   - `< 1,000` → `X,XXX RWF` (plain number)
4. **`formatPassengers` collapses small values** — same fix: show raw number if `< 1,000`, else `XK`.

Fix steps:
1. Rewrite `formatRevenue(value: number)` in `analytics-helpers.ts` with the tiered logic above.
2. Rewrite `formatPassengers(value: number)` similarly.
3. In `AnalyticsStatsCards.tsx`, wrap `summary.totalFuelConsumption` in `Math.round()` before rendering.
4. In `TrendCharts.tsx`, add `tickFormatter={(v) => Math.round(v).toLocaleString()}` to the revenue `YAxis` on the Revenue & Passengers chart.
5. Update `analytics-pdf.ts` `summaryBox` to use the same `formatRevenue` for consistency so the exported PDF also shows correct values.

**Branch:** `master`
**Commit:** `fix: analytics formatting — fuel integer, tiered revenue/passenger display`

- [x] Task 5.1 complete

---

## Phase 6 — Security & Audit

---

### Task 6.1 — Real Audit Log on Security Page

**Files:** `backend/app/routers/audit.py` _(new)_, `backend/app/services/audit_service.py`, `backend/app/schemas/audit.py` _(new)_, `backend/app/routers/__init__.py` (or `main.py`), `frontend/src/app/components/pages/Security.tsx`, `frontend/src/app/services/` _(new `audit.service.ts`)_

**Description:**
The Security & Audit page currently renders a hard-coded placeholder list of four fake events. The backend already has an `audit_service.log()` utility that writes `AuditLog` rows. Wire a real API endpoint and connect the frontend.

Backend changes:
1. Create `GET /api/v1/audit-logs` (admin only) that returns paginated `AuditLog` rows for the current tenant, ordered by `created_at DESC`. Accept optional query params: `page`, `page_size` (default 50), `action` filter, `resource_type` filter.
2. Create `app/schemas/audit.py` with `AuditLogRead` (id, userId, tenantId, resourceType, resourceId, action, metadata, createdAt).
3. Register the router in `main.py`.

Frontend changes:
1. Create `audit.service.ts` with `listAuditLogs(params?)` calling `GET /api/v1/audit-logs`.
2. Add `AuditLogRead` to `api-types.ts`.
3. Rewrite `Security.tsx`:
   - Load real audit logs on mount with a loading/error state.
   - Display them in the existing event list card with real `action`, `user email` (from `userId` resolved via users list or embedded in log), `createdAt` formatted as relative time (e.g. "5 minutes ago"), and a coloured badge for the action type (`create` = green, `update` = blue, `soft_delete` = red).
   - Replace the four stat-card placeholders with: **Total Audit Logs** (real count), **Last Login** (most recent `login` action timestamp), **Failed Logins** (count of any `login_failed` actions in last 24 h — log these in `auth_service`), **Data Modifications** (count of `create`/`update`/`soft_delete` today).

**Branch:** `master`
**Commit:** `feat: real audit log endpoint and Security page wired to live data`

- [x] Task 6.1 complete

---

## Phase 7 — Tenant Identity & Data Isolation

---

### Task 7.1 — Fix Seed Data: Remove Kigali Express, Ensure EcoFleet Only

**Files:** `backend/app/core/seed.py`

**Description:**
The seed script correctly creates an **EcoFleet Ltd** tenant with `@ecofleet.rw` users, but older seed runs may have left a **Kigali Express** tenant (or users with `@kigaliexpress.com` emails) in the database. The login page demo credentials still work for `@kigaliexpress.com` addresses if those rows exist.

Fix steps:
1. Search `seed.py` for any reference to `kigaliexpress` or `Kigali Express` and remove them (the grep earlier found none in seed — confirm there is no second tenant block).
2. Add a **cleanup block** at the top of the seeder that deletes any tenant whose `name` or `contact_email` contains `kigali` (case-insensitive) before inserting fresh data, so stale rows from a previous run are wiped.
3. Add a re-seed CLI command or document clearly: run `docker compose exec backend python -m app.core.seed --reset` to wipe and re-seed cleanly.
4. Update `LoginPage.tsx` demo credentials panel to show only `@ecofleet.rw` addresses (it already does — confirm and keep).
5. Verify after re-seeding that logging in with an `@kigaliexpress.com` address returns `401`.

**Branch:** `master`
**Commit:** `fix: remove stale kigali-express seed data, enforce ecofleet-only seed`

- [x] Task 7.1 complete

---

### Task 7.2 — Tenant-Aware Dashboard & Sidebar Branding

**Files:** `frontend/src/app/components/layout/Sidebar.tsx`, `frontend/src/app/components/pages/Dashboard.tsx`, `frontend/src/app/lib/auth-context.tsx`, `frontend/src/app/lib/api-types.ts`, `frontend/src/app/services/auth.service.ts`

**Description:**
After login the sidebar shows "Rwanda Transport" (hard-coded) and the dashboard shows no tenant name. Every logged-in user should see their own tenant's name instead of the generic platform name.

Fix steps:
1. Extend `AuthUserSummary` (backend `TokenResponse` + frontend `api-types.ts`) to include `tenantName: string | null`.
2. In `auth_service.login` (backend), populate `tenant_name` from the `Tenant.name` field when building the token response.
3. Update `userFromAuthSummary` and `userFromTokenPayload` in `auth-context.tsx` to carry `tenantName` onto the `User` object (add `tenantName?: string` to the `User` type in `types.ts`).
4. In `Sidebar.tsx`, replace the hard-coded `"Rwanda Transport"` heading with `user?.tenantName ?? 'Rwanda Transport'` and the sub-label `"Fleet Management"` with `user?.role.charAt(0).toUpperCase() + user?.role.slice(1)` (or keep as-is if appropriate).
5. In `Dashboard.tsx`, update the page title from the static `"Fleet Dashboard"` to `` `${user?.tenantName ?? ''} Fleet Dashboard` ``.
6. The `PassengerApp.tsx` header also hard-codes `"Rwanda Transport"` — replace with `user?.tenantName` if the user is logged in, or keep generic for public-facing use.

**Branch:** `master`
**Commit:** `feat: tenant name shown in sidebar and dashboard header after login`

- [x] Task 7.2 complete

---

### Task 7.3 — Tenant-Branded Analytics PDF Report

**Files:** `frontend/src/app/components/pages/analytics/analytics-pdf.ts`, `frontend/src/app/components/pages/Analytics.tsx`, `frontend/src/app/lib/auth-context.tsx`

**Description:**
The exported PDF report header always reads **"Smart Transport"** regardless of which tenant is logged in, and does not include tenant contact details. The report should be branded per-tenant.

The required PDF header layout (left side / right side split):
```
LEFT                               RIGHT
[Tenant Logo placeholder / name]   Analytics & Performance Report
[Tenant address if available]      Generated: DD/MM/YYYY
[Tenant contact email]             Period: YYYY-MM-DD — YYYY-MM-DD
```

Fix steps:
1. Add `tenantAddress?: string` and `tenantPhone?: string` to the `Tenant` model/schema (can be nullable — just add the fields even if unpopulated for now).
2. Expose `tenantName`, `tenantEmail` (the `contact_email`) from the `TokenResponse` so they are available in the auth context (piggyback on Task 7.2's `tenantName` addition).
3. Update `exportAnalyticsPDF` signature to accept `{ tenantName, tenantEmail }` and update the `pageHeader` function to render the two-column layout described above (use `doc.text` with `align: 'right'` for the right column).
4. Pass `tenantName` and `tenantEmail` from `Analytics.tsx` when calling `exportAnalyticsPDF`.
5. Update the PDF footer to read `"Page X of Y  •  {tenantName} Analytics Report"` instead of `"Smart Transport Analytics Report"`.
6. Update the saved filename to `{tenantName}-report-{from}-to-{to}.pdf` (slugified).

**Branch:** `master`
**Commit:** `feat: tenant-branded PDF analytics report with contact details`

- [x] Task 7.3 complete

---

## Phase 8 — Additional Bugs & Improvements

---

### Task 8.1 — Route Number & Distance Not Persisted on Edit

**Files:** `backend/app/services/route_service.py`, `backend/app/schemas/route.py`, `frontend/src/app/lib/api-types.ts`

**Description:**
`RouteUpdate` on the frontend includes `number`, `distance`, and `duration` fields, but the backend `update_route` service in `route_service.py` does **not** apply these fields — only `name`, `is_active`, `color`, and `stops` are handled. This means edits to the route number or distance are silently dropped.

Fix steps:
1. In `route_service.update_route`, add handlers for `"number"`, `"distance"`, and `"duration"` in the `update_data` block.
2. Before applying `number`, check for uniqueness within the tenant (same check as `create_route`) and raise `409` if another route already uses that number.
3. Confirm `RouteUpdate` schema in `backend/app/schemas/route.py` includes `number`, `distance`, `duration` as optional fields (add them if absent).

**Branch:** `master`
**Commit:** `fix: persist route number, distance and duration on route update`

- [x] Task 8.1 complete

---

### Task 8.2 — Arrivals Screen Shows Stops from All Routes Including Inactive

**Files:** `frontend/src/app/components/pages/arrival-times/useArrivalTimes.ts`

**Description:**
`collectStops` in `useArrivalTimes` calls `listRoutes({ pageSize: 100 })` without `isActive: true`, so stops from deactivated routes appear in the arrivals dropdown. This is the arrivals-specific part of Issue 4 and is tracked here separately from the passenger app fix.

Fix: Add `isActive: true` to the `listRoutes` call in `loadStops` in `useArrivalTimes.ts`.

**Branch:** `master`
**Commit:** `fix: arrivals screen excludes stops from inactive routes`

- [x] Task 8.2 complete

---

### Task 8.3 — Map Marker Drag Calls `updateStop` Twice (Double State Update)

**Files:** `frontend/src/app/components/pages/route-management/RouteStopsEditor.tsx`

**Description:**
In `handleMarkerDragEnd`, when the user confirms the drag, `updateStop` is called **twice** — once for `lat` and once for `lng`. Each call dispatches a separate `setForm` using the updater function pattern, but because both reads from `current` happen before the first state flush, the second call may overwrite the first's change. This can result in only the longitude or only the latitude being updated.

Fix: Merge both updates into a single `setForm` call:
```tsx
setForm(current => ({
  ...current,
  stops: current.stops.map(stop =>
    stop.key === key
      ? { ...stop, lat: Number(position.lat.toFixed(6)), lng: Number(position.lng.toFixed(6)) }
      : stop
  ),
}));
```

**Branch:** `master`
**Commit:** `fix: merge lat/lng updates into single setForm call on marker drag`

- [x] Task 8.3 complete

---

### Task 8.4 — Dashboard Revenue Display Is Raw Unformatted Number

**Files:** `frontend/src/app/components/pages/Dashboard.tsx`

**Description:**
The Dashboard stat card for Total Passengers shows:
```
{(analyticsSummary?.totalRevenue ?? 0).toLocaleString()} RWF revenue
```
This outputs raw numbers like `959168.05 RWF revenue`. It should use the same tiered `formatRevenue` helper from `analytics-helpers.ts` (fixed in Task 5.1) so it reads e.g. `959K RWF revenue`.

Fix: Import `formatRevenue` from `analytics-helpers.ts` and apply it to `analyticsSummary.totalRevenue` in `Dashboard.tsx`.

**Branch:** `master`
**Commit:** `fix: format dashboard revenue using tiered formatRevenue helper`

- [x] Task 8.4 complete

---

### Task 8.5 — Passenger App Shows Wrong Branding & Hard-coded Service Info

**Files:** `frontend/src/app/components/pages/PassengerApp.tsx`

**Description:**
The passenger app header hard-codes `"Rwanda Transport"` and `"Passenger Information"` regardless of which tenant is logged in. The Service Information card also hard-codes Kigali-specific copy (`"Kigali City - All major districts"`, `"200 RWF | Distance-based pricing"`).

Fix steps:
1. Read tenant name from auth context (`useAuth`) and display it in the header — fall back to `"Transport System"` if unauthenticated (public use).
2. Retrieve tenant contact info from the auth context (added in Task 7.2) and show tenant phone/email in a footer or info card instead of the hard-coded Kigali text.
3. Keep the operating hours card as-is (reasonable generic default), but remove the hard-coded coverage area and fare strings, or make them configurable via tenant settings in a future task.

**Branch:** `master`
**Commit:** `fix: passenger app uses tenant branding from auth context`

- [x] Task 8.5 complete

---

### Task 8.6 — Route Cards Grid Also Shows Inactive Routes

**Files:** `frontend/src/app/components/pages/route-management/RouteCardsGrid.tsx`

**Description:**
`RouteCardsGrid` renders all routes fetched by `useRouteManagement`, which calls `listRoutes({ pageSize: 100 })` without an `isActive` filter — so both active and inactive routes are shown in the cards grid.

**Clarification needed before implementing:** Should the admin Routes screen show inactive routes (with a dimmed/greyed card), or completely hide them? The `RoutesTable` should show both for management purposes, but the cards grid is more visual. Assumed approach: show inactive routes with a reduced opacity and a clear "Inactive" overlay badge.

Fix: In `RouteCardsGrid`, apply `opacity-50` and a `"Inactive"` overlay `Badge` to cards where `route.isActive === false`.

**Branch:** `master`
**Commit:** `fix: route cards grid dims inactive routes with inactive badge`

- [x] Task 8.6 complete

---

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

- [ ] Task 9.3 complete

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

- [ ] Task 9.4 complete

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

- [ ] Task 9.5 complete

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

- [ ] Task 9.6 complete

---

## Implementation Summary

| Phase | Tasks | Status |
|---|---|---|
| Phase 1 — Route Management Fixes | 3 tasks | 3 / 3 |
| Phase 2 — Passenger App Fixes | 1 task | 1 / 1 |
| Phase 3 — Arrivals Screen Enhancement | 1 task | 1 / 1 |
| Phase 4 — Maintenance Screen Fix | 1 task | 1 / 1 |
| Phase 5 — Analytics Formatting Fixes | 1 task | 1 / 1 |
| Phase 6 — Security & Audit | 1 task | 1 / 1 |
| Phase 7 — Tenant Identity & Data Isolation | 3 tasks | 3 / 3 |
| Phase 8 — Additional Bugs & Improvements | 6 tasks | 6 / 6 |
| Phase 9 — Branding, Tracking UX, Header Interactions & Dispatch Clarity | 6 tasks | 1 / 6 |
| **Total** | **23 tasks** | **18 / 23** |

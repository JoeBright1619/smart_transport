# Frontend Bug Fixes & Feature Enhancements

> **How to use this document:**
> - Work through tasks **strictly in order** — each phase depends on the previous.
> - After completing a task, tick its checkbox: `[ ]` → `[x]`
> - Keep the **Current Task Pointer** below updated after each completed task.
> - **DO NOT proceed to the next task without explicit user approval.**
> - Use the `master` branch for all tasks and use commit messages exactly as provided.

---

## Current Task Pointer

**Next task:** Task 8.5 — Passenger App Shows Wrong Branding & Hard-coded Service Info

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

- [ ] Task 8.5 complete

---

### Task 8.6 — Route Cards Grid Also Shows Inactive Routes

**Files:** `frontend/src/app/components/pages/route-management/RouteCardsGrid.tsx`

**Description:**
`RouteCardsGrid` renders all routes fetched by `useRouteManagement`, which calls `listRoutes({ pageSize: 100 })` without an `isActive` filter — so both active and inactive routes are shown in the cards grid.

**Clarification needed before implementing:** Should the admin Routes screen show inactive routes (with a dimmed/greyed card), or completely hide them? The `RoutesTable` should show both for management purposes, but the cards grid is more visual. Assumed approach: show inactive routes with a reduced opacity and a clear "Inactive" overlay badge.

Fix: In `RouteCardsGrid`, apply `opacity-50` and a `"Inactive"` overlay `Badge` to cards where `route.isActive === false`.

**Branch:** `master`
**Commit:** `fix: route cards grid dims inactive routes with inactive badge`

- [ ] Task 8.6 complete

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
| Phase 8 — Additional Bugs & Improvements | 6 tasks | 4 / 6 |
| **Total** | **17 tasks** | **15 / 17** |

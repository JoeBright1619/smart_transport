# Frontend Implementation Plan — Backend Integration

> **How to use this document:**
> - Work through tasks **strictly in order** — each phase depends on the previous.
> - After completing a task, tick its checkbox: `[ ]` → `[x]`
> - Keep the **Current Task Pointer** below updated after each completed task.
> - **DO NOT proceed to the next task without explicit user approval.**
> - Branches are optional for this solo workflow; work on the current branch unless you intentionally choose otherwise.
> - Commit messages are suggestions only. Prefer descriptive messages that summarize the actual completed change.

---

## Current Task Pointer

**Next task:** Task 4.1 — Dashboard Page (`pages/Dashboard.tsx`)

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

## Background — Why This Plan Exists

The frontend UI is **fully built** with routing, layouts, components, and mock data for all screens. The backend is **fully built** with a production-ready FastAPI multi-tenant API and WebSocket tracking. Currently **zero** frontend pages call the backend — all data comes from `src/app/lib/mock-data.ts` and a localStorage-based auth mock.

This plan connects the two systems in a logical order: foundation first, then auth, then one resource domain at a time, then real-time tracking, then new pages that only make sense after real data flows.

---

## Type Alignment Reference

Before starting any task, note these **naming differences** between the existing frontend types (`lib/types.ts`) and backend schemas:

| Frontend field | Backend field | File |
|---|---|---|
| `Route.active` | `is_active` | route.py |
| `Stop.location.{lat,lng}` | `lat`, `lng` (top-level) | route.py |
| `Alert.acknowledged` | `is_acknowledged` | alert.py |
| `Alert.timestamp` | `created_at` | alert.py |
| `User.fullName` | `full_name` | user.py |
| `Driver.licenseNumber` | `license_number` | driver.py |
| `Driver.totalTrips` | `total_trips` | driver.py |
| `Driver.certificationExpiry` | `certification_expiry` | driver.py |
| `Vehicle.currentLocation` | `current_location` (computed) | vehicle.py |
| `Vehicle.registrationNumber` | `registration_number` | vehicle.py |
| `Vehicle.engineStatus` | `engine_status` | vehicle.py |
| `Vehicle.lastUpdate` | `updated_at` (aliased `lastUpdate`) | vehicle.py |
| `MaintenanceRecord.scheduledDate` | `scheduled_date` | maintenance.py |
| `MaintenanceRecord.completedDate` | `completed_date` | maintenance.py |
| `MaintenanceRecord.nextDue` | `next_due` | maintenance.py |
| `Trip.vehicleId` | `vehicle_id` | trip.py |
| `Trip.routeId` | `route_id` | trip.py |
| `Trip.driverId` | `driver_id` | trip.py |
| `Trip.scheduledStart` | `scheduled_start` | trip.py |
| `Trip.scheduledEnd` | `scheduled_end` | trip.py |
| `Trip.actualStart` | `actual_start` | trip.py |
| `Trip.actualEnd` | `actual_end` | trip.py |

The backend returns **all responses** wrapped in `APIResponse<T> = { data: T, meta?: Meta, error?: ErrorDetail }`. Paginated responses have `{ data: T[], meta: { total, page, pageSize } }`.

The backend uses **snake_case** field names in JSON by default, but many schemas define `serialization_alias` or `alias` for camelCase. Trust the actual JSON response, not just the Python field name.

---

## Phase 1 — Foundation

---

### Task 1.1 — Environment & Package Setup

**Description:**
Create environment configuration and install the HTTP client library.

1. Create `frontend/.env.example`:
   ```
   VITE_API_BASE_URL=http://localhost:8000
   VITE_WS_URL=ws://localhost:8000
   ```
2. Create `frontend/.env.local` with the same values (for local development — add to `.gitignore` if not already there).
3. Install `axios` using the frontend's package manager. This project currently has a `package-lock.json`, so use `npm install axios`.
4. Verify the install by confirming `axios` appears in `package.json` dependencies.

**Suggested commit:** `Configure frontend API environment variables and install Axios`

- [x] Task 1.1 complete

---

### Task 1.2 — API TypeScript Types (`lib/api-types.ts`)

**Description:**
Create `src/app/lib/api-types.ts` with TypeScript types that **exactly match the backend JSON responses**. Do not modify the existing `lib/types.ts` yet — the pages still use it and it will be migrated incrementally. These new types live alongside it.

Define these types:

```typescript
// Response envelopes
export interface ApiMeta { total: number; page: number; pageSize: number; }
export interface ApiError { code: string; message: string; }
export interface ApiResponse<T> { data: T; meta?: ApiMeta; error?: ApiError; }
export type PaginatedResponse<T> = ApiResponse<T[]>;

// Auth
export interface AuthUserSummary {
  id: string; email: string | null; full_name: string | null;
  role: UserRole; tenant_id: string | null;
}
export interface AuthTenantSummary { id: string; name: string; is_active: boolean; }
export interface RegisterResponse { tenant: AuthTenantSummary; user: AuthUserSummary; access_token: string; }
export interface TokenResponse { access_token: string; user: AuthUserSummary; }
export interface RefreshTokenResponse { access_token: string; }

// Users
export type UserRole = 'superadmin' | 'admin' | 'operator' | 'dispatcher' | 'passenger';
export type TenantUserRole = 'admin' | 'operator' | 'dispatcher' | 'passenger';
export interface UserRead {
  id: string; tenant_id: string | null; full_name: string; email: string;
  role: UserRole; phone: string | null; is_deleted: boolean; created_at: string;
}
export interface UserCreate { full_name: string; email: string; role: TenantUserRole; phone?: string; password: string; }
export interface UserUpdate { full_name?: string; phone?: string; role?: TenantUserRole; }

// Vehicles
export type VehicleStatus = 'active' | 'idle' | 'maintenance' | 'offline';
export type EngineStatus = 'good' | 'warning' | 'critical';
export interface VehicleLocation { lat: number; lng: number; }
export interface VehicleRead {
  id: string; registration_number: string; model: string; capacity: number;
  status: VehicleStatus; speed: number | null; heading: number | null;
  fuel: number | null; engine_status: EngineStatus;
  current_location: VehicleLocation | null; route_id: string | null;
  driver_id: string | null; lastUpdate: string;
}
export interface VehicleCreate { registration_number: string; model: string; capacity: number; status?: VehicleStatus; }
export interface VehicleUpdate { status?: VehicleStatus; fuel?: number; route_id?: string | null; driver_id?: string | null; }

// Routes & Stops
export interface StopRead { id: string; name: string; lat: number; lng: number; order: number; }
export interface StopCreate { name: string; lat: number; lng: number; order: number; }
export interface RouteRead {
  id: string; name: string; number: string; distance: number; duration: number;
  color: string; is_active: boolean; created_at: string; stops: StopRead[];
}
export interface RouteCreate { name: string; number: string; distance: number; duration: number; color: string; stops: StopCreate[]; }
export interface RouteUpdate { name?: string; is_active?: boolean; color?: string; stops?: StopCreate[]; }

// Drivers
export type DriverStatus = 'available' | 'on-trip' | 'off-duty';
export interface DriverRead {
  id: string; name: string; license_number: string; phone: string;
  rating: number; total_trips: number; status: DriverStatus;
  vehicle_id: string | null; certification_expiry: string; created_at: string;
}
export interface DriverCreate { name: string; license_number: string; phone: string; certification_expiry: string; }
export interface DriverUpdate { name?: string; phone?: string; status?: DriverStatus; vehicle_id?: string | null; certification_expiry?: string; }

// Trips
export type TripStatus = 'scheduled' | 'active' | 'completed' | 'cancelled';
export interface TripRead {
  id: string; vehicle_id: string; route_id: string; driver_id: string;
  scheduled_start: string; actual_start: string | null;
  scheduled_end: string; actual_end: string | null;
  status: TripStatus; passengers: number; delay: number; created_at: string;
}
export interface TripCreate { vehicle_id: string; route_id: string; driver_id: string; scheduled_start: string; scheduled_end: string; }
export interface TripUpdate { status: TripStatus; }

// Alerts
export type AlertType = 'delay' | 'breakdown' | 'maintenance' | 'geofence' | 'speeding' | 'info';
export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical';
export interface AlertRead {
  id: string; type: AlertType; severity: AlertSeverity;
  title: string; message: string; vehicle_id: string | null;
  driver_id: string | null; is_acknowledged: boolean; created_at: string;
}

// Maintenance
export type MaintenanceType = 'routine' | 'repair' | 'inspection';
export type MaintenanceStatus = 'scheduled' | 'in-progress' | 'completed';
export interface MaintenanceRead {
  id: string; vehicle_id: string; type: MaintenanceType;
  description: string; scheduled_date: string; completed_date: string | null;
  cost: number; status: MaintenanceStatus; next_due: string | null;
  created_at: string;
}
export interface MaintenanceCreate { vehicle_id: string; type: MaintenanceType; description: string; scheduled_date: string; cost: number; }
export interface MaintenanceUpdate { status?: MaintenanceStatus; cost?: number; completed_date?: string; next_due?: string; }

// Analytics
export interface AnalyticsSummary {
  totalTrips: number; onTimePercentage: number; avgDelay: number;
  totalPassengers: number; totalRevenue: number; totalFuelConsumption: number;
}
export interface AnalyticsDaily {
  date: string; totalTrips: number; onTimePercentage: number;
  avgDelay: number; totalPassengers: number; fuelConsumption: number; revenue: number;
}
export interface AnalyticsData { summary: AnalyticsSummary; daily: AnalyticsDaily[]; }

// Arrivals
export interface ArrivalEstimate {
  vehicle_id: string; registration_number: string; route_id: string;
  distance_km: number; eta_minutes: number | null;
  status: 'approaching' | 'stopped';
}

// Superadmin
export interface TenantRead {
  id: string; name: string; contact_email: string; is_active: boolean;
  created_at: string; vehicle_count: number; user_count: number;
}
export interface TenantDetail extends TenantRead { active_vehicles: number; trips_last_30d: number; }
export interface SuperadminAnalytics {
  total_tenants: number; active_tenants: number; total_vehicles: number;
  total_trips: number; total_users: number;
}
export interface ImpersonateResponse { access_token: string; tenant_id: string; }

// WebSocket
export type WsVehiclePosition = {
  vehicleId: string; lat: number; lng: number; speed: number;
  heading: number; fuel: number; status: VehicleStatus; timestamp: string;
};
export type WsMessage = { type: 'vehicle_positions'; vehicles: WsVehiclePosition[] };
```

**Suggested commit:** `Define frontend API response types for backend integration`

- [x] Task 1.2 complete

---

### Task 1.3 — HTTP Client (`lib/api-client.ts`)

**Description:**
Create `src/app/lib/api-client.ts` — an axios instance that:
1. Reads `VITE_API_BASE_URL` from `import.meta.env` as the `baseURL`
2. Sets `withCredentials: true` so the browser sends the HttpOnly refresh token cookie
3. Attaches `Authorization: Bearer <token>` from `localStorage` on every request (request interceptor)
4. On `401` response: calls `POST /auth/refresh` once to get a new access token, stores it, retries the original request. If refresh also fails, clears the token from storage and redirects to `/login` (response interceptor).
5. Exports a typed `ApiError` class that wraps backend error envelopes `{ error: { code, message } }`

Token storage keys: `ACCESS_TOKEN_KEY = 'st-access-token'`

The file must export:
- `apiClient` — the configured axios instance
- `getStoredToken(): string | null`
- `setStoredToken(token: string): void`
- `clearStoredToken(): void`

**Suggested commit:** `Create Axios API client with JWT injection and refresh handling`

- [x] Task 1.3 complete

---

## Phase 2 — Auth Integration

---

### Task 2.1 — Auth Service (`services/auth.service.ts`)

**Description:**
Create `src/app/services/auth.service.ts` with four functions that call the backend auth endpoints:

```typescript
registerTenant(payload: {
  companyName: string; contactEmail: string;
  adminFullName: string; adminEmail: string;
  adminPhone?: string; password: string;
}): Promise<RegisterResponse>

login(email: string, password: string): Promise<TokenResponse>

refresh(): Promise<RefreshTokenResponse>

logout(): Promise<void>
```

- `registerTenant` → `POST /auth/register` — maps camelCase payload to snake_case body
- `login` → `POST /auth/login`
- `refresh` → `POST /auth/refresh` (cookie is sent automatically because `withCredentials: true`)
- `logout` → `POST /auth/logout`

All functions must use `apiClient` and unwrap `response.data.data` from the `APIResponse<T>` envelope.

**Suggested commit:** `Implement auth API service for tenant registration and sessions`

- [x] Task 2.1 complete

---

### Task 2.2 — Rewrite Auth Context (`lib/auth-context.tsx`)

**Description:**
Replace the localStorage-mock auth context with real JWT-based auth. Keep the same `AuthContextType` interface shape so no page component needs to change (login returns `boolean`, register returns `{ok: true} | {ok: false, reason: 'email_taken'}`).

Changes:
1. `login(email, password)` — calls `authService.login()`, stores the returned `access_token` via `setStoredToken()`, sets user state from `response.user`. Returns `true` on success, `false` on 401.
2. `register(payload)` — maps the payload to `registerTenant()` format (company fields come from the registration payload; adapt the `AuthContextType` register signature to accept `companyName` and `contactEmail` as well — see Task 2.3 for the UI change). Returns `{ok: true}` on success, `{ok: false, reason: 'email_taken'}` on 409.
3. `logout()` — calls `authService.logout()`, calls `clearStoredToken()`, clears user state.
4. On mount (useEffect), if a token exists in localStorage, decode it (use `atob` on the payload segment — no library needed) to restore the user object. Attempt a silent `refresh()` call to validate the session; on success store new token; on failure clear token and set user to null.
5. Remove all `mockUsers`, `readRegisteredUsers`, `writeRegisteredUsers` logic.
6. Remove the `transport-registered-users` and `transport-user` localStorage keys — use `st-access-token` instead.

**Suggested commit:** `Replace mock auth state with JWT-backed authentication context`

- [x] Task 2.2 complete

---

### Task 2.3 — Update Register Page (`pages/RegisterPage.tsx`)

**Description:**
The backend `POST /auth/register` requires: `company_name`, `contact_email`, `admin_full_name`, `admin_email`, `admin_phone?`, `password`. The current `RegisterPage` only collects a single user's info.

Update `RegisterPage.tsx` to:
1. Add a **Company** section with fields: `Company Name`, `Company Contact Email`
2. Rename the existing name/email/phone fields to **Admin Name**, **Admin Email**, **Admin Phone**
3. Call `register({ companyName, contactEmail, adminFullName, adminEmail, adminPhone, password })` from `useAuth()`
4. Update `AuthContextType.register` signature to include `companyName: string` and `contactEmail: string` (and update the context implementation from Task 2.2 accordingly)
5. On success, navigate to `/login` with a `toast.success('Company registered — please sign in')` message. Do **not** auto-login after register (the backend issues an access token, but the login page is the correct UX entry point for a multi-tenant system).

Remove the "Demo Accounts" hint from `RegisterPage` (keep it only on `LoginPage`).

**Suggested commit:** `Update registration flow for tenant and admin account creation`

- [x] Task 2.3 complete

---

## Phase 3 — API Services Layer

> Each service file lives in `src/app/services/`. All use `apiClient` and unwrap `response.data.data`. Paginated list endpoints return `{ items: T[], total: number, page: number, pageSize: number }`.

---

### Task 3.1 — Users Service (`services/users.service.ts`)

**Description:**
```typescript
listUsers(params?: { page?: number; pageSize?: number; role?: string }): Promise<{ items: UserRead[]; total: number }>
getUser(id: string): Promise<UserRead>
createUser(data: UserCreate): Promise<UserRead>
updateUser(id: string, data: UserUpdate): Promise<UserRead>
deleteUser(id: string): Promise<void>
```
Endpoints: `GET /api/v1/users`, `POST /api/v1/users`, `GET /api/v1/users/{id}`, `PATCH /api/v1/users/{id}`, `DELETE /api/v1/users/{id}`

**Suggested commit:** `Add users API service for tenant user CRUD operations`

- [x] Task 3.1 complete

---

### Task 3.2 — Vehicles Service (`services/vehicles.service.ts`)

**Description:**
```typescript
listVehicles(params?: { page?: number; pageSize?: number; status?: VehicleStatus; routeId?: string }): Promise<{ items: VehicleRead[]; total: number }>
getVehicle(id: string): Promise<VehicleRead>
createVehicle(data: VehicleCreate): Promise<VehicleRead>
updateVehicle(id: string, data: VehicleUpdate): Promise<VehicleRead>
deleteVehicle(id: string): Promise<void>
```
Endpoints: `GET /api/v1/vehicles`, `POST /api/v1/vehicles`, `GET /api/v1/vehicles/{id}`, `PATCH /api/v1/vehicles/{id}`, `DELETE /api/v1/vehicles/{id}`

**Suggested commit:** `Add vehicles API service for fleet CRUD and assignment updates`

- [x] Task 3.2 complete

---

### Task 3.3 — Routes Service (`services/routes.service.ts`)

**Description:**
```typescript
listRoutes(params?: { page?: number; pageSize?: number; isActive?: boolean }): Promise<{ items: RouteRead[]; total: number }>
getRoute(id: string): Promise<RouteRead>
createRoute(data: RouteCreate): Promise<RouteRead>
updateRoute(id: string, data: RouteUpdate): Promise<RouteRead>
deleteRoute(id: string): Promise<void>
```
Endpoints: `GET /api/v1/routes`, `POST /api/v1/routes`, `GET /api/v1/routes/{id}`, `PATCH /api/v1/routes/{id}`, `DELETE /api/v1/routes/{id}`

**Suggested commit:** `Add routes API service for route and stop management`

- [x] Task 3.3 complete

---

### Task 3.4 — Drivers Service (`services/drivers.service.ts`)

**Description:**
```typescript
listDrivers(params?: { page?: number; pageSize?: number; status?: DriverStatus }): Promise<{ items: DriverRead[]; total: number }>
getDriver(id: string): Promise<DriverRead>
createDriver(data: DriverCreate): Promise<DriverRead>
updateDriver(id: string, data: DriverUpdate): Promise<DriverRead>
deleteDriver(id: string): Promise<void>
```
Endpoints: `GET /api/v1/drivers`, `POST /api/v1/drivers`, `GET /api/v1/drivers/{id}`, `PATCH /api/v1/drivers/{id}`, `DELETE /api/v1/drivers/{id}`

**Suggested commit:** `Add drivers API service for driver records and status updates`

- [x] Task 3.4 complete

---

### Task 3.5 — Trips Service (`services/trips.service.ts`)

**Description:**
```typescript
listTrips(params?: { page?: number; pageSize?: number; status?: TripStatus; vehicleId?: string; driverId?: string; routeId?: string }): Promise<{ items: TripRead[]; total: number }>
getTrip(id: string): Promise<TripRead>
createTrip(data: TripCreate): Promise<TripRead>
updateTripStatus(id: string, status: TripStatus): Promise<TripRead>
```
Endpoints: `GET /api/v1/trips`, `POST /api/v1/trips`, `GET /api/v1/trips/{id}`, `PATCH /api/v1/trips/{id}`

**Suggested commit:** `Add trips API service for scheduling and status transitions`

- [x] Task 3.5 complete

---

### Task 3.6 — Alerts Service (`services/alerts.service.ts`)

**Description:**
```typescript
listAlerts(params?: { page?: number; pageSize?: number; severity?: AlertSeverity; type?: AlertType; isAcknowledged?: boolean }): Promise<{ items: AlertRead[]; total: number }>
acknowledgeAlert(id: string): Promise<AlertRead>
```
Endpoints: `GET /api/v1/alerts`, `POST /api/v1/alerts/{id}/acknowledge`

**Suggested commit:** `Add alerts API service for listing and acknowledging incidents`

- [x] Task 3.6 complete

---

### Task 3.7 — Maintenance Service (`services/maintenance.service.ts`)

**Description:**
```typescript
listMaintenance(params?: { page?: number; pageSize?: number; vehicleId?: string; status?: MaintenanceStatus }): Promise<{ items: MaintenanceRead[]; total: number }>
getMaintenance(id: string): Promise<MaintenanceRead>
createMaintenance(data: MaintenanceCreate): Promise<MaintenanceRead>
updateMaintenance(id: string, data: MaintenanceUpdate): Promise<MaintenanceRead>
```
Endpoints: `GET /api/v1/maintenance`, `POST /api/v1/maintenance`, `GET /api/v1/maintenance/{id}`, `PATCH /api/v1/maintenance/{id}`

**Suggested commit:** `Add maintenance API service for scheduling and record updates`

- [x] Task 3.7 complete

---

### Task 3.8 — Analytics Service (`services/analytics.service.ts`)

**Description:**
```typescript
getAnalytics(params?: { from?: string; to?: string }): Promise<AnalyticsData>
```
Endpoint: `GET /api/v1/analytics?from=YYYY-MM-DD&to=YYYY-MM-DD`

**Suggested commit:** `Add analytics API service for dashboard and reporting data`

- [x] Task 3.8 complete

---

### Task 3.9 — Arrivals Service (`services/arrivals.service.ts`)

**Description:**
```typescript
getArrivals(stopId: string): Promise<ArrivalEstimate[]>
```
Endpoint: `GET /api/v1/arrivals?stopId=<id>`

**Suggested commit:** `Add arrivals API service for stop ETA estimates`

- [x] Task 3.9 complete

---

### Task 3.10 — Superadmin Service (`services/superadmin.service.ts`)

**Description:**
```typescript
listTenants(params?: { page?: number; pageSize?: number; isActive?: boolean }): Promise<{ items: TenantRead[]; total: number }>
getTenant(id: string): Promise<TenantDetail>
updateTenant(id: string, data: { is_active: boolean }): Promise<TenantRead>
impersonateTenant(id: string): Promise<ImpersonateResponse>
getSuperadminAnalytics(): Promise<SuperadminAnalytics>
```
Endpoints from `superadmin` router: `GET /superadmin/tenants`, `GET /superadmin/tenants/{id}`, `PATCH /superadmin/tenants/{id}`, `POST /superadmin/tenants/{id}/impersonate`, `GET /superadmin/analytics`

**Suggested commit:** `Add superadmin API service for tenant management and analytics`

- [x] Task 3.10 complete

---

## Phase 4 — Page Integration

> For each page, replace mock data imports with real API calls. Use `useState` + `useEffect` for data fetching. Add loading spinners and empty-state messages. Keep all existing UI structure — do not redesign components.

---

### Task 4.1 — Dashboard Page (`pages/Dashboard.tsx`)

**Description:**
Replace mock data imports with:
1. `analyticsService.getAnalytics()` for KPI summary values (total trips, on-time %, passengers)
2. `alertsService.listAlerts({ pageSize: 5, isAcknowledged: false })` for the recent alerts section
3. `vehiclesService.listVehicles({ pageSize: 100 })` to compute fleet status counts (active/idle/maintenance/offline)
4. Show a skeleton/loading state while fetching, and an error message if any call fails.

Map backend field names (`totalTrips`, `onTimePercentage`, `avgDelay`, `totalPassengers`) to the existing display labels.

**Suggested commit:** `Connect dashboard KPIs, alerts, and fleet status to backend APIs`

- [ ] Task 4.1 complete

---

### Task 4.2 — Fleet Management Page (`pages/FleetManagement.tsx`)

**Description:**
1. On mount, call `vehiclesService.listVehicles()` and populate the fleet table.
2. Wire the **Add Vehicle** form to `vehiclesService.createVehicle()` — after success, refetch the list.
3. Wire vehicle status PATCH (e.g., status dropdowns, assign driver/route) to `vehiclesService.updateVehicle()`.
4. Wire the delete action to `vehiclesService.deleteVehicle()` — show a confirmation before calling.
5. Map backend `VehicleRead` to the display columns:
   - `registration_number`, `model`, `capacity`, `status`, `fuel`, `engine_status`
   - `current_location` → show `lat, lng` or `—` if null
   - `lastUpdate` → format as relative time

**Suggested commit:** `Connect fleet management vehicle table and actions to backend API`

- [ ] Task 4.2 complete

---

### Task 4.3 — Route Management Page (`pages/RouteManagement.tsx`)

**Description:**
1. On mount, call `routesService.listRoutes()` and populate the route list.
2. Wire the **Create Route** modal (`CreateRouteModal.tsx`) to `routesService.createRoute()`. The stops array must use `{ name, lat, lng, order }` shape.
3. Wire the edit action to `routesService.updateRoute()` (stop list is a full replacement).
4. Wire the delete action to `routesService.deleteRoute()` — show `409` conflict error in a toast.
5. Map `is_active` → the active/inactive badge. Map `stops` (array with `lat`/`lng` top-level) to the Leaflet stop markers.

**Suggested commit:** `Connect route management list, editor, and map data to backend API`

- [ ] Task 4.3 complete

---

### Task 4.4 — Drivers Page (`pages/Drivers.tsx`)

**Description:**
1. On mount, call `driversService.listDrivers()`.
2. Wire the **Add Driver** form to `driversService.createDriver()`.
3. Wire the status change action to `driversService.updateDriver()`.
4. Wire the delete action to `driversService.deleteDriver()` — surface `400 DRIVER_ON_TRIP` error in a toast.
5. Map backend fields: `license_number`, `total_trips`, `certification_expiry` → display labels.

**Suggested commit:** `Connect drivers page records and actions to backend API`

- [ ] Task 4.4 complete

---

### Task 4.5 — Dispatch Page (`pages/Dispatch.tsx`)

**Description:**
The Dispatch page manages trip scheduling and status transitions.

1. On mount, call `tripsService.listTrips()` — display scheduled and active trips.
2. Wire the **Schedule Trip** form to `tripsService.createTrip()`. Fields needed: `vehicle_id`, `route_id`, `driver_id`, `scheduled_start`, `scheduled_end`. Populate the vehicle/route/driver dropdowns from `vehiclesService.listVehicles()`, `routesService.listRoutes()`, and `driversService.listDrivers()` respectively.
3. Wire status transition buttons (Start Trip → `active`, Complete → `completed`, Cancel → `cancelled`) to `tripsService.updateTripStatus()`.
4. Show conflict errors (vehicle/driver already on trip) from the `422` response in a toast.

**Suggested commit:** `Connect dispatch scheduling and trip transitions to backend API`

- [ ] Task 4.5 complete

---

### Task 4.6 — Alerts Page (`pages/Alerts.tsx`)

**Description:**
1. On mount, call `alertsService.listAlerts()`.
2. Wire the **Acknowledge** button to `alertsService.acknowledgeAlert(id)` — update the item in local state immediately (optimistic update) then confirm with the response.
3. Wire severity/type/acknowledged filter controls to re-call `listAlerts()` with the filter params.
4. Map `is_acknowledged` → the acknowledged badge. Map `created_at` → the timestamp display.

**Suggested commit:** `Connect alerts filters and acknowledgements to backend API`

- [ ] Task 4.6 complete

---

### Task 4.7 — Maintenance Page (`pages/Maintenance.tsx`)

**Description:**
1. On mount, call `maintenanceService.listMaintenance()`.
2. Wire the **Schedule Maintenance** form to `maintenanceService.createMaintenance()`.
3. Wire the status update action (mark as in-progress, completed) to `maintenanceService.updateMaintenance()`.
4. Map `scheduled_date`, `completed_date`, `next_due` → date display columns.

**Suggested commit:** `Connect maintenance scheduling and status updates to backend API`

- [ ] Task 4.7 complete

---

### Task 4.8 — Analytics Page (`pages/Analytics.tsx`)

**Description:**
1. On mount, call `analyticsService.getAnalytics({ from, to })` where `from`/`to` default to the last 7 days.
2. Wire the date range picker to re-fetch when the range changes.
3. Map `AnalyticsSummary` fields to the KPI cards: `totalTrips`, `onTimePercentage`, `avgDelay`, `totalPassengers`, `totalRevenue`, `totalFuelConsumption`.
4. Map `AnalyticsDaily[]` to the existing Recharts chart data (the `daily` array replaces `mockAnalytics`).

**Suggested commit:** `Connect analytics date-range reports and charts to backend API`

- [ ] Task 4.8 complete

---

### Task 4.9 — Arrival Times Page (`pages/ArrivalTimes.tsx`)

**Description:**
1. On mount, call `routesService.listRoutes()` to populate the stop selector — collect all stops from all routes.
2. When a stop is selected, call `arrivalsService.getArrivals(stopId)`.
3. Map `ArrivalEstimate` fields: `registration_number`, `eta_minutes` (or `null` → "Stopped"), `distance_km`, `status`.
4. Sort arrivals by `eta_minutes` ascending (nulls last).
5. Refresh the arrivals list every 10 seconds while a stop is selected (use `setInterval` in `useEffect`).

**Suggested commit:** `Connect arrival time estimates to backend API with auto-refresh`

- [ ] Task 4.9 complete

---

## Phase 5 — Real-Time Vehicle Tracking

---

### Task 5.1 — WebSocket Client (`lib/ws-client.ts`)

**Description:**
Create `src/app/lib/ws-client.ts` with a `VehicleTrackingSocket` class:

```typescript
class VehicleTrackingSocket {
  constructor(
    onMessage: (msg: WsMessage) => void,
    onError?: (err: Event) => void,
    onClose?: () => void,
  ) {}

  connect(): void    // opens WS to VITE_WS_URL/ws/tracking?token=<access_token>
  disconnect(): void // closes the WS connection
  get isConnected(): boolean
}
```

- Reads `VITE_WS_URL` from `import.meta.env`
- Appends the access token from `getStoredToken()` as `?token=<value>`
- On `close` with code `4001` (invalid token): calls `clearStoredToken()` and navigates to `/login`
- Does not auto-reconnect — the caller is responsible for reconnect logic

**Suggested commit:** `Add authenticated WebSocket client for live vehicle tracking`

- [ ] Task 5.1 complete

---

### Task 5.2 — Update Vehicle Tracking Page (`pages/VehicleTracking.tsx`)

**Description:**
Replace the client-side GPS simulation with real WebSocket data:

1. On mount, create a `VehicleTrackingSocket` instance and call `.connect()`.
2. On `WsMessage` with `type: 'vehicle_positions'`: update local state with the `vehicles` array.
3. On disconnect, set a "Disconnected — reconnecting…" status badge and retry `connect()` after 5 seconds.
4. On unmount, call `.disconnect()`.
5. Remove the import of `useVehicleSimulation` from this page.
6. Map `WsVehiclePosition` to the Leaflet marker positions: `vehicleId`, `lat`, `lng`, `speed`, `heading`, `status`.
7. Keep the vehicle list sidebar — it should update in real time from WebSocket messages.

Also call `vehiclesService.listVehicles()` on mount to seed the initial vehicle list before the first WebSocket message arrives.

**Suggested commit:** `Replace simulated vehicle tracking with live WebSocket positions`

- [ ] Task 5.2 complete

---

### Task 5.3 — Remove Vehicle Simulation Hook

**Description:**
Delete `src/app/lib/use-vehicle-simulation.ts` — it is no longer used after Task 5.2. If any other page still imports it, replace the import with a static initial load from `vehiclesService.listVehicles()`.

**Suggested commit:** `Remove obsolete client-side GPS simulation hook`

- [ ] Task 5.3 complete

---

## Phase 6 — New Pages

---

### Task 6.1 — Administration Page: Users CRUD (`pages/Administration.tsx`)

**Description:**
The current `Administration.tsx` contains placeholder UI. Replace it with a real users management page:

1. On mount, call `usersService.listUsers()` — show a table with columns: `full_name`, `email`, `role`, `phone`, `created_at`, actions.
2. **Invite User** button → modal form with `full_name`, `email`, `role` (dropdown: admin/operator/dispatcher), `phone?`, `password` → calls `usersService.createUser()`.
3. **Edit** action → inline form or modal with `full_name`, `phone`, `role` → calls `usersService.updateUser()`.
4. **Remove** action → confirmation dialog → calls `usersService.deleteUser()`.
5. Guard the page: only `admin` and `superadmin` roles can see the Invite and Remove actions (use `useAuth()` to check `user.role`).

**Suggested commit:** `Implement administration user management with backend CRUD`

- [ ] Task 6.1 complete

---

### Task 6.2 — Superadmin Portal (new route + page)

**Description:**
Add a superadmin-only section of the app, visible only when `user.role === 'superadmin'`.

1. Create `src/app/components/pages/SuperadminPortal.tsx` with three tabs:
   - **Tenants** — table with `name`, `contact_email`, `is_active`, `vehicle_count`, `user_count`. Actions: **Suspend** / **Reactivate** (calls `superadminService.updateTenant()`) and **Impersonate** (calls `superadminService.impersonateTenant()` — stores the returned token via `setStoredToken()` and reloads the app).
   - **Analytics** — calls `superadminService.getSuperadminAnalytics()` — display `total_tenants`, `active_tenants`, `total_vehicles`, `total_trips`, `total_users` as KPI cards.
   - **Tenant Detail** — clicking a tenant row loads `superadminService.getTenant(id)` and shows full detail.

2. Add the route to `routes.tsx`:
   ```tsx
   { path: 'superadmin', Component: SuperadminPortal }
   ```
3. Add a **Superadmin** sidebar link in `MainLayout.tsx` visible only when `user?.role === 'superadmin'`.
4. Add a route guard that redirects non-superadmin users to `/` if they navigate to `/superadmin`.

**Suggested commit:** `Add superadmin portal for tenant management and platform analytics`

- [ ] Task 6.2 complete

---

## Phase 7 — Final Polish

---

### Task 7.1 — Remove Mock Data File

**Description:**
Once all pages have been connected to the API (Phases 4–6 complete), delete `src/app/lib/mock-data.ts`.

Before deleting:
1. Search for any remaining imports of `mock-data` across the codebase using grep.
2. For each remaining import, replace it with the appropriate API service call.
3. `LoginPage.tsx` still shows "Demo Accounts" with mock credentials — update those credentials to match the backend seed data from `docs/Seed-Plan.md` (the seeded demo admin email/password).
4. Delete `mock-data.ts`.

**Suggested commit:** `Remove mock data dependency and align demo credentials with seed data`

- [ ] Task 7.1 complete

---

### Task 7.2 — Global Error & Loading States

**Description:**
Add consistent UX polish across all integrated pages:

1. Create a reusable `LoadingSpinner` component in `src/app/components/ui/loading-spinner.tsx` — a centered spinner using an existing Lucide icon or CSS animation.
2. Create a reusable `ErrorMessage` component in `src/app/components/ui/error-message.tsx` — shows `error.message` with a Retry button that re-triggers the fetch.
3. Apply both components uniformly to every page from Phase 4 that has a `useEffect` data fetch.
4. Add a global "Session expired" toast: in the `api-client.ts` response interceptor, when a token refresh fails, show `toast.error('Session expired — please log in again')` before redirecting to `/login`.

**Suggested commit:** `Add reusable loading and error states with session expiry feedback`

- [ ] Task 7.2 complete

---

### Task 7.3 — TypeScript Type Cleanup

**Description:**
Now that all pages use `api-types.ts`, audit `lib/types.ts` for types that are no longer used anywhere:

1. Run the TypeScript compiler (`npm exec tsc --noEmit`) and fix all type errors.
2. For each type in `lib/types.ts`, check if it still has any imports. Remove unused types.
3. Types that are still used as local UI state (e.g., a component maps `VehicleRead` to a local `VehicleViewModel`) can be kept or inlined.
4. Ensure no page still imports from `mock-data.ts` (deleted in Task 7.1).
5. Fix any remaining `any` casts introduced during migration.

**Suggested commit:** `Clean up legacy frontend types and resolve TypeScript errors`

- [ ] Task 7.3 complete

---

## Implementation Summary

| Phase | Tasks | Status |
|---|---|---|
| Phase 1 — Foundation | 3 tasks | 3 / 3 |
| Phase 2 — Auth Integration | 3 tasks | 3 / 3 |
| Phase 3 — API Services Layer | 10 tasks | 10 / 10 |
| Phase 4 — Page Integration | 9 tasks | 0 / 9 |
| Phase 5 — Real-Time Tracking | 3 tasks | 0 / 3 |
| Phase 6 — New Pages | 2 tasks | 0 / 2 |
| Phase 7 — Final Polish | 3 tasks | 0 / 3 |
| **Total** | **33 tasks** | **16 / 33** |

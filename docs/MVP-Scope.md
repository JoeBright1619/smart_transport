# MVP Scope — Smart Public Transport Tracking & Fleet Management System

> **Version:** 1.0 (MVP)
> **Last updated:** 2026-04-08
> **Purpose:** Defines exactly what is built, what is deferred, and what "done" means for each feature.
> Any agent or developer working on the system must treat this document as the authority on scope.

---

## MVP Goal

Deliver a working, multi-tenant fleet management SaaS that allows a transport company to:
1. Track their vehicles in real time on a map
2. Manage their fleet, drivers, and routes
3. Dispatch trips
4. Receive automated alerts for critical events
5. View basic operational analytics

A company must be able to sign up, log in, and start using all five capabilities above without any manual intervention from us.

---

## What is IN Scope (MVP v1.0)

### ✅ Authentication & Tenancy
| Feature | Notes |
|---|---|
| Login / logout | JWT + HttpOnly refresh cookie |
| Register new tenant (company) | Creates tenant + first admin user in one step |
| 14-day free trial | Full `pro` access during trial, no billing required |
| Role-based access control | `superadmin`, `admin`, `operator`, `dispatcher`, `passenger` |
| Protected routes (frontend) | Role-checked route guards |
| Tenant data isolation | Every query filtered by `tenant_id` from JWT |
| Soft deletes on all records | `is_deleted` flag; no hard deletes |
| Audit logging | `audit_logs` table for mutations on critical entities |

---

### ✅ Vehicle Tracking (Core Feature)
| Feature | Notes |
|---|---|
| Live map showing all tenant vehicles | React-Leaflet, OpenStreetMap tiles |
| Vehicle markers coloured by status | `active`=green, `idle`=blue, `maintenance`=orange, `offline`=grey |
| Vehicle detail panel on marker click | Shows registration, speed, fuel, driver, route |
| Position updates every 5 seconds | WebSocket via Redis pub/sub — tenant-scoped channel |
| Vehicle status badges | `active`, `idle`, `maintenance`, `offline` |

**Out of MVP:** Geofence polygon drawing tool, historical playback of vehicle routes

---

### ✅ Fleet Management
| Feature | Notes |
|---|---|
| List all vehicles with filters | Filter by status, route |
| Add new vehicle | Enforces `vehicleLimit` per subscription tier |
| Edit vehicle details | Patch: model, capacity, registration, status |
| Soft-delete a vehicle | Sets `is_deleted = true`; audit logged |
| Vehicle count vs tier limit indicator | Shown in the UI when approaching the limit |

---

### ✅ Route Management
| Feature | Notes |
|---|---|
| List all routes | Filter by active/inactive |
| Add new route with stops | Stops ordered; linked to route via `route_stops` |
| Edit route details | Name, number, stops, colour |
| Activate / deactivate a route | Toggle `is_active` |
| Route overlay on tracking map | Polyline drawn in route colour |

**Out of MVP:** Route optimisation, auto stop suggestion, GTFS import

---

### ✅ Driver Management
| Feature | Notes |
|---|---|
| List all drivers | Filter by status (`available`, `on-trip`, `off-duty`) |
| Add new driver | Name, licence, phone, certification expiry |
| Edit driver details | All fields patchable |
| View driver's current assignment | Which vehicle and trip they are on |
| Certification expiry warnings | Alert generated when expiry < 30 days |

---

### ✅ Dispatch & Trip Management
| Feature | Notes |
|---|---|
| Create a scheduled trip | Assign vehicle + driver + route + scheduled time |
| View dispatch queue | Unassigned / scheduled trips list |
| Start / complete / cancel a trip | Status transitions: `scheduled → active → completed / cancelled` |
| View active trips on map | Active trips visible in vehicle tracking view |
| Delay tracking | `delay` field updated as trip progresses |

**Out of MVP:** Automated optimal driver/vehicle matching, recurring trip schedules

---

### ✅ Alerts
| Feature | Notes |
|---|---|
| Auto-generated alerts | Delay > 5 min, engine critical, maintenance due in 7 days, speeding > 80 km/h, driver available |
| Alert feed with severity filter | `low`, `medium`, `high`, `critical` |
| Acknowledge alert | Sets `is_acknowledged = true` |
| Duplicate suppression | No new alert if unacknowledged alert of same type + vehicle exists |
| Alert count badge in nav | Unacknowledged count shown on sidebar |

**Out of MVP:** SMS/email alert notifications, custom alert rules, webhook delivery

---

### ✅ Arrival Time Estimation
| Feature | Notes |
|---|---|
| ETA per stop for active vehicles | Calculated server-side on request — no ML |
| Calculation method | Haversine distance (vehicle location → next stop) ÷ current speed |
| `/arrivals` page | Stop selector → lists approaching vehicles with ETA in minutes |
| Edge cases handled | Vehicle stopped (speed = 0) → shows "Stopped"; vehicle not on route → excluded |
| Endpoint | `GET /api/v1/arrivals?stopId=<id>` — returns vehicles approaching that stop with ETA |

**Algorithm:**
```
distance_km  = haversine(vehicle.lat, vehicle.lng, stop.lat, stop.lng)
eta_minutes  = (distance_km / vehicle.speed_kmh) * 60
arrival_time = now + eta_minutes
```

> Accuracy is intentionally simple — it does not account for traffic or road geometry. This is clearly labelled as an estimate in the UI. ML-based ETA is deferred to v1.2.

---

### ✅ Maintenance
| Feature | Notes |
|---|---|
| Log a maintenance record | Type (routine/repair/inspection), cost, dates |
| View maintenance records per vehicle | Filter by status: scheduled / in-progress / completed |
| Mark maintenance as complete | Sets `completed_date`, triggers `next_due` calculation |
| Maintenance due alert | Auto-generated when `next_due` within 7 days |

> **Tier gate:** Maintenance module requires `pro` or `enterprise` tier. On `starter`, the page returns `403 FEATURE_NOT_AVAILABLE`.

---

### ✅ Analytics Dashboard
| Feature | Notes |
|---|---|
| 7-day on-time percentage trend | Line chart |
| Daily trip count | Bar chart |
| Average delay per day | Line chart |
| Total passengers per day | Area chart |
| Fleet status distribution | Pie/radial chart (active/idle/maintenance/offline) |
| Date range filter | `from` / `to` query params |

> **Tier gate:** Analytics module requires `pro` or `enterprise` tier.

---

### ✅ Administration
| Feature | Notes |
|---|---|
| List all users in tenant | Filter by role |
| Invite / create a new user | Creates user with temporary password |
| Change user role | `admin` can change `operator`, `dispatcher`, `passenger` roles only |
| Deactivate a user | Soft delete + revoke active sessions |

---

### ✅ Superadmin Portal
| Feature | Notes |
|---|---|
| List all tenants | Name, tier, is_active, vehicle count, created date |
| View tenant details | Users, vehicles, subscription status |
| Suspend / reactivate a tenant | Sets `is_active = false / true` |
| Manual tier override | Change tier without billing (for manual deals) |
| Impersonate tenant admin | Full audit log entry created on impersonation |

---

### ✅ Subscription Tiers (Soft-Enforced in MVP)
| Tier | Vehicle Limit | Feature Gates |
|---|---|---|
| `starter` | 20 | Tracking, Fleet, Routes, Drivers, Dispatch, Alerts |
| `pro` | 100 | + Analytics, Maintenance |
| `enterprise` | Unlimited | + API access (deferred), White-label (deferred) |

> **Billing integration is deferred.** In MVP, tiers are set manually by superadmin or default to `trialing` (14 days). Stripe/Flutterwave integration is post-MVP.

---

## What is OUT of Scope (Post-MVP)

| Feature | Target Version | Reason Deferred |
|---|---|---|
| Stripe / Flutterwave billing integration | v1.1 | Complex to implement + not needed to validate product |
| SMS / email alert notifications | v1.1 | Needs third-party API (Africa's Talking, SendGrid) |
| Passenger mobile app | v1.1 | Separate product with different UX requirements |
| Arrival time predictions (ML/ETA) | v1.2 | Simple physics-based ETA is in MVP; ML refinement deferred |
| Geofence drawing tool | v1.1 | Backend rule exists; UI tool deferred |
| Historical vehicle route playback | v1.2 | Needs position history table (not in MVP schema) |
| GTFS data import | v1.2 | Useful for onboarding but not blocking |
| API access for enterprise tenants | v1.1 | API keys + rate limiting system needed |
| White-label branding | v1.1 | Requires theme customisation per tenant |
| Route optimisation / AI dispatch | v2.0 | Requires significant ML investment |
| Recurring / automated trip schedules | v1.1 | Cron/task queue infrastructure needed |
| Driver scoring / performance reports | v1.1 | Needs aggregated historical trip data |
| PostGIS spatial geofence queries | v1.1 | Basic distance check used in MVP instead |
| Audit log viewer page (Security module) | v1.1 | Logs are written; UI viewer deferred |
| Multi-language / localisation | v2.0 | English only in MVP |

---

## MVP Definition of Done

The MVP is complete when all of the following are true:

### Backend
- [ ] All `IN Scope` endpoints are implemented, tested, and return the standard response envelope
- [ ] Every list endpoint filters by `tenant_id` from JWT (verified by `test_tenant_isolation.py`)
- [ ] `get_current_tenant` checks `isActive` on every protected request
- [ ] Subscription tier feature gates enforced for `analytics` and `maintenance` endpoints
- [ ] Vehicle limit enforced on vehicle creation
- [ ] WebSocket broadcasts to tenant-scoped Redis channels
- [ ] Audit logs written for mutations on Users, Vehicles, Routes, Tenants
- [ ] **≥80% test coverage** on `services/` and `routers/`
- [ ] All Alembic migrations reversible and applied cleanly on fresh DB
- [ ] Seed script creates: 1 superadmin, 1 demo tenant (pro tier), demo vehicles/routes/drivers

### Frontend
- [ ] All `IN Scope` module pages are implemented and consuming mock data (prototype) or real API
- [ ] Role-based route guards enforce access restrictions
- [ ] Vehicle tracking map renders live positions with correct status colours
- [ ] Alerts page shows feed with unacknowledged badge count in sidebar
- [ ] Analytics and Maintenance pages show `FEATURE_NOT_AVAILABLE` state for `starter` tier
- [ ] All tables support filtering and sorting
- [ ] Responsive at 1280px minimum viewport

### System
- [ ] Docker Compose runs the full stack (frontend, backend, PostgreSQL, Redis) in one command
- [ ] `Dev-Setup.md` accurately describes the full local setup process
- [ ] No secrets committed to the repository

---

## Modules Excluded from Prototype Frontend (Keep Mock Data Only)

The following frontend pages exist in the prototype but will **not** be connected to the real backend in the MVP — they remain on mock data for the academic submission and are wired up post-submission:

| Page | Reason |
|---|---|
| `/passenger` | Deferred product; prototype-only |
| `/security` | Audit log viewer deferred to v1.1 |

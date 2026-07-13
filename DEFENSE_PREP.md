# Smart Transport — Defense Prep (Start Here)

This is your exam study pack. Read this file first for the big picture, then dive into the two detailed guides:

- **[Backend guide](DEFENSE_PREP_BACKEND.md)** — FastAPI, DB, auth, services, simulation, ETA.
- **[Frontend guide](DEFENSE_PREP_FRONTEND.md)** — React, routing, auth, maps, charts, i18n.

---

## 0. ⚠️ Positioning — read this first (Ecofleet vs. multi-tenant)

This system was built **for EcoFleet Ltd** — that is the thesis deliverable, and all documented requirements are implemented for them. You *also* architected it as a **multi-tenant platform** (each operator's data isolated) so it can be commercialized as a SaaS to other operators after the thesis. **Lead with Ecofleet; present multi-tenancy as a deliberate architectural/commercialization decision — never hide it, never overstate it.**

- **Demo as `admin@ecofleet.rw`** (seeded, [seed.py:156](backend/app/core/seed.py#L156)). Then everything on screen is "Ecofleet's system" and the superadmin menu isn't even visible.
- **Say once, in your architecture section:** *"The core deliverable is Ecofleet's system; I additionally designed it multi-tenant so it can be offered as SaaS to other operators later."*
- **If asked about the superadmin:** *"Ecofleet is one tenant; the superadmin is the SaaS platform-operator role that onboards and oversees operator companies. It sits above Ecofleet and touches none of their daily operations."*
- **If told "this wasn't in scope":** *"Correct — the documented requirements target Ecofleet as a single operator and are fully delivered. Multi-tenancy is an architectural decision beyond that scope for commercialization; it adds no Ecofleet-facing feature and is a security strength — one operator can never see another's data (`tests/test_tenant_isolation.py`)."*
- **Don't log in as superadmin** unless explicitly asked; then show it briefly.

## 1. What the system is (say this in your opening)

> "This is EcoFleet's public-transport management system. EcoFleet manages its vehicles, routes, stops, drivers, trips, alerts and maintenance, sees live vehicle tracking on a map, and gets analytics with exportable PDF reports; passengers get their own app to track buses and see arrival times. The backend is **FastAPI + PostgreSQL + Redis**; the frontend is **React + Vite + TypeScript**; auth is **JWT with rotating refresh tokens**; the UI supports **English and Kinyarwanda**. Architecturally it is built **multi-tenant**, so the same platform can serve additional transport operators as a commercial SaaS."

---

## 2. The five user roles

`superadmin > admin > operator > dispatcher > passenger`

**The four Ecofleet-facing roles (this is your thesis story):**
- **admin** — EcoFleet's owner/administrator; full control + user management.
- **operator** — manages fleet/routes/drivers/maintenance.
- **dispatcher** — schedules and runs trips.
- **passenger** — tracks buses and views arrivals.

**Platform role (commercialization layer, above Ecofleet):**
- **superadmin** — the SaaS platform-operator; onboards/oversees operator companies (tenants), impersonates for support, sees platform-wide analytics. *Not part of Ecofleet's day-to-day; present only if asked.*

---

## 3. Full-stack request flow (memorize one example)

**"A user views their fleet":**
```
Sidebar link /fleet
  → routes.tsx renders FleetManagement.tsx
    → useFleetManagement.ts calls vehicles.service.ts
      → api-client.ts attaches JWT, GET /api/v1/vehicles
        → main.py routes to routers/vehicles.py
          → require_role + get_current_tenant (dependencies.py)
            → vehicle_service.py queries WHERE tenant_id = <this tenant>
              → returns {data:[...], meta:{...}} envelope
            → hook stores it, page renders the table
```

If the JWT is expired, the backend returns 401, and `api-client.ts` silently refreshes via the HttpOnly cookie and retries — all invisible to the user.

---

## 4. The signature features to demo (all as Ecofleet)

1. **Real-time tracking** — the backend **simulates** buses moving along routes (standing in for GPS hardware), streams positions over a **WebSocket** (`/ws/tracking`) fanned out via **Redis pub/sub**, and the frontend renders them live on a **Leaflet** map.
2. **Analytics + branded PDF reports** — Redis-cached KPIs, **Recharts** graphs, and **jsPDF** reports carrying EcoFleet's own logo/name, localized to English or Kinyarwanda.
3. **Automated operations** — driver/vehicle status, ETAs, alerts (delay/breakdown/speeding/low-fuel/capacity), boardings and revenue are all **derived from operational data**, replacing manual radio check-ins and logbooks.

**Architectural strength (explain, don't demo):** **multi-tenant data isolation** — every query is scoped by `tenant_id` from the JWT, and `tests/test_tenant_isolation.py` proves one operator can never see another's data. This is what makes the post-thesis SaaS commercialization safe.

---

## 5. Cross-cutting questions that span both sides

| Question | Short answer |
|---|---|
| "How does auth work end to end?" | Login returns a 15-min JWT (localStorage) + a 7-day HttpOnly refresh cookie. Frontend attaches the JWT to every request; on 401 it refreshes via the cookie and retries. Backend rotates the refresh token each time. |
| "How do you enforce security?" | Backend: `require_role` + `get_current_tenant` on every endpoint, bcrypt passwords, hashed/rotated refresh tokens, audit logging. Frontend: route guards + role-filtered menu (defense-in-depth — the backend is the real gate). |
| "How do you support two languages?" | Frontend i18next with 16 namespaces per language; backend returns error **codes** that the frontend maps to localized messages; reports are generated in the chosen language. |
| "How would this scale to real GPS?" | Replace the simulation engine (`app/websocket/route_simulation.py`) with a real telemetry ingest endpoint writing to the `telemetry` table; everything downstream (WebSocket broadcast, ETA, tracking UI) stays the same. |
| "Why these technologies?" | FastAPI = async + auto OpenAPI docs; Postgres = relational integrity for multi-tenant data; Redis = pub/sub for real-time scaling + caching; React/Vite = fast SPA; Leaflet = free OSM maps. |

---

## 6. How to run it (for a live demo)

- **Everything via Docker:** `docker compose up` (starts Postgres, Redis, backend).
- **Seed the EcoFleet demo data:** `docker compose exec backend python -m app.core.seed` (add `--reset` to wipe and reseed clean).
- **Frontend:** `cd frontend && npm run dev`.
- **Backend API docs (fallback demo surface):** `http://localhost:8000/docs`.
- **Backend tests:** `docker compose exec backend pytest`.

**Seeded logins** (password `Password123!`, except superadmin):

| Role | Email | Password |
|---|---|---|
| Admin (EcoFleet) | `admin@ecofleet.rw` | `Password123!` |
| Operator | `operator@ecofleet.rw` | `Password123!` |
| Dispatcher | `dispatcher@ecofleet.rw` | `Password123!` |
| Passenger | `passenger@ecofleet.rw` | `Password123!` |
| Superadmin (only if asked) | `superadmin@platform.local` | `Admin@123456` |

**Seed state to know** (so nothing surprises you): 3 buses are **already moving** on the map at startup — `veh-001` (Route 101 Nyabugogo–Kimironko), `veh-003` (Route 202 CBD–Gisozi), `veh-007` (Route 404). One trip is **scheduled** (`veh-006`, Route 303). **Idle & available** to dispatch: `veh-002`, `veh-005`, `veh-008`. **`veh-004` is in maintenance** (engine critical) — great for the maintenance/alerts story.

---

## 7. Full demo walkthrough (rehearse this end to end)

Run it top to bottom. Each step is **Do → Say → ✅ Verify**. The ✅ boxes double as your "is everything working?" test. Unless noted, stay logged in as **`admin@ecofleet.rw`** so the whole thing reads as EcoFleet's own system.

### Pre-flight
- [ ] `docker compose up` is running; `docker compose ps` shows db, redis, backend healthy.
- [ ] Seed data loaded (`... python -m app.core.seed`).
- [ ] `npm run dev` up; open the printed URL; set the app language to **English** to start.

### Act 1 — Login & Dashboard
- **Do:** Log in as `admin@ecofleet.rw`.
- **Say:** *"This is EcoFleet's management system. The dashboard gives the operator a live overview — fleet status, active trips, alerts, KPIs."*
- **✅ Verify:** Redirected to the dashboard; the **EcoFleet name/logo** shows in the sidebar/header; KPI cards and any charts render with numbers (not spinners/errors).

### Act 2 — Fleet Management (`/fleet`)
- **Do:** Open Fleet. Point out the 8 vehicles and their statuses (idle / active / maintenance). Click **Add Vehicle**, create one (e.g. reg `RAD 010 X`, capacity 50), save.
- **Say:** *"Operators manage the whole fleet here — capacity, fuel, engine status, current occupancy. Notice `RAD 004 D` is in maintenance with a critical engine."*
- **✅ Verify:** New vehicle appears in the table; a success toast shows; refresh keeps it (persisted).

### Act 3 — Routes & Stops (`/routes`)
- **Do:** Open Routes. Show Route 101 (Nyabugogo–Kimironko) and its **ordered stops**. Open the stops editor to show the stop sequence.
- **Say:** *"Each route is an ordered list of stops. That ordering is what powers ETA calculation and the map polyline."*
- **✅ Verify:** Routes list loads; opening a route shows its stops in order.

### Act 4 — Drivers (`/drivers`)
- **Do:** Open Drivers. Show statuses (available / on-trip / off-duty). Point out that on-trip drivers are the ones tied to the moving buses.
- **Say:** *"Driver status is derived automatically from the trip lifecycle — nobody types it in. An assigned, running driver shows on-trip; when the trip ends they return to available."*
- **✅ Verify:** Drivers list loads; at least one shows **on-trip** (matching the 3 active buses).

### Act 5 — Dispatch a trip (`/dispatch`) — *the automation centerpiece*
- **Do:** Open Dispatch. Show the **active trips** (3) and **scheduled** (1). Click **Schedule Trip**, pick an idle vehicle (`veh-002`), an available driver, and a route → save (toast **"Trip scheduled"**). Then **Start** that trip (status → active; toast **"Trip status updated"**).
- **Say:** *"The dispatcher schedules and runs trips. Starting a trip flips the vehicle to active and the driver to on-trip, and reserves both so they can't be double-booked."*
- **✅ Verify:** New trip appears as scheduled, then moves to active; the chosen vehicle/driver disappear from the "available" lists.

### Act 6 — Live Tracking (`/tracking`) — *the real-time centerpiece*
- **Do:** Open Tracking. Watch buses **move** on the Leaflet map. Click a vehicle marker to open its popup (occupancy, speed, fuel, engine, next stop). Find the bus you just dispatched.
- **Say:** *"Positions stream over a WebSocket, fanned out via Redis so it scales across servers. In production this is where real GPS feeds in; here a simulation stands in for the hardware."*
- **✅ Verify:** Markers move every few seconds; the popup shows live occupancy/speed; the **connection badge shows connected** (not "disconnected"); your newly dispatched bus appears and starts moving within ~10s.

### Act 7 — Arrival Times / ETAs (`/arrivals`)
- **Do:** Select a stop on an active route (e.g. a stop on Route 101). Show the estimated arrivals.
- **Say:** *"ETA is computed by walking the ordered stops from the bus's current position, summing the real (haversine) distances, and dividing by live speed."*
- **✅ Verify:** Picking a stop returns one or more ETAs with a bus and minutes.

### Act 8 — Alerts (`/alerts`)
- **Do:** Open Alerts. Show auto-generated alerts (e.g. low-fuel, maintenance/critical engine, delay/speeding). Acknowledge one.
- **Say:** *"Alerts are generated automatically from operational data — breakdowns from engine status, delays from schedule, low fuel from telemetry — no human has to report them."*
- **✅ Verify:** Alerts list loads; acknowledging one updates its state (and the toast/counter).

### Act 9 — Maintenance (`/maintenance`)
- **Do:** Open Maintenance. Show records; click **Schedule Maintenance** for `veh-004`, save.
- **Say:** *"Operators track routine service, repairs and inspections; a vehicle in maintenance is automatically excluded from dispatch."*
- **✅ Verify:** New maintenance record appears; toast confirms.

### Act 10 — Analytics + PDF export (`/analytics`)
- **Do:** Open Analytics. Show the trend charts (revenue, passengers, fuel), route/fleet tabs. Change the date range. Click **Export PDF**.
- **Say:** *"KPIs are cached in Redis for speed. Reports export as branded PDFs carrying EcoFleet's logo and name, in the selected language."*
- **✅ Verify:** Charts render; date-range change updates them; the PDF downloads and shows **EcoFleet branding** + real numbers.

### Act 11 — Bilingual UI (i18n)
- **Do:** In the header, switch language **English → Kinyarwanda**. Navigate a page or two.
- **Say:** *"The whole UI is internationalized — English and Kinyarwanda — including dates, numbers, and the PDF reports."*
- **✅ Verify:** Labels switch to Kinyarwanda immediately; refresh keeps the choice (persisted). **Switch back to English** before continuing.

### Act 12 — Administration & Security
- **Do:** Open Administration (`/admin`) → show users; **Invite** a new staff user (enter an email, pick a role) → send. Open Security (`/security`) → show the **audit log** (your recent actions — login, trip create, invite).
- **Say:** *"Admins manage their team via email invitations, and every sensitive action is written to an immutable audit log."*
- **✅ Verify:** Invite succeeds (toast); the invited user appears as invited; the audit log shows your recent actions.

### Act 13 — Passenger app (log out → `passenger@ecofleet.rw`)
- **Do:** Log out, log in as the passenger. Show **live tracking**, **arrival times** for a favourite stop, **trip history**, **notifications** (approaching bus), and **profile / operators** directory.
- **Say:** *"Passengers get their own focused app — track buses, see ETAs, get notified when their bus is near, and view their trip history."*
- **✅ Verify:** Passenger home loads; tracking/arrivals show data; notifications page loads; profile is editable.

### Act 14 — Superadmin (ONLY if asked; see §0)
- **Do:** Log in as `superadmin@platform.local`. Show the tenants list, platform analytics.
- **Say:** *"This is the commercialization layer — the SaaS platform-operator that onboards and oversees operator companies. EcoFleet is one tenant. Each tenant's data is fully isolated, proven by our tenant-isolation test."*
- **✅ Verify:** Superadmin portal loads tenants + platform metrics.

### Fallback if the UI misbehaves
Open `http://localhost:8000/docs` and demo the same flows via the API (login → get token → call `/api/v1/vehicles`, `/api/v1/trips`, etc.). Good insurance to mention you have.

---

## 8. Two-minute pre-exam checklist

- [ ] I can name the 5 roles and the role hierarchy.
- [ ] I can explain the access/refresh token split and *why* (§ auth).
- [ ] I can point to `get_current_tenant` as the multi-tenancy gate.
- [ ] I can trace one feature from Sidebar click to DB query and back.
- [ ] I can explain the bus simulation + WebSocket + Redis pub/sub chain.
- [ ] I can explain how an ETA is computed (haversine over ordered stops ÷ speed).
- [ ] I can show the i18n setup and switch languages live.
- [ ] I know where migrations live and how to run tests.

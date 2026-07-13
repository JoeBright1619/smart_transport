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

- **Everything via Docker:** `docker-compose up` (starts Postgres, Redis, backend).
- **Backend alone:** `cd backend && uvicorn main:app --reload` → API docs at `http://localhost:8000/docs`.
- **Frontend:** `cd frontend && npm run dev`.
- **Backend tests:** `cd backend && pytest`.

---

## 7. Two-minute pre-exam checklist

- [ ] I can name the 5 roles and the role hierarchy.
- [ ] I can explain the access/refresh token split and *why* (§ auth).
- [ ] I can point to `get_current_tenant` as the multi-tenancy gate.
- [ ] I can trace one feature from Sidebar click to DB query and back.
- [ ] I can explain the bus simulation + WebSocket + Redis pub/sub chain.
- [ ] I can explain how an ETA is computed (haversine over ordered stops ÷ speed).
- [ ] I can show the i18n setup and switch languages live.
- [ ] I know where migrations live and how to run tests.

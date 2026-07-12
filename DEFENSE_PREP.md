# Smart Transport — Defense Prep (Start Here)

This is your exam study pack. Read this file first for the big picture, then dive into the two detailed guides:

- **[Backend guide](DEFENSE_PREP_BACKEND.md)** — FastAPI, DB, auth, services, simulation, ETA.
- **[Frontend guide](DEFENSE_PREP_FRONTEND.md)** — React, routing, auth, maps, charts, i18n.

---

## 1. What the system is (say this in your opening)

> "Smart Transport is a **multi-tenant** public-transport management platform. One deployment serves many transport companies; each company manages its vehicles, routes, stops, drivers, trips, alerts and maintenance, sees live vehicle tracking on a map, and gets analytics with exportable PDF reports. Passengers get their own app to track buses and see arrival times. A superadmin oversees all companies. The backend is **FastAPI + PostgreSQL + Redis**; the frontend is **React + Vite + TypeScript**; auth is **JWT with rotating refresh tokens**; and the UI supports **English and Kinyarwanda**."

---

## 2. The five user roles

`superadmin > admin > operator > dispatcher > passenger`

- **superadmin** — platform owner; manages all tenants, impersonates, sees platform-wide analytics.
- **admin** — a company's owner; full control of their tenant + user management.
- **operator** — manages fleet/routes/drivers/maintenance.
- **dispatcher** — schedules and runs trips.
- **passenger** — tracks buses and views arrivals.

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

## 4. The three "signature" features to be ready to demo

1. **Multi-tenancy + isolation** — every query is scoped by `tenant_id` from the JWT; `tests/test_tenant_isolation.py` proves company A can't see company B's data.
2. **Real-time tracking** — the backend **simulates** buses moving along routes (no real GPS), streams positions over a **WebSocket** (`/ws/tracking`) fanned out via **Redis pub/sub**, and the frontend renders them live on a **Leaflet** map.
3. **Analytics + branded PDF reports** — Redis-cached KPIs, **Recharts** graphs, and **jsPDF** reports carrying the tenant's own logo/name, localized to English or Kinyarwanda.

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

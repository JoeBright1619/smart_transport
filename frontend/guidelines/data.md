# Frontend — Data, Charts & Maps

> Rules for displaying data, using mock data, simulation hooks, charts, and maps.

---

## Mock Data (Prototype Phase)

All dashboards and tables must populate from `lib/mock-data.ts` exports:

| Export | Use For |
|---|---|
| `mockVehicles` | Vehicle tables, fleet cards, map markers |
| `mockRoutes` | Route tables, route map overlays |
| `mockStops` | Stop lists, arrival time panels, map pins |
| `mockDrivers` | Driver lists, dispatch assignment panels |
| `mockTrips` | Active trip feeds, dispatch queue |
| `mockMaintenanceRecords` | Maintenance log tables |
| `mockAlerts` | Alert feed, alert badge counts |
| `mockAnalytics` | Charts on the analytics page |
| `mockUsers` | Admin user management table |

**Rules:**
- Do **not** create new mock data files or simulation modules
- Do **not** invent data structures not present in `lib/types.ts`
- All mock data uses **Kigali, Rwanda** coordinates and context — keep this consistent
- When the real backend is connected, replace mock imports with API calls — do not mix both

---

## Real-Time Simulation

- Use `lib/use-vehicle-simulation.ts` exclusively for simulating live vehicle movement
- Do **not** create new simulation hooks or timers
- The hook updates vehicle positions every **5 seconds** — match this interval if building WebSocket integration

---

## Charts (Recharts)

Use Recharts for all data visualization:

| Chart Type | Use For |
|---|---|
| `LineChart` | On-time % trend, delay trend over time, passenger demand over time |
| `BarChart` | Daily trip counts, fuel consumption comparison, revenue per day |
| `PieChart` / `RadialBar` | Fleet status distribution (active/idle/maintenance/offline) |
| `AreaChart` | Cumulative passenger counts |

**Rules:**
- Maximum **3 charts per page** — prefer KPI stat cards + one main chart
- Always include axis labels and a legend
- Use chart colors consistent with `theme.css` tokens — do not use raw hex codes inline
- Charts must use data from `mockAnalytics` or other mock exports — never hardcode chart data inline

---

## Maps (React-Leaflet)

Used on: Vehicle Tracking (`/tracking`), Route Management (`/routes`), Arrival Times (`/arrivals`).

- Tile provider: **OpenStreetMap** — no API key required
- Default map centre: Kigali, Rwanda — `lat: -1.9403, lng: 30.0618`
- Vehicle markers must reflect `vehicle.status` via color:
  - `active` → green
  - `idle` → blue
  - `maintenance` → orange
  - `offline` → grey
- Route overlays must use the `route.color` field for polyline color
- Do not use Google Maps or Mapbox — keep it open-source

---

## Tables

All operational data tables must:
- Support **sorting** on at least one column (e.g., status, name, date)
- Support **filtering** via a control panel above the table
- Use mock/simulated data from `lib/mock-data.ts`
- Show a **loading skeleton** state (even in prototype — use consistent placeholder rows)
- Show an **empty state** message when no data matches the filter

Standard transport tables: `VehicleTable`, `DriverList`, `RouteTable`, `MaintenanceLog`, `TripList`, `AlertFeed`

---

## Types

`lib/types.ts` is the frontend's canonical type source. It must stay in sync with `shared/guidelines/entities.md`. When an entity changes in the shared guidelines, update `lib/types.ts` in the same commit.

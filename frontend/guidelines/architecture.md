# Frontend — Architecture

> Component structure, routing, module map, and auth patterns.

---

## Project Structure

```
src/
├── main.tsx                        # App entry point — mounts RouterProvider
├── app/
│   ├── App.tsx                     # Root component
│   ├── routes.tsx                  # All routes (react-router v7 createBrowserRouter)
│   ├── components/
│   │   ├── pages/                  # One file per system module (full pages)
│   │   ├── ui/                     # Reusable primitives (shadcn/Radix-based)
│   │   ├── layout/                 # MainLayout, Sidebar, TopNavigationBar
│   │   ├── figma/                  # Auto-generated Figma exports — use sparingly
│   │   └── ProtectedRoute.tsx      # Route guard using auth context
│   └── lib/
│       ├── types.ts                # Canonical TypeScript interfaces (mirrors shared/entities.md)
│       ├── mock-data.ts            # Simulated Kigali transport data
│       ├── use-vehicle-simulation.ts  # Real-time vehicle movement hook
│       └── auth-context.tsx        # Auth state, role, token management
└── styles/
    └── theme.css                   # Global CSS variables, Tailwind @theme{} tokens
```

---

## Component Hierarchy

```
App (RouterProvider)
└── ProtectedRoute
    └── MainLayout
        ├── TopNavigationBar  (system title, user profile, notifications)
        ├── SidebarNavigation (links to all module pages)
        └── <Page>            (one of 13 module pages — see module map below)
            ├── PageHeader
            ├── FilterControlPanel
            ├── DataVisualization  (Recharts / Leaflet)
            └── DataTable / List
```

---

## Module Map (All Routes)

Do not rename, remove, or add routes without updating this table.

| Route | Component | Key UI Elements |
|---|---|---|
| `/` | `Dashboard` | KPI stat cards, fleet summary chart, alert feed |
| `/tracking` | `VehicleTracking` | Live Leaflet map, vehicle detail panel |
| `/fleet` | `FleetManagement` | VehicleTable, status badges, add/edit forms |
| `/routes` | `RouteManagement` | RouteTable, stop list, route map overlay |
| `/arrivals` | `ArrivalTimes` | Stop selector, ETA list, delay indicators |
| `/passenger` | `PassengerApp` | Simplified route/stop view for passengers |
| `/dispatch` | `Dispatch` | Unassigned trips queue, driver assignment panel |
| `/drivers` | `Drivers` | DriverList, assignment status, certifications |
| `/maintenance` | `Maintenance` | MaintenanceLog, scheduled/in-progress/completed |
| `/analytics` | `Analytics` | Line/bar charts: on-time %, delays, revenue |
| `/alerts` | `Alerts` | Alert feed, severity filter, acknowledge action |
| `/admin` | `Administration` | User management, role assignment |
| `/security` | `Security` | Access control and audit log |
| `/login` | `LoginPage` | Public — no ProtectedRoute |
| `/register` | `RegisterPage` | Public — no ProtectedRoute |

---

## Auth & Protected Routes

- All routes except `/login` and `/register` must be wrapped in `<ProtectedRoute>`.
- `ProtectedRoute` reads from `auth-context.tsx` — redirects to `/login` if not authenticated.
- Roles: `superadmin | admin | operator | dispatcher | passenger` (defined in `lib/types.ts`).
- Administrative pages (`/admin`, `/security`) must check for `admin` or `superadmin` role and redirect otherwise.
- The `passenger` role must never see fleet management actions (dispatch, maintenance, admin).
- Use `auth-context.tsx` for reading auth state. Never store tokens in `localStorage` directly — context handles it.

---

## Code Rules

- React functional components with TypeScript strictly (`strict: true`). No class components.
- Files under 200 lines. Extract sub-components or helpers when approaching the limit.
- All new component files: `.tsx` extension. Utilities and hooks: `.ts` extension.
- Prefer importing existing `components/ui/` primitives over creating new ones.
- Only create a new component when functionality genuinely cannot be reused.
- Refactor repeated logic into helper functions in `lib/`.

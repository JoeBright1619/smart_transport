# Smart Transport — Frontend Defense Prep

> **Goal of this file:** Teach you the frontend well enough that in the defense you can (a) explain how the UI works, and (b) instantly open the right file when asked "show me where X is implemented."

**Stack:** React 18 + Vite 6 + TypeScript SPA · **React Router 7** · axios · Leaflet/react-leaflet (maps) · Recharts (charts) · jsPDF (PDF export) · i18next (English + Kinyarwanda) · Radix UI + Tailwind v4. **Global state = React Context only** (no Redux/Zustand).

> **Positioning (read [DEFENSE_PREP.md](DEFENSE_PREP.md) §0):** Demo as **`admin@ecofleet.rw`** — then the app reads entirely as EcoFleet's system and the superadmin nav item is hidden. `SuperadminPortal` / `SuperadminRoute` are the SaaS **commercialization layer**; show them only if explicitly asked.

**Root:** `frontend/` — source under `frontend/src/app/`.

---

## 1. The 30-second mental model

To trace **any** feature end-to-end, follow this chain:

```
routes.tsx                          (which URL → which page)
  → pages/<Feature>.tsx             (the page component / layout)
    → pages/<feature>/use<Feature>Management.ts   (the hook: state + data fetching)
      → services/<feature>.service.ts             (feature API calls)
        → lib/api-client.ts         (axios: base URL, auth header, refresh-on-401)
          → backend
```

**One-liner to memorize:** *"Route picks a page, the page's hook fetches through a service, the service uses one shared axios client that auto-attaches the token and auto-refreshes on 401."*

---

## 2. Directory map (`frontend/src/app/`)

| Folder | What it holds |
|---|---|
| `components/pages/` | One component per route, **plus a subfolder per feature** with its sub-components + hook + helpers |
| `components/layout/` | App shell: `Header.tsx`, `Sidebar.tsx`, `MainLayout.tsx`, `ProtectedLayout.tsx` |
| `components/ui/` | The reusable design system (~55 Radix-based components) |
| `components/` (root) | Route guards: `ProtectedRoute.tsx`, `SuperadminRoute.tsx`, `RoleHomeRedirect.tsx` |
| `services/` | One API module per backend feature |
| `lib/` | Cross-cutting infra: `api-client.ts`, `auth-context.tsx`, `ws-client.ts`, `i18n.ts`, `format.ts`, types |
| `locales/en/` & `locales/rw/` | Translation JSON (16 namespaces each) |

**Entry points:** `src/main.tsx` (bootstraps, initializes i18n) → `src/app/App.tsx` (wraps in `<AuthProvider>` + `<RouterProvider>`) → `src/app/routes.tsx` (route table).

> **Note for the panel:** No `hooks/`, `context/`, or `store/` folders — hooks are **colocated per feature**, the single context is `lib/auth-context.tsx`, routing is the single file `routes.tsx`.

---

## 3. Routing & access control (`src/app/routes.tsx`)

Built with `createBrowserRouter`. **Public** routes are top-level; **everything else** is nested under a guarded shell.

**Public:** `/login`, `/register` (passenger), `/register/company` (tenant + admin), `/accept-invite`.

**Protected shell** (`/` → `<ProtectedRoute><MainLayout/></ProtectedRoute>`):
`/` (role-based redirect), `/dashboard`, `/tracking`, `/fleet`, `/routes`, `/arrivals`, `/passenger`, `/dispatch`, `/drivers`, `/maintenance`, `/analytics`, `/alerts`, `/passenger-notifications`, `/admin`, `/security`, `/profile`, `/operators`, `/superadmin/:tab`.

**Three layers of access control (know all three):**
1. **`ProtectedRoute.tsx`** — shows "Restoring your session…" while auth initializes, then redirects to `/login` if not authenticated.
2. **`SuperadminRoute.tsx`** — redirects to `/` unless `user.role === 'superadmin'`.
3. **`Sidebar.tsx`** — the `navigation` array gives each menu item a `roles: [...]` list, filtered by the current user's role. **This is the clearest single reference for "which role sees which page."**

`RoleHomeRedirect.tsx` sends each role to its home: superadmin→`/superadmin`, passenger→`/passenger`, staff→dashboard.

---

## 4. Pages (`src/app/components/pages/`)

| Page | Feature |
|---|---|
| `LoginPage` / `RegisterPage` / `TenantRegisterPage` / `AcceptInvitePage` | Auth flows |
| `Dashboard` | Staff overview KPIs |
| `VehicleTracking` | Real-time Leaflet map + live vehicle list (WebSocket) |
| `FleetManagement` | Vehicles CRUD + utilization |
| `RouteManagement` | Routes + stops CRUD |
| `ArrivalTimes` | ETA estimates per stop |
| `PassengerApp` | Passenger tracking/trips/profile |
| `Dispatch` | Trip scheduling |
| `Drivers` | Drivers CRUD |
| `Maintenance` | Maintenance records |
| `Analytics` | Recharts charts + PDF export |
| `Alerts` | Alert management |
| `Administration` | Tenant admin: users/invites |
| `Security` | Security settings / audit logs |
| `ProfilePage` / `OperatorsPage` / `PassengerNotificationsPage` | Profile / operator directory / passenger alerts |
| `SuperadminPortal` | Cross-tenant portal (tabs via `:tab` param) |

**Per-feature folders** (e.g. `fleet-management/`, `analytics/`, `route-management/`) each contain the page's sub-components (dialogs, tables, stat cards), a `use<Feature>Management.ts` hook (state + fetching), and a `<feature>-helpers.ts` file (pure helpers). This is a deliberate **separation of concerns**: pages render, hooks manage state, helpers compute.

---

## 5. API layer & the axios client (`src/app/lib/api-client.ts`)

This one file is the answer to many questions:
- `apiClient = axios.create({ baseURL: VITE_API_BASE_URL, withCredentials: true })` — `withCredentials` is what sends the HttpOnly refresh cookie.
- **Request interceptor** — attaches `Authorization: Bearer <token>` from `localStorage` (`st-access-token`).
- **Response interceptor** — on **401** for a non-auth request that hasn't been retried: calls `refreshAccessToken()`, updates the header, and **retries the original request once**. If refresh fails: clears the token, toasts "Session expired", redirects to `/login`.
- A module-level `refreshPromise` **de-duplicates concurrent refreshes** (single-flight) — if 5 requests 401 at once, only one refresh call happens.
- Exports `ApiError` (unwraps the backend's `{error:{code,message}}` envelope) and token helpers.

**Per-feature services** in `services/` (`auth.service.ts`, `vehicles.service.ts`, `routes.service.ts`, `drivers.service.ts`, `trips.service.ts`, `alerts.service.ts`, `analytics.service.ts`, `arrivals.service.ts`, `passenger.service.ts`, `superadmin.service.ts`, etc.) — each imports `apiClient` and exposes typed functions per endpoint.

---

## 6. Authentication (frontend) — *the most-asked topic*

**`src/app/lib/auth-context.tsx`** — `AuthProvider` + `useAuth()`. Exposes `user`, `login`, `logout`, `register`, `isAuthenticated`, `isInitializing`.
- **Access token** → `localStorage['st-access-token']`. **Refresh token** → HttpOnly cookie (JS never touches it).
- On app mount, `bootstrapSession()` reads the stored JWT, **base64url-decodes the payload**, checks `exp`; if valid it hydrates `user` straight from the claims (no extra request); if expired it tries a silent refresh; else it clears state.
- The JWT claims include `role`, `tenantId`, and **tenant branding** (name, logo, address, phone) — that's how the tenant's logo/name appear in the UI and PDF reports **without an extra API call**.

**Error localization:** `lib/error-messages.ts` maps an `ApiError.code` to a translation key (`errors:<CODE>`), so backend errors show in the user's language.

---

## 7. State management

- **Global:** a single React Context (`AuthProvider`) — current user + auth actions. That's it.
- **Per-feature:** each feature's `use<Feature>Management.ts` hook owns its data (`useState`/`useEffect`/`useCallback`), form state, dialog flags, and calls services. Toasts via **sonner**.
- **Why no Redux?** The only truly global state is the logged-in user; everything else is page-local, so Context + colocated hooks is simpler and sufficient. (Good answer if they ask "why not Redux?")

---

## 8. Real-time tracking (WebSocket + Leaflet)

- **`lib/ws-client.ts`** — `VehicleTrackingSocket` class. Connects to `${VITE_WS_URL}/ws/tracking?token=<access token>` (JWT in the query string because browsers can't set WS headers). Normalizes `vehicle_update` / `vehicle_occupancy_updated` messages. On close code **4001** (auth failure) it clears the token and redirects to login.
- **`pages/VehicleTracking.tsx`** — loads vehicles/routes/drivers, opens the socket (kept in a `useRef`), merges live updates into state, **auto-reconnects after 5s** on disconnect, shows a "disconnected" badge.
- **`pages/vehicle-tracking/VehicleMapView.tsx`** — `react-leaflet` map centered on **Kigali `[-1.9536, 30.0606]`**, OpenStreetMap tiles, route `Polyline`s, stop `CircleMarker`s (highlighting at-stop/next-stop), and vehicle `Marker`s with popups (occupancy, speed, fuel, engine).
- Helpers (`vehicle-tracking-helpers.ts`): `createVehicleIcon`, `occupancyColor`, `MapController` (recenters on the selected vehicle).

---

## 9. Charts & PDF export (Analytics)

- **Charts (Recharts):** `pages/analytics/TrendCharts.tsx` (line/bar of daily performance, revenue, passengers), `RouteAnalytics.tsx`, `FleetAnalytics.tsx`, `AnalyticsChartsTabs.tsx`. Generic wrapper at `components/ui/chart.tsx`.
- **PDF export (jsPDF + jspdf-autotable):** `pages/analytics/analytics-pdf.ts` — builds a **branded tenant report** (tenant name/logo/address header, styled tables, brand colors). Text is localized via `i18n.t('report:...')` and dates via `lib/format.ts`.
- Orchestrated by `pages/analytics/useAnalyticsPage.ts`.

---

## 10. Internationalization (English + Kinyarwanda)

*This was a large chunk of recent work — expect questions.*
- **Setup:** `lib/i18n.ts` — i18next + react-i18next + browser-language-detector. Languages `en`, `rw`; `fallbackLng: 'en'`; default namespace `common`. Chosen language persisted in `localStorage['st-lang']`.
- **16 namespaces**, one JSON file per language in `locales/en/` and `locales/rw/`: `common`, `errors`, `passenger`, `fleet`, `dispatch`, `drivers`, `maintenance`, `analytics`, `admin`, `dashboard`, `tracking`, `alerts`, `routes`, `arrivals`, `security`, `report`.
- **Usage:** components call `useTranslation('<namespace>')` then `t('key')`; cross-namespace lookups use `t('fleet:vehicleStatus.active')`.
- **Language switcher:** `layout/Header.tsx` (`i18n.changeLanguage('en'|'rw')`).
- **Locale-aware formatting:** `lib/format.ts` maps the language to a BCP-47 tag (`en`→`en-GB`, `rw`→`rw-RW`) for `Intl` date/number formatting.

---

## 11. UI component library & layout shell

- **`components/ui/`** — ~55 components on **Radix UI + Tailwind v4** + `class-variance-authority`; the `cn()` merge helper is in `ui/utils.ts`. Includes `button`, `card`, `dialog`, `table`, `tabs`, `select`, `form` (react-hook-form), `chart`, `sonner` (toasts), plus project extras like `PasswordStrengthMeter.tsx`, `table-pagination.tsx`, `loading-spinner.tsx`.
- **Layout shell** (`components/layout/`): `MainLayout.tsx` (Sidebar + Header + `<Outlet/>`), `Sidebar.tsx` (role-filtered nav + tenant branding + logout), `Header.tsx` (language switcher, **notification bell that polls every 30s**, profile link, live clock).
- Icons: `lucide-react`.

---

## 12. Key config files

| File | Purpose |
|---|---|
| `vite.config.ts` | Vite + React + Tailwind plugins; path alias `@` → `./src`. |
| `package.json` | Scripts: `dev`, `build`, `preview`; confirms the whole dependency stack. |
| `.env.local` | `VITE_API_BASE_URL=http://localhost:8000`, `VITE_WS_URL=ws://localhost:8000`. |
| `main.tsx` / `App.tsx` | Bootstrap + provider tree. |

---

## 13. Likely exam questions → where to point

| Question | Answer / file |
|---|---|
| "How does the frontend log a user in?" | `pages/LoginPage.tsx` → `useAuth().login` (`lib/auth-context.tsx`) → `auth.service.ts`. |
| "Where is the JWT stored and why?" | Access token in `localStorage`; refresh token in an HttpOnly cookie (out of JS reach) — `auth-context.tsx` + `api-client.ts`. |
| "What happens when the token expires mid-use?" | 401 interceptor in `api-client.ts` silently refreshes and retries. |
| "How do you stop non-admins seeing admin pages?" | `ProtectedRoute` + `SuperadminRoute` + role-filtered `Sidebar.tsx`. |
| "How does the live map update?" | `ws-client.ts` WebSocket → merged in `VehicleTracking.tsx` → rendered in `VehicleMapView.tsx`. |
| "How do you support Kinyarwanda?" | i18next; `lib/i18n.ts` + `locales/rw/*.json`; switcher in `Header.tsx`. |
| "How is the PDF report generated?" | `pages/analytics/analytics-pdf.ts` with jsPDF, branded per tenant. |
| "Why no Redux?" | Only global state is the user (Context); rest is page-local hooks. |
| "How does the tenant's logo appear everywhere?" | It's a JWT claim, read in `auth-context.tsx`. |

---

### Fastest way to demo any frontend feature live
1. `cd frontend && npm run dev` → open the printed localhost URL.
2. Trace live in DevTools: **Network → Fetch/XHR** shows the service calls, **Network → WS** shows the live tracking socket frames, **Application → Local Storage** shows `st-access-token` and `st-lang`.

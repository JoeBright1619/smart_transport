# API Specification — Index

> **Base URL:** `/api/v1` (tenant-scoped) | `/superadmin` (platform-level)
> **Auth:** All endpoints except `/auth/*` require `Authorization: Bearer <access_token>`
> **Format:** All responses use the standard envelope — see `shared/guidelines/api-contracts.md`

---

## Files in This Directory

| File | Endpoints | Load When... |
|---|---|---|
| [auth.md](./auth.md) | `POST /auth/*` | Building login, register, token refresh |
| [users.md](./users.md) | `GET/POST/PATCH/DELETE /api/v1/users` | User management features |
| [vehicles.md](./vehicles.md) | `GET/POST/PATCH/DELETE /api/v1/vehicles` | Fleet management features |
| [routes.md](./routes.md) | `GET/POST/PATCH/DELETE /api/v1/routes` | Route management features |
| [drivers.md](./drivers.md) | `GET/POST/PATCH/DELETE /api/v1/drivers` | Driver management features |
| [trips.md](./trips.md) | `GET/POST/PATCH /api/v1/trips` | Dispatch and trip management |
| [operations.md](./operations.md) | `/api/v1/alerts` + `/api/v1/maintenance` | Alerts and maintenance features |
| [analytics.md](./analytics.md) | `GET /api/v1/analytics` | Analytics dashboard |
| [tracking.md](./tracking.md) | `GET /api/v1/arrivals` + `WS /ws/tracking` | Arrival times + live vehicle WebSocket |
| [superadmin.md](./superadmin.md) | `GET/PATCH /superadmin/*` | Platform admin portal |

---

## Common Rules (Apply to All Files)

- `tenantId` is extracted from JWT — never accepted from request body or URL
- All list endpoints support `?page=1&page_size=20` (max 100)
- All soft-deleted records are excluded from list results automatically
- `404` is returned for cross-tenant ID access (not `403`) — do not reveal existence
- Tier-gated endpoints return `403 FEATURE_NOT_AVAILABLE` for insufficient tier

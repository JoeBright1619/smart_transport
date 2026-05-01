# Shared — Naming Conventions & Code Quality

> Cross-layer rules for naming, code structure, version control, and documentation.
> Apply these in both frontend and backend work.

---

## Naming Conventions

### Identifiers
| Thing | Convention | Example |
|---|---|---|
| Entity IDs | `<prefix>-<uuid>` | `veh-uuid`, `drv-uuid`, `ten-uuid`, `route-uuid` |
| Boolean fields | `is` or `has` prefix | `isActive`, `isDeleted`, `hasAlerts` |
| Timestamp fields | `camelCase` + `At` suffix | `createdAt`, `updatedAt`, `completedAt` |
| Status enums | lowercase strings | `'active'`, `'on-trip'`, `'in-progress'` |

### By Layer
| Layer | Variables / Functions | Files | Components |
|---|---|---|---|
| Frontend (TS) | `camelCase` | `kebab-case.ts` or `PascalCase.tsx` | `PascalCase` |
| Backend (Python) | `snake_case` | `snake_case.py` | N/A |
| JSON API output | `camelCase` (always) | N/A | N/A |
| DB columns | `snake_case` | N/A | N/A |
| API endpoints | `lowercase-hyphenated` | N/A | N/A |

### Transport Domain Names
- Use descriptive, domain-specific names — never generic ones
- ✅ `VehicleCard`, `RouteTable`, `DriverList`, `FleetStatusCard`, `vehicle_service`, `alert_service`
- ❌ `Component1`, `CardWidget`, `MyTable`, `helper`, `utils2`

---

## Code Quality Rules

- **One responsibility per function** — max ~50 lines per function, ~200–300 lines per file
- **No wildcard imports** — `from module import *` is forbidden in Python
- **No hard-coded secrets** — use environment variables for all credentials and config
- **No `TODO` / `FIXME`** without a linked GitHub issue
- **Type annotations required** — TypeScript strict mode on frontend; full type hints on all Python functions
- **Docstrings required** on all public-facing Python functions and business logic functions

---

## Error Handling

- Never swallow errors silently
- Log errors with: entity ID, operation name, user role, tenant ID — without logging PII
- Frontend: user-friendly messages via Sonner toast; technical details to console in dev only
- Backend: always return the standard error envelope with an appropriate HTTP status code

---

## Git Workflow

- **Branch naming:** `feature/<short-description>`, `fix/<short-description>`, `chore/<short-description>`
- **Commit messages:** imperative mood, present tense → `Add vehicle dispatch endpoint`, `Fix delay calculation bug`
- **Never commit:** secrets, `.env` files, `node_modules/`, compiled binaries, large assets

---

## Documentation Standards

- Public API endpoints must have OpenAPI annotations (FastAPI docstring or `description=` param)
- Complex business logic (delay calc, geofence detection, feature gating) must have an inline comment explaining the algorithm
- New domain entities or status enums must be added to `shared/guidelines/entities.md` immediately

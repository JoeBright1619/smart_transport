# Smart Public Transport Tracking & Fleet Management – Tech Stack

> **Last updated:** 2026-03-24
> This document is the authoritative reference for all technology choices in this system.

---

## 1. Frontend

| Category | Technology | Version | Rationale |
|---|---|---|---|
| Framework | React | 18.x | Industry-standard for complex, data-driven UIs |
| Language | TypeScript | 5.x | Type safety across the entire frontend |
| Build Tool | Vite | 6.x | Fast HMR, native ESM, plugin ecosystem |
| Routing | React Router | v7 | File-based and code routing, nested layouts |
| Styling | Tailwind CSS | v4 | Utility-first; CSS-first config via `@theme {}` |
| UI Library | shadcn/ui (Radix UI) | latest | Accessible, un-styled primitives; customizable |
| Component Toolkit | MUI (Material UI) | v7 | Supplemental components where Radix is insufficient |
| Charts | Recharts | 2.x | Composable React chart components; SVG-based |
| Maps | React-Leaflet + Leaflet | 4.x / 1.9.x | Open-source map rendering, no API key required |
| Icons | Lucide React | latest | Consistent, tree-shakeable icon set |
| Animation | Motion (Framer) | 12.x | Declarative animations and transitions |
| Forms | React Hook Form | 7.x | Performant, uncontrolled form management |
| Notifications | Sonner | 2.x | Lightweight toast notifications |
| Date Utilities | date-fns | 3.x | Tree-shakeable date formatting/manipulation |
| Class Utilities | clsx + tailwind-merge | latest | Conditional class composition |
| Drag & Drop | React DnD | 16.x | Drag-and-drop interactions (dispatch board) |

### Frontend Dev Dependencies
| Tool | Purpose |
|---|---|
| `@vitejs/plugin-react` | React fast refresh in Vite |
| `@tailwindcss/vite` | Tailwind v4 Vite plugin |

---

## 2. Backend

| Category | Technology | Version | Rationale |
|---|---|---|---|
| Language | Python | 3.11+ | Async support, rich data science/geo ecosystem |
| Web Framework | FastAPI | 0.110+ | High-performance async API; OpenAPI auto-docs |
| ASGI Server | Uvicorn | 0.29+ | Production-grade ASGI server for FastAPI |
| Production Server | Gunicorn | 21.x | Process manager for multiple Uvicorn workers |
| Data Validation | Pydantic v2 | 2.x | Request/response validation; 5–50× faster than v1 |
| ORM | SQLAlchemy | 2.x | Async ORM with type-safe `Mapped` API |
| DB Migrations | Alembic | 1.x | Schema versioning tied to SQLAlchemy models |
| Auth | python-jose + passlib | latest | JWT creation/verification; bcrypt password hashing |
| Settings | pydantic-settings | 2.x | Type-safe `.env` configuration |
| WebSocket | FastAPI WebSockets | built-in | Real-time vehicle position broadcasting |
| Caching / Pub-Sub | Redis (via redis-py async) | 7.x | Real-time fan-out, analytics caching, sessions |
| Database Driver | asyncpg | 0.29+ | Async PostgreSQL driver for SQLAlchemy |
| HTTP Client | httpx | 0.27+ | Async HTTP for external integrations |
| Testing | pytest + pytest-asyncio | latest | Async-safe test runner |
| Linting/Formatting | Ruff | latest | Fast Python linter + formatter (replaces flake8/black) |
| Type Checking | mypy | 1.x | Static type checking for Python |

---

## 3. Database

| Category | Technology | Version | Rationale |
|---|---|---|---|
| Primary DB | PostgreSQL | 15+ | ACID compliance, rich GIS via PostGIS if needed |
| Dev/Test DB | SQLite | 3.x | Zero-config local development and unit tests |
| Cache / Pub-Sub | Redis | 7.x | Sub-millisecond pub/sub for WebSocket fan-out |

### PostgreSQL Extensions (Optional / Future)
| Extension | Use Case |
|---|---|
| `PostGIS` | Spatial queries (geofencing, route corridor checks) |
| `pg_trgm` | Fuzzy text search on vehicle/driver names |
| `timescaledb` | Time-series optimization for analytics data |

---

## 4. Infrastructure & DevOps

| Category | Technology | Rationale |
|---|---|---|
| Reverse Proxy | Nginx | TLS termination, static file serving, API proxying |
| Containerization | Docker + Docker Compose | Reproducible environments; easy local setup |
| CI/CD | GitHub Actions | Automated tests, linting, and Docker image builds |
| Static Hosting | Nginx (production) / Vite dev server (dev) | Serve built frontend assets |
| Secrets Management | Environment variables (`.env`) | Simple; upgrade to Vault/AWS Secrets Manager at scale |
| Monitoring (future) | Prometheus + Grafana | Metrics collection and dashboard |
| Logging (future) | Structured JSON logs → Loki or CloudWatch | Centralized log aggregation |

---

## 5. External Services

| Service | Purpose | Status |
|---|---|---|
| OpenStreetMap | Map tile provider for Leaflet (no API key) | Active — prototype |
| SMTP / Gmail | Email notifications for critical alerts | Implemented |
| (Future) Firebase Cloud Messaging | Mobile push notifications for passengers | Planned |
| (Future) Africa's Talking SMS API | SMS alerts for critical fleet events | Planned |

---

## 6. Development Tools

| Tool | Purpose |
|---|---|
| VS Code | Primary IDE |
| Figma | UI design and component reference |
| Postman / Bruno | API testing and documentation |
| pgAdmin / DBeaver | PostgreSQL administration |
| Git + GitHub | Version control and collaboration |
| pnpm | Frontend package manager (faster than npm) |

---

## 7. Key Architectural Decisions & Rationale

### Why FastAPI over Django/Flask?
- Native `async/await` support — essential for WebSocket broadcasting to hundreds of clients.
- Auto-generated OpenAPI docs (`/docs`) enable frontend devs to explore the API without a separate doc site.
- Pydantic integration gives consistent validation across all endpoints.

### Why Pydantic v2?
- 5–50× performance improvement over v1.
- Full Python type annotation support (`model_config`, `Annotated`, validators as descriptors).
- Used by FastAPI natively — zero integration friction.

### Why React Router v7 (not Next.js)?
- This is a **prototype SPA** embedded as a dashboard — SSR is unnecessary.
- Vite + React Router v7 provides all needed routing without the overhead of a full meta-framework.

### Why Tailwind CSS v4?
- CSS-first configuration (`@theme {}`) is cleaner and more portable than a JS config file.
- Aligns with the project's Vite-first setup via `@tailwindcss/vite`.
- Better performance in production builds.

### Why PostgreSQL over MySQL/MongoDB?
- Stronger ACID guarantees for financial (fare revenue) and operational data.
- PostGIS extension enables spatial geofencing queries without a separate geo service.
- SQLAlchemy ORM support is more mature for PostgreSQL.

### Why Redis for WebSocket fan-out?
- Enables horizontal scaling: multiple backend instances can all subscribe to the same Redis channel and broadcast to their local WebSocket clients.
- Also serves as an API response cache for analytics aggregations.

---

## 8. Tech Stack Constraints & Rules

- **TypeScript strict mode** is mandatory in the frontend; `any` type is forbidden.
- **Python type annotations** are mandatory on all function signatures in the backend.
- Do **not** introduce new major libraries without updating this document.
- Do **not** upgrade Tailwind from v4 to any future version without full team review (breaking changes).
- Do **not** use SQLite in production or staging — PostgreSQL only.
- Do **not** add direct frontend calls to any DB or cache layer — all data access goes through the REST API or WebSocket.

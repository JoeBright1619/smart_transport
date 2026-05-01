# Backend — Framework Patterns

> How to use FastAPI, Pydantic v2, and SQLAlchemy 2.x correctly in this project.

---

## FastAPI — Router Layer

- One router per resource, registered in `main.py` (see `architecture.md`)
- Routers handle **HTTP concerns only**: parse request, call service, return response
- Business logic lives in `services/` — never inline in a router function
- Always declare explicit response models:
  ```python
  @router.get("/", response_model=PaginatedResponse[VehicleRead])
  async def list_vehicles(...):
  ```
- Use `Depends()` for all cross-cutting concerns:
  ```python
  async def list_vehicles(
      db: AsyncSession = Depends(get_db),
      current_user: User = Depends(get_current_user),
      tenant: Tenant = Depends(get_current_tenant),
  ):
  ```

---

## FastAPI — Dependency Patterns

| Dependency | Purpose |
|---|---|
| `get_db` | Yields an async DB session; auto-closes on response |
| `get_current_user` | Decodes JWT → returns `User` ORM model |
| `get_current_tenant` | Loads `Tenant` → checks `isActive` → raises `403 TENANT_INACTIVE` if inactive |
| `require_role(*roles)` | Factory — raises `403` if user role not in allowed roles |

```python
# Usage examples
@router.delete("/{id}", dependencies=[Depends(require_role("admin", "superadmin"))])
```

---

## Pydantic v2 — Schema Patterns

Define three schemas per entity:

| Schema | Purpose | Notes |
|---|---|---|
| `VehicleCreate` | Fields required to create | Validates enums, coordinates |
| `VehicleUpdate` | All fields optional for PATCH | Use `Optional[T]` on every field |
| `VehicleRead` | Full response shape | Include `id`, `createdAt`; add `model_config = ConfigDict(from_attributes=True)` |

Rules:
- Never include `tenantId` as a writable field in Create/Update schemas for non-superadmin endpoints — it is always sourced from the JWT
- Use `Literal` or `Enum` types for status fields — never `str`
- Validate coordinates: `lat` in `[-90, 90]`, `lng` in `[-180, 180]`

---

## SQLAlchemy 2.x — Model Patterns

Use the modern `Mapped` / `mapped_column` typing API:

```python
class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"veh-{uuid4()}")
    tenant_id: Mapped[str] = mapped_column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    registration_number: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(Enum("active", "idle", "maintenance", "offline"), nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now())
```

Rules:
- Every operational model must have: `id`, `tenant_id`, `is_deleted`, `created_at`, `updated_at`
- Never use raw SQL strings — parameterized ORM queries only
- Declare all relationships explicitly with `relationship()` and specify `lazy=`
- Use `selectinload` for eager-loading related entities to avoid N+1 queries

---

## Service Layer — Patterns

- Services receive `db: AsyncSession` and `tenant_id: str` from dependency injection — they never create their own sessions or infer tenant from context
- Services return ORM model instances or Pydantic schemas — never HTTP response objects
- Complex multi-step operations must be wrapped in a single transaction:
  ```python
  async with db.begin():
      vehicle = await update_vehicle_status(db, vehicle_id, tenant_id)
      trip = await create_trip_record(db, vehicle, tenant_id)
      await audit_service.log(db, user_id, tenant_id, "Vehicle", vehicle.id, "update")
  ```
- **Every list query must apply `WHERE tenant_id = :tenant_id` as a mandatory filter** — see `shared/guidelines/multi-tenancy.md`

---

## Alert Auto-Generation

Alerts are created by `alert_service.py` only — never in routers or other services directly.

| Alert Type | Trigger |
|---|---|
| `delay` | Trip `delay` > 5 minutes |
| `breakdown` | Vehicle `engineStatus == 'critical'` |
| `maintenance` | `MaintenanceRecord.nextDue` within 7 days |
| `geofence` | Vehicle position > 500m outside assigned route corridor |
| `speeding` | Vehicle `speed` > 80 km/h |
| `info` | Driver status changed to `'available'` |

Duplicate suppression: do not create an alert if an unacknowledged alert of the same `type` + `vehicleId` already exists within the tenant.

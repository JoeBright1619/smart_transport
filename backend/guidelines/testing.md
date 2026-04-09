# Backend — Testing Guidelines

> Standards for writing and organizing tests.

---

## Stack

- **pytest** + **pytest-asyncio** for all async tests
- **SQLite in-memory** for unit tests (fast, zero setup)
- **PostgreSQL** for integration tests (matches production)
- `conftest.py` provides: async DB session fixture, test HTTP client, tenant factory, user factory

---

## Minimum Test Coverage Per Endpoint

Every router endpoint must have at minimum:

| Test Type | What to Verify |
|---|---|
| Happy path | Correct status code + response shape |
| Auth failure | Returns `401` when no/invalid JWT provided |
| Permission failure | Returns `403` when role is insufficient |
| Validation failure | Returns `400` or `422` on bad input |

---

## Tenant Isolation Tests (Required)

`test_tenant_isolation.py` is a mandatory test file. It must verify for **every resource type** that:

1. A user from **Tenant A** cannot `GET /api/v1/vehicles` and see Tenant B's vehicles
2. A user from **Tenant A** cannot `GET /api/v1/vehicles/{id}` and retrieve a vehicle belonging to Tenant B (must return `404`)
3. A user from **Tenant A** cannot `PATCH /api/v1/vehicles/{id}` to modify Tenant B's vehicle (must return `404`)
4. A user from **Tenant A** cannot `DELETE /api/v1/vehicles/{id}` to soft-delete Tenant B's vehicle (must return `404`)

These tests must cover: `vehicles`, `routes`, `trips`, `drivers`, `maintenance`, `alerts`.

---

## Test Organisation

```python
# conftest.py pattern
@pytest.fixture
async def tenant_a(db):
    return await tenant_service.create(db, name="Company A", ...)

@pytest.fixture
async def admin_a(db, tenant_a):
    return await user_service.create(db, tenant_id=tenant_a.id, role="admin", ...)

@pytest.fixture
async def vehicle_a(db, tenant_a):
    return await vehicle_service.create(db, tenant_id=tenant_a.id, ...)
```

---

## Coverage Target

- **≥80% coverage** on `services/` and `routers/`
- Mock external services in unit tests: email sending, WebSocket broadcasts, billing webhooks
- Test billing webhooks and WebSocket broadcasts in integration tests

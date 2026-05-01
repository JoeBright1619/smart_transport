# Shared — API Contract Rules

> Rules for every REST API endpoint in this system.
> Both the frontend (when consuming APIs) and the backend (when building APIs) must follow these contracts.

---

## URL Patterns

- Base URL: `/api/v1/<resource>` for tenant-scoped operations
- Superadmin routes: `/superadmin/<resource>` (no `/api/v1` prefix)
- Resources are **plural, lowercase**: `/vehicles`, `/routes`, `/trips`, `/drivers`, `/maintenance`, `/alerts`, `/analytics`, `/users`

## HTTP Methods

| Method | Use |
|---|---|
| `GET` | List or retrieve |
| `POST` | Create |
| `PATCH` | Partial update (preferred) |
| `PUT` | Full replacement (use sparingly) |
| `DELETE` | Soft delete only — never hard delete |

---

## Standard Response Envelope

**All** API responses must use this envelope — never return a raw list or object:

```json
{
  "data": <payload>,
  "meta": { "total": 100, "page": 1, "pageSize": 20 },
  "error": null
}
```

**Error envelope:**
```json
{
  "data": null,
  "meta": null,
  "error": { "code": "NOT_FOUND", "message": "Vehicle not found" }
}
```

---

## HTTP Status Codes

| Code | When to Use |
|---|---|
| `200 OK` | Successful GET / PATCH |
| `201 Created` | Successful POST |
| `204 No Content` | Successful DELETE (no body) |
| `400 Bad Request` | Validation failure (wrong format/type) |
| `401 Unauthorized` | Missing or invalid JWT |
| `403 Forbidden` | Insufficient role or inactive tenant account |
| `404 Not Found` | Resource does not exist (also use for cross-tenant ownership mismatch) |
| `409 Conflict` | Duplicate resource (e.g., duplicate registration number) |
| `422 Unprocessable Entity` | Semantically invalid input (e.g., end date before start date) |
| `500 Internal Server Error` | Unexpected backend error |

---

## Reserved SaaS Error Codes

These `code` values must be used exactly as specified in the error envelope:

| Code | Meaning |
|---|---|
| `TENANT_INACTIVE` | Tenant/company account is suspended or inactive |

---

## Pagination, Filtering, Sorting

All list endpoints must support:
- `?page=1&page_size=20` — default page 1, default size 20, max size 100
- `?sort=createdAt&order=desc` — where applicable
- Resource-specific filters: `?status=active`, `?routeId=route-1`, `?vehicleId=veh-1`

---

## Mandatory Tenant Scoping

Every list/read endpoint for operational data **must** implicitly scope results to the authenticated user's `tenantId` — extracted from the JWT, never from the request body or URL. See [`multi-tenancy.md`](./multi-tenancy.md) for full enforcement rules.

# API Spec — Authentication

> Public endpoints. No `Authorization` header required.
> Refresh token is delivered and read via `HttpOnly` cookie automatically.

---

## `POST /auth/register`
Register a new tenant and their first admin user in one step.

**Request:**
```json
{
  "companyName": "EcoFleet Ltd",
  "contactEmail": "admin@ecofleet.rw",
  "adminFullName": "Jean Claude Mugabo",
  "adminEmail": "jean@ecofleet.rw",
  "adminPhone": "+250788123456",
  "password": "SecurePass123!"
}
```
**Response `201`:**
```json
{
  "data": {
    "tenant": { "id": "ten-uuid", "name": "EcoFleet Ltd", "isActive": true },
    "user": { "id": "user-uuid", "email": "jean@ecofleet.rw", "role": "admin" },
    "accessToken": "<jwt>"
  }
}
```
**Errors:** `409` email already exists.

---

## `POST /auth/login`
**Request:** `{ "email": "jean@ecofleet.rw", "password": "SecurePass123!" }`

**Response `200`:**
```json
{
  "data": {
    "accessToken": "<jwt>",
    "user": { "id": "user-uuid", "fullName": "Jean Claude Mugabo", "role": "admin", "tenantId": "ten-uuid" }
  }
}
```
**Errors:** `401` invalid credentials | `403 TENANT_INACTIVE` if tenant/company account is suspended.

---

## `POST /auth/refresh`
No body — uses `HttpOnly` refresh cookie.

**Response `200`:** `{ "data": { "accessToken": "<new_jwt>" } }`

**Errors:** `401` if token missing, expired, or already rotated.

---

## `POST /auth/logout`
No body. Invalidates refresh token server-side.

**Response `204`.** No content.

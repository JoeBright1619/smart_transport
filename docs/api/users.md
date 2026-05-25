# API Spec — Users

> **Roles:** `admin` manages all users in their tenant. Own record: any role can read/update limited fields.

---

## `GET /api/v1/users`
**Roles:** `admin`, `superadmin`
**Query params:** `?role=operator&page=1&page_size=20`

**Response `200`:**
```json
{
  "data": [
    {
      "id": "user-uuid",
      "fullName": "Marie Umutesi",
      "email": "marie@ecofleet.rw",
      "role": "operator",
      "phone": "+250788234567",
      "isDeleted": false,
      "createdAt": "2026-04-01T08:00:00Z"
    }
  ],
  "meta": { "total": 5, "page": 1, "pageSize": 20 }
}
```

---

## `POST /api/v1/users`
**Roles:** `admin`

**Request:**
```json
{
  "fullName": "Paul Nkunda",
  "email": "paul@ecofleet.rw",
  "role": "dispatcher",
  "phone": "+250788345678",
  "password": "TempPass123!"
}
```
**Response `201`:** Single user object.
**Errors:** `409` duplicate email.

---

## `GET /api/v1/users/{id}`
**Roles:** `admin`, `superadmin` | Own record: any role.

**Response `200`:** Single user object.
**Errors:** `404` if not found or belongs to another tenant.

---

## `PATCH /api/v1/users/{id}`
**Roles:** `admin` (any user in tenant) | `operator`, `dispatcher` (own record only).

**Request** (all optional):
```json
{ "fullName": "Paul Nkunda Jr.", "phone": "+250788345679", "role": "operator" }
```
> `admin` cannot change their own role. Role changes are restricted to roles below the requester's level.

**Response `200`:** Updated user object.

---

## `DELETE /api/v1/users/{id}`
**Roles:** `admin`

Soft deletes the user and revokes all active sessions.

**Response `204`.**
**Errors:** `400` if trying to delete own account.

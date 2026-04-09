# Frontend Guidelines — Index

> Always check this index first and load only the files relevant to your task.
> Also read the relevant files from `prototype/shared/guidelines/` before working on anything that touches data or API calls.

---

## Files in This Directory

| File | What It Covers | Load When... |
|---|---|---|
| [architecture.md](./architecture.md) | Component structure, routing, module map, auth context | Adding pages, components, or routes |
| [design.md](./design.md) | UI rules, Tailwind v4, theming, responsiveness, naming | Building or modifying any UI element |
| [data.md](./data.md) | Mock data, simulation, charts, maps, tables | Displaying any data, adding charts or maps |

---

## Quick Reference: What to Load by Task

| Task | Shared Files | Frontend Files |
|---|---|---|
| New module page | `entities.md`, `auth.md` | `architecture.md`, `design.md` |
| New UI component | `conventions.md` | `design.md` |
| Chart or map widget | `entities.md` | `data.md`, `design.md` |
| API integration (real backend) | `api-contracts.md`, `multi-tenancy.md` | `architecture.md` |
| Auth / protected route | `auth.md` | `architecture.md` |
| Mock data / simulation | `entities.md` | `data.md` |

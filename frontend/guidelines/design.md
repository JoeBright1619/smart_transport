# Frontend — Design & UI Guidelines

> Rules for building UI components, applying styles, and maintaining visual consistency.

---

## Design Principles

This is a **professional fleet management platform** — not a consumer app.
- Prioritize operational clarity and data density over decorative aesthetics
- Every UI element must make sense in the context of public transport operations
- Avoid e-commerce, social-media, or entertainment design patterns

---

## Page Layout Rules

Every module page must follow this structure:
1. **Page header** — title, optional breadcrumb or description
2. **Filter / control panel** — module-specific actions and filters
3. **Data visualization** — charts, KPI cards, or map
4. **Data table / list** — detailed records

Every dashboard must include:
- Top navigation bar (system title, user profile, notification bell)
- Sidebar navigation linking all module pages
- Main content area with KPI stat cards, charts, and tables

Keep visible metrics: **active vehicles, delayed routes, fleet utilization, passenger demand**.

---

## Tailwind CSS v4 Rules

This project uses **Tailwind v4** via `@tailwindcss/vite`. Syntax differences from v3 apply:

- Configuration lives in `styles/theme.css` using `@theme {}` blocks — no `tailwind.config.js`
- Do not generate a `tailwind.config.js`
- Arbitrary values are supported: `bg-[#1a2b3c]`, `w-[320px]`
- Never mix v3 and v4 patterns in the same file
- Use `tailwind-merge` (`twMerge`) + `clsx` for conditional class composition

---

## Theme & Styling

- `styles/theme.css` is the single source of truth for colors, font sizes, spacing, and shadows
- Do not use inline styles — use Tailwind utility classes or `theme.css`
- Do not introduce new font families or color palettes
- Minor color tweaks for chart series, severity badges, and status indicators are allowed
- Use `lucide-react` exclusively for all icons — no other icon libraries

---

## Component Rules

- Buttons must reflect transport operations:
  - **Primary:** Add Vehicle, Dispatch Driver, Update Route, Acknowledge Alert
  - **Secondary:** Export, Filter, View Details
- Use `sonner` for all toast notifications
- Use `next-themes` for dark/light mode — do not implement custom theme switching
- Avoid purely decorative UI (gradients for decoration, illustration-heavy sections, etc.)
- Do not crowd a page with more than 3 charts — prefer summary stat cards + one main chart

---

## Naming Conventions

Use transport-domain-specific, descriptive names:

| ✅ Good | ❌ Bad |
|---|---|
| `VehicleCard` | `Component1` |
| `RouteTable` | `CardWidget` |
| `DriverList` | `MyTable` |
| `FleetStatusCard` | `DataDisplay` |
| `ArrivalTimePanel` | `InfoBox` |

- Components: `PascalCase`
- Hooks: `use` prefix + descriptive name → `useVehicleSimulation`, `useAuth`
- Files: same name as the primary export → `VehicleTracking.tsx`, `FleetStatusCard.tsx`

---

## Responsiveness

- **Desktop-first** — fleet management consoles run on large screens (1440px+)
- Also support: laptops (1280px+) and tablets (768px+)
- Mobile (< 768px) is out of scope for the fleet management interface
- Use Tailwind flex/grid layouts — avoid fixed pixel widths
- Dashboards must remain readable and functional at 1280×800 minimum viewport

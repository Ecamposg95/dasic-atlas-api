# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **Note:** `context/CLAUDE.md` describes a hypothetical Next.js/Prisma stack and is **not** the current implementation. The real stack is documented below.

## Source of truth — read first

This repo is documented in `context/`. Before any non-trivial change, read:

1. `context/00_CONTEXT_START_HERE.md` — index + Golden Rules
2. `context/02_REPO_CURRENT_STATE.md` — what's actually built and what's pending
3. `context/UI_PATTERNS.md` — mandatory frontend conventions (Jinja+Tailwind+Alpine)
4. `context/CRM_SPEC.md` and `context/RBAC.md` — domain spec + permissions matrix

## Stack

- **Backend:** FastAPI + SQLAlchemy 2.x + Alembic, Python (see `runtime.txt`)
- **DB:** PostgreSQL only, via `psycopg` (no SQLite, no in-memory fakes)
- **Auth:** JWT (`python-jose`) in HttpOnly cookie (`access_token`); `passlib[bcrypt]==4.0.1`
- **Frontend:** SSR with Jinja2 templates + Tailwind CDN + Alpine.js. **No SPA frameworks.**
- **PDFs / exports:** `fpdf2`, `openpyxl`, `qrcode`
- **Email:** SMTP via stdlib (configured through `SMTP_*` env vars)
- **AI:** Anthropic SDK (`app/services/ai_service.py`)

## Common commands

```bash
# Run dev server (auto-reload)
uvicorn app.main:app --reload
# Swagger: http://127.0.0.1:8000/docs

# Alembic migrations
alembic upgrade head
alembic revision --autogenerate -m "descripcion"
alembic downgrade -1

# Tenant bootstrap (idempotent — also runs in lifespan)
python scripts/bootstrap_tenant.py

# Production process (Procfile)
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

There is **no test suite** wired up. Validation has been done with `python -m py_compile` and manual checks. If you add tests, set up the harness first.

## Architecture

### Bootstrap flow (`app/main.py` → `app/core/lifespan.py` → `app/db/seeds.py`)

1. `configure_logging()` then `get_settings()` (cached, validates `DATABASE_URL` and `SECRET_KEY`).
2. `lifespan` runs at startup: `Base.metadata.create_all()` (transitional — Alembic is the long-term path), then `run_all_seeds()`:
   - `run_backfill_ddl` — idempotent `ALTER TABLE … ADD COLUMN IF NOT EXISTS` for legacy schemas pre-Alembic. **Treat this list as a migration shim, not as a permanent home.** New schema changes belong in Alembic.
   - `seed_base_tenant` — guarantees one `Organization` ("DASIC Industrial") + one HQ `Branch`.
   - `seed_super_admin` — creates `admin@dasic.com / admin123` if no users exist.
   - `ensure_memberships` + `backfill_organization_ids` — backfills org scope on legacy rows.
3. Routers mounted under `/api/*`; SSR HTML routes (login, dashboard, cotizador, seguimiento, inventario, clientes, compras, gastos, reportes, usuarios) are registered via `_protected_view` factory which decodes the cookie JWT and redirects unauthenticated users to `/`.

### Multi-tenancy (non-negotiable)

- Every business table carries `organization_id` (UUID stored as `VARCHAR(36)`).
- `app/dependencies.py::get_current_active_organization` resolves the tenant from `X-Organization-ID` header or the JWT `org_id` claim, validates membership in `UserOrganization`, and pushes it into a `ContextVar` via `app/core/context.py` so service code can read it without threading args.
- **Every query touching a business table must filter by `organization_id`.** No exceptions. Endpoints that return cross-tenant data are bugs.

### Domain layout

`app/models/` is partitioned by domain — do not create catch-all files:

- `enums.py` — `RolUsuario`, `EstatusOrden`, `TipoMovimiento`, `BranchType`
- `nucleus.py` — `Organization`, `Branch`, `UserOrganization` (multi-tenant core)
- `users.py` — `Usuario` (note: tolerates legacy enum aliases when reading from existing DBs)
- `catalog.py` — `Producto`, `Promocion` (cost-first: `costo_compra` + `moneda_compra`, `precio_publico` is no longer required)
- `clients.py` — `Cliente`, `Proveedor`
- `sales.py` — `OrdenVenta`, `DetalleOrden` (carries `moneda`/`tipo_cambio`/`utilidad_aplicada`; supports versioned re-quotes via `cotizacion_origen_id` + `version`; line items can be ad-hoc via `sku_libre` + `descripcion_libre` when `producto_id` is null)
- `purchases.py` — `OrdenCompra`, `DetalleCompra` (linked to a quote via `cotizacion_id`)
- `finance.py` — `TransaccionCliente`, `TransaccionProveedor`
- `quote_events.py` — `QuoteEvent` (audit log per quote: email, WhatsApp, AI suggestions)

`app/schemas/` mirrors this domain split for Pydantic. `app/routers/` exposes endpoints; routers are intentionally thick today (pending extraction into a repository/service layer — see `context/02_REPO_CURRENT_STATE.md`).

### Quote → folio → OC flow

- Folio format: `COT-YYYYMM-{user-initials}-NNNN` (or `VTA-…` for sales orders), generated **in the backend only** (see `_generar_folio` in `app/routers/ventas.py`).
- A quote (`EstatusOrden.COTIZACION`) becomes a sales order; `app/routers/compras.py` exposes `GET /api/compras/cotizacion/{quote_id}/borrador` to preview an OC without persisting it.
- Pricing model is **cost + utility margin**, not list price minus discount. Quote currency may differ from purchase currency; `tipo_cambio` is required when `moneda == "USD"`.

### RBAC (transitional)

Canonical roles in `RolUsuario`: `ADMINISTRADOR`, `GERENTE_COMERCIAL`, `VENTAS`. Legacy aliases (`ADMIN`, `ASISTENTE`, `VENDEDOR`) are still accepted when reading existing rows. Authorization helpers live in `app/security/jwt.py` (`allow_admin`, `allow_all_staff`, etc.). Real tenant-aware enforcement using `UserOrganization` is **pending** — current checks are role-string only.

## Conventions and rules

- **Multi-tenant always.** Every business query filters by `organization_id`. New tables get an `organization_id` column.
- **Alembic for schema changes.** Add a revision under `migrations/versions/` for any `app/models/` edit. Use `_BACKFILL_DDL` in `app/db/seeds.py` only as a transitional shim — new work goes into Alembic.
- **SSR only.** Templates are Jinja2 in `app/templates/`. Frontend interactivity is Alpine.js + Tailwind CDN. Do not introduce React/Vue/Svelte/etc.
- **Folios, totals, stock movements are server-side.** Never compute folios in the frontend. Recompute subtotal/IVA/total in the backend on save. Stock changes only via `MovimientoStock` rows.
- **Cookie auth.** SSR routes read the JWT from the `access_token` cookie; API routes accept `Authorization: Bearer …` or the same cookie. Do not move auth client-side.
- **DB URL normalization.** `app/core/config.py::normalize_database_url` rewrites `postgres://` and `postgresql://` to `postgresql+psycopg://`. Don't hand-craft URLs that bypass it.
- **Required env vars:** `DATABASE_URL`, `SECRET_KEY`. Optional: `ACCESS_TOKEN_EXPIRE_MINUTES`, `TOKEN_COOKIE_NAME`, `COOKIE_SECURE`, `ALLOWED_ORIGINS`, `SMTP_*`, `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`. Settings are validated at boot — the app refuses to start with a missing `DATABASE_URL` or `SECRET_KEY`.

## Known transitional state

- `create_all()` still runs in `lifespan` alongside Alembic; the eventual goal is Alembic-only (Phase 6 in `context/02_REPO_CURRENT_STATE.md`).
- Routers (`ventas.py`, `productos.py`, `compras.py`) mix domain logic, persistence, and presentation. A repository/service split is on the roadmap; small targeted changes are fine, but don't bundle a refactor into an unrelated fix.

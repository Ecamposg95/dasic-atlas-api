---
title: Atlas ONE — DASIC Industrial (ERP/CRM)
tags: [proyecto, dasic, atlas-one, erp, crm, fastapi, react, documentacion]
updated: 2026-06-05
repo: Dasic_Atlas_api
estado: producción (Railway, autodeploy desde main)
---

# Atlas ONE · DASIC Industrial

> [!abstract] Qué es
> **Atlas ONE** es el ERP/CRM industrial de **DASIC Industrial**: un sistema de cotización inteligente acoplado a inventario, CRM de pipeline, cobranza, remisiones y reportería, con una **consola de plataforma** separada para el dev/operador. Hoy es una **SPA React** servida por un backend **FastAPI**, desplegada en **Railway** con autodeploy desde `main`.

> [!warning] Documentos legacy
> El `README` y varios docs en `context/` describían un estado **anterior** (SSR Jinja2 + Alpine, multi-tenant estricto). **Eso ya no aplica.** La fuente de verdad del stack es `CLAUDE.md` (raíz) y este documento. Migración a SPA: **2026-05-22**. Multi-tenancy: **inerte en la práctica** (mono-tenant — `Usuario` no tiene `organization_id`).

---

## 1. Stack

| Capa | Tecnología |
|------|-----------|
| **Backend** | FastAPI + SQLAlchemy 2.x + Alembic, Python 3.11/3.12 |
| **DB** | PostgreSQL (solo), vía `psycopg`. Sin SQLite ni in-memory |
| **Auth** | JWT (`python-jose`) en cookie HttpOnly `access_token`; `passlib[bcrypt]` |
| **Frontend** | SPA React 18 + Vite 5 + TypeScript + Tailwind (compilado) + shadcn/ui + Zustand + TanStack Query v5 + React Router v6 |
| **PDF / export** | HTML imprimible (Jinja inline en routers) + `fpdf2`, `openpyxl`, `python-docx`, `qrcode` |
| **Email** | SMTP (stdlib), vía `SMTP_*` |
| **IA** | Anthropic SDK (`app/services/ai_service.py`) |
| **FX** | Banxico SIE (TC FIX SF63528) + fallback `open.er-api.com` |
| **Gráficos** | recharts |
| **Deploy** | Railway (nixpacks: corre `npm run build`); Procfile = `uvicorn`. **`alembic` NO corre en el Procfile.** |

> [!tip] Dónde vive el código del front
> Toda página del sistema vive en `web/src/features/<feature>/`. Build a `app/static/dist/` (commiteado a git). Cookie auth se preserva entre Vite dev (`:5173` proxy a `:8000`) y producción.

---

## 2. Arquitectura

### Bootstrap (`app/main.py` → `app/core/lifespan.py` → `app/db/seeds.py`)
1. `configure_logging()` + `get_settings()` (valida `DATABASE_URL`, `SECRET_KEY`).
2. **lifespan startup:** `Base.metadata.create_all()` (transicional — crea tablas nuevas automáticamente) + `run_all_seeds()`:
   - `run_backfill_ddl` — `ALTER TABLE … ADD COLUMN IF NOT EXISTS` idempotente (shim porque Railway no corre Alembic).
   - `seed_super_admin` — admin inicial si la DB está vacía.
   - `seed_dedicated_superadmin` — crea superadmin DEDICADO desde env (`SUPERADMIN_EMAIL`/`SUPERADMIN_PASSWORD`).
   - `promote_superadmin_from_env` — promueve `BOOTSTRAP_SUPERADMIN_EMAIL`.
   - `seed_marcas`, `seed_sat_*`, `seed_contactos_principal`, `seed_default_pipeline`.
3. Routers bajo `/api/*`. Las rutas `/spa/*` sirven el `index.html` del SPA (con `Cache-Control: no-cache`).

### Dominio (`app/models/` — "design by domain", sin archivos todólogos)
`enums`, `nucleus`, `users`, `catalog`, `clients`, `sales`, `purchases`, `finance`, `quote_events`, `remisiones`, `reportes_servicio`, `services`, `sat`, `fantasmas`, `inventory`, `precios`, `expenses`, `fx`, `plantillas`, `platform`, **`crm`** (Pipeline/Stage/Deal), **`recordatorios`** (Recordatorio).

### Frontend (`web/src/`)
- `features/<x>/` con patrón `types.ts` + `hooks/use<X>.ts` (TanStack Query) + `pages/<X>Page.tsx` + `components/`.
- Primitivas en `components/ui/` (shadcn-style, **tokenizadas**).
- Chrome en `components/layout/` (Sidebar, Header, Footer, ThemeToggle, Layout).
- Router en `router.tsx` (code-split lazy + auto-reload ante chunk stale tras deploy).

---

## 3. Design System premium (2026-06-04)

> [!note] Estrategia aditiva
> Se introdujeron **tokens semánticos** (HSL, soportan alpha) consumidos por las primitivas y el chrome, SIN migrar las ~66 páginas slate de golpe (heredan el feel). Dark = **near-black azulado** (`--background: #070b16`, `--surface: #0d1424`).

- **Tokens** (`web/src/index.css` + `tailwind.config.ts`): `bg-background`, `bg-card`, `bg-surface-2`, `text-foreground`, `text-muted-foreground`, `border-border`, `border-border-strong`, `ring-ring`, `primary`, sombras `elev-1/2/3` + `glow-accent`, easing `premium`.
- **Acento comercial:** cyan `accent-glow` (#00d4e0) + blue `accent-deep`. **Acento dev (superadmin):** emerald/lima.
- **Microinteracciones:** glow en botón primario, modales con `backdrop-blur` + animación `modal-in`, `.app-canvas` con gradiente radial sutil.
- **Migrado a tokens:** primitivas, chrome, y el **cotizador** completo (cierra la diferencia de luminancia). Pendiente: ~65 páginas restantes (mismo mapeo de 8 pares por feature).

---

## 4. Módulos

### Comercial
- **Dashboard** — KPIs, sparklines, tendencia (recharts), pipeline donut, alertas, panel de recordatorios.
- **CRM Pipeline** (`/spa/crm`) — Kanban de deals por etapa, **drag-and-drop HTML5 nativo** + update optimista. Modelos `Pipeline`/`PipelineStage`/`Deal`. Seed crea pipeline "Ventas" (Prospecto→Cotizado→Negociación→Ganado/Perdido).
- **Cotizador** — el corazón. Costo + utilidad (NO lista menos descuento). Multimoneda con TC del día (DOF±spread). Líneas catálogo / fantasma / servicio / libres. Plantillas. Recotización versionada. PDF (desglose o **unificado**), Word, remisión, reporte de servicio.
- **Borradores · Seguimiento** — historial de cotizaciones con vigencia, filtros, acciones (recotizar, convertir, cancelar, **recordar seguimiento**).
- **Recordatorios** (`/spa/recordatorios`) — tareas de próximo contacto sobre cotizaciones; vistas vencidos/hoy/próximos; panel en dashboard. Owner-scoped.
- **Clientes (Empresas) · Contactos** — CRM de cuentas, contactos múltiples, dedup/unificación de empresas, estado de cuenta + PDF.

### Operación
- **Compras** — OC desde cotización (borrador → persistencia), historial paginado.
- **Fantasmas** — productos no-catálogo solicitados; promover a producto real (con SAT).
- **Remisiones** — desde orden o libre; PDF + **Word (.docx)**.
- **Reportes de servicio** — actas de servicio (PDF).
- **Gastos** — egresos operativos.

### Catálogo
- **Inventario** — productos costo-first, stock auditable (`movimientos_stock`/kardex), reservas, importación Excel/CSV.
- **Servicios · Precios (proveedor) · Diccionarios (marcas/categorías/unidades + navegador SAT)**.

### Finanzas
- **Centro de cobranza** (CxC) — aging **0-30/31-60/61-90/90+** (donut), top deudores, registrar pago distribuido (FIFO), estado de cuenta PDF.
- **Tipo de cambio (FX)** — Banxico + fallback; override manual.

### Reportes
- **Reportes** (ventas, inventario, conversión) y **Analítica de servicios**.

### Plataforma (Consola Super-Admin — solo dev) — `/spa/superadmin/*`
> [!important] Identidad visual distinta (emerald/mono "dev console") vía `PlatformShell`, mismo Layout.
- **Overview · Usuarios de plataforma · Configuración · Auditoría · Salud · Mantenimiento.**
- **Usuarios** — CRUD con rol superadmin habilitado; blindajes anti-escalada (solo superadmin modifica/elimina/resetea otro superadmin), protección último-superadmin-activo, anti-auto-bloqueo.
- **Configuración** — IVA/vigencia en runtime (sin redeploy).
- **Auditoría** — timeline global (cotizaciones + fusiones).
- **Salud** — versión/git/uptime, conteos DB, FX, integraciones (booleanos, sin secretos).
- **Mantenimiento** — re-seeds idempotentes, jobs (CxC vencidas, refresh FX), seed-context, **ZONA ROJA** (drop-all-tables con doble guarda: type-to-confirm "BORRAR TODO" + diálogo danger; blindado a solo superadmin).

---

## 5. Reglas no negociables (Golden Rules — actualizadas)

> [!danger] Cambió respecto a docs viejos
> - ~~SSR Jinja/Alpine~~ → **SPA React** en `web/src/features/<x>/`. NO crear `.html` nuevos en `app/templates/` (se conservan como respaldo histórico).
> - ~~Multi-tenant siempre~~ → **mono-tenant en la práctica** (`organization_id` existe en columnas pero es inerte; `Usuario` no lo tiene). No asumir aislamiento por org.

- **Folios, totales y movimientos de stock = server-side.** Nunca calcular folios en el front. Recalcular subtotal/IVA/total en el backend al guardar. Stock solo vía filas `MovimientoStock`.
- **Cookie auth.** No mover auth al cliente. `@/lib/api` ya hace `credentials:'include'`.
- **Alembic para schema** + entrada paralela en `_BACKFILL_DDL` (Railway no corre alembic). Tablas NUEVAS las crea `create_all` (no requieren backfill); columnas en tablas existentes SÍ.
- **Re-exportar** clases nuevas de modelos/schemas en `__init__.py` (+`__all__`) o la app crashea al arrancar (py_compile NO lo detecta).
- **Build SPA antes de push:** `cd web && npm run build`. Commitear `app/static/dist/`.
- **Enums en query:** nunca filtrar `rol` con strings crudos — usar `RolUsuario.X` (los valores de DB son `superadmin/admin/asistente/vendedor/operativo`, NO los nombres).

---

## 6. RBAC

Roles canónicos: `ADMINISTRADOR` (="admin"), `GERENTE_COMERCIAL` (="asistente"), `VENTAS` (="vendedor"), `OPERATIVO`, `SUPERADMIN`. Aliases legacy tolerados al leer. Helpers en `app/security/jwt.py`: `allow_superadmin`, `allow_user_admin`/`allow_admin`, `allow_admin_asistente`, `allow_all_staff`. `is_owner_scoped(user,"read","cotizacion")` → VENTAS ve solo lo suyo. Enforcement tenant-aware real: **pendiente** (hoy role-string).

---

## 7. Cómo correr

```bash
# Backend (auto-reload) — necesita DATABASE_URL + SECRET_KEY
uvicorn app.main:app --reload          # Swagger en /docs

# Frontend
cd web && npm install && npm run dev    # Vite :5173 (proxy a :8000)
cd web && npm run build                 # build a app/static/dist (pre-push)

# Alembic
alembic upgrade head
alembic revision --autogenerate -m "desc"
```

**Env requeridas:** `DATABASE_URL`, `SECRET_KEY`. Opcionales clave: `BANXICO_TOKEN`, `ANTHROPIC_API_KEY`, `SMTP_*`, `SUPERADMIN_EMAIL`/`SUPERADMIN_PASSWORD` (crear superadmin dedicado), `BOOTSTRAP_SUPERADMIN_EMAIL` (promover existente).

> [!tip] Crear tu cuenta superadmin (dev)
> Setear `SUPERADMIN_EMAIL` + `SUPERADMIN_PASSWORD` en Railway → redeploy → login. Idempotente, nunca pisa el password si ya existe.

---

## 8. Gotchas / lecciones

- **Chunk stale tras deploy:** `index.html` es `no-cache`, pero una SPA abierta puede pedir un chunk con hash viejo → el `lazyPage` auto-recarga una vez (guarda en `sessionStorage`).
- **Enums lowercase:** el backend serializa enums en minúsculas (cargo/abono, entrada/salida). Comparar case-insensitive en el front.
- **PDF cotización paginado:** ya no fuerza "1 hoja" — pagina con encabezado de tabla repetido, filas sin partir, totales una vez, y **footer en flujo normal (última hoja)**.
- **Decimales:** el backend manda strings, los types TS dicen `number` (funciona por coerción).
- **Pydantic v2** manda `detail` 422 como array de objetos → usar `normalizeDetail` en el front.

---

## 9. Roadmap

> [!todo] Pendiente
> - **CRM v2:** CRUD visual de pipelines/stages, métricas de conversión por etapa, deal↔cotización bidireccional, actividades/tareas por deal.
> - **Timeline automático de negocio** (eventos: deal movido, cotización enviada, pago recibido).
> - **RBAC tenant-aware real** (hoy inerte).
> - **Migrar las ~65 páginas slate restantes a tokens** (cotizador ya hecho).
> - **Superadmin:** impersonación, feature flags, Módulo B v2 (`audit_log` + instrumentar login/CRUD usuarios/precio-stock), log de mantenimiento.
> - **Aprobaciones de descuento** por rol; **WhatsApp nivel B** (API oficial).
> - **`SECRET_KEY` persistente en Railway** (para que no rote por deploy) — config.

---

## 10. Mapa rápido de archivos

| Necesito… | Archivo |
|-----------|---------|
| Stack real / reglas | `CLAUDE.md` (raíz) |
| Estado del repo | `context/02_REPO_CURRENT_STATE.md` |
| Modelos por dominio | `app/models/*.py` |
| Tokens / tema | `web/src/index.css`, `web/tailwind.config.ts` |
| Chrome / layout | `web/src/components/layout/` |
| Primitivas UI | `web/src/components/ui/` |
| Rutas SPA | `web/src/router.tsx` |
| Seeds / bootstrap | `app/db/seeds.py`, `app/core/lifespan.py` |
| Consola dev | `web/src/features/superadmin/`, `app/routers/superadmin.py` |
| PDF cotización | `app/routers/ventas.py` (`PDF_TEMPLATE_VENTA`) |

---

> [!quote] TL;DR
> SPA React + FastAPI, mono-tenant en práctica, cotizador costo+utilidad multimoneda como corazón, CRM Kanban, centro de cobranza con aging, recordatorios, consola de plataforma dev con skin propio, design system premium con tokens (dark near-black). Deploy continuo a Railway desde `main`.

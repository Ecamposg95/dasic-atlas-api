# Estado Actual del Repo (dasic-atlas-api / Atlas ONE)

> **Actualizado:** 2026-06-05. Rama de referencia: `main` (autodeploy a Railway).
> Fuente de verdad del stack: `CLAUDE.md` (raíz) + `docs/Atlas-ONE-Proyecto.md`.

El repo dejó de ser un refactor base hace tiempo. Es un **ERP/CRM en producción**: SPA React (migrada 2026-05-22) sobre FastAPI, con design system premium tokenizado, CRM Kanban, cotizador robusto, centro de cobranza, recordatorios, y una consola de plataforma (super-admin) separada. **Mono-tenant en la práctica.**

## Stack (resumen — ver `CLAUDE.md` para detalle)

- **Backend:** FastAPI + SQLAlchemy 2.x + Alembic + PostgreSQL (`psycopg`). Modelos por dominio en `app/models/`.
- **Frontend:** SPA React 18 + Vite + TypeScript + Tailwind (compilado) + shadcn/ui + Zustand + TanStack Query v5 + React Router v6, en `web/src/features/<x>/`. Build a `app/static/dist/` (commiteado).
- **Auth:** JWT en cookie HttpOnly `access_token`.
- **Deploy:** Railway (nixpacks corre `npm run build`); Procfile = `uvicorn`. **Alembic NO corre en deploy** → shim `_BACKFILL_DDL` para columnas en tablas existentes; `create_all()` en lifespan crea tablas nuevas.

## Qué está construido (módulos en producción)

**Comercial:** Dashboard (KPIs + recharts + panel recordatorios) · **CRM Pipeline** Kanban (Pipeline/Stage/Deal, DnD nativo) · **Cotizador** (costo+utilidad, multimoneda, plantillas, recotización versionada, PDF desglose/unificado + Word + remisión + reporte servicio) · Borradores · Seguimiento · **Recordatorios** · Clientes/Empresas + Contactos (dedup, estado de cuenta + PDF).

**Operación:** Compras (OC desde cotización) · Fantasmas (promover a producto) · Remisiones (PDF + **Word**) · Reportes de servicio · Gastos.

**Catálogo:** Inventario (costo-first, kardex auditable, reservas, import Excel) · Servicios · Precios proveedor · Diccionarios (marcas/categorías/unidades + navegador SAT).

**Finanzas:** **Centro de cobranza** (aging 0-30/31-60/61-90/90+, top deudores, pago distribuido FIFO, estado de cuenta PDF) · FX (Banxico + fallback).

**Reportes:** Reportes (ventas/inventario/conversión) · Analítica de servicios.

**Plataforma (Consola Super-Admin, solo dev — skin emerald/mono vía `PlatformShell`):** Usuarios de plataforma (CRUD + rol superadmin, blindajes anti-escalada) · Configuración runtime (IVA/vigencia sin redeploy) · Auditoría global · Salud del sistema · Mantenimiento (re-seeds, jobs, seed-context, zona roja drop-all-tables con doble guarda).

## Design system premium (2026-06-04)

Tokens semánticos HSL (`web/src/index.css` + `tailwind.config.ts`): `bg-card`, `bg-surface-2`, `text-foreground`, `text-muted-foreground`, `border-border`, etc. Dark = near-black azulado. Consumidos por primitivas (`components/ui/`) y chrome (`components/layout/`). **Cotizador ya migrado a tokens**; ~65 páginas slate restantes pendientes (mismo mapeo de 8 pares por feature).

## RBAC

Roles: `SUPERADMIN`, `ADMINISTRADOR` (="admin"), `GERENTE_COMERCIAL` (="asistente"), `VENTAS` (="vendedor"), `OPERATIVO`. Helpers en `app/security/jwt.py`. Owner scoping (`is_owner_scoped`) para VENTAS. **Enforcement tenant-aware real: pendiente** (hoy role-string). Blindaje superadmin: solo superadmin gestiona otro superadmin (anti-escalada cerrada 2026-06-04).

## Riesgos / deuda

1. **RBAC tenant-aware inexistente** (mono-tenant en práctica; `Usuario` sin `organization_id`).
2. **Routers cargados** (`ventas.py`, `productos.py`, `compras.py` mezclan dominio/persistencia/presentación). Falta capa repository/services.
3. **Sin suite de tests** — validación por `py_compile` + `npm run build` + review por subagentes + QA visual manual.
4. **Decimales** serializados como string; los types TS dicen `number` (coerción).

## Pendientes (roadmap activo)

1. **CRM v2** — CRUD visual de pipelines/stages, métricas de conversión, deal↔cotización bidireccional, actividades por deal.
2. **Timeline automático de negocio** (eventos deal/cotización/pago).
3. **Migrar ~65 páginas slate restantes a tokens** (cotizador ya hecho).
4. **RBAC tenant-aware real.**
5. **Super-admin:** impersonación, feature flags, Módulo B v2 (`audit_log` + instrumentar login/CRUD usuarios/precio-stock), log de mantenimiento.
6. **Aprobaciones de descuento** por rol; **WhatsApp nivel B**.
7. **`SECRET_KEY` persistente en Railway** (config, para que no rote por deploy).

## Histórico (lanes cerrados — resumen)

RBAC fase 1 · catálogo costo-first · cotizador fase 2 (multimoneda) · seguimiento · folios/recotización · OC real · migración SPA (2026-05-22) · Atlas ONE rebrand + theme · arquitectura de documentos (OC/remisión/reporte desde cotización) · empresas+contactos · auditoría paralela · super-admin Módulos 0/A/B/C/D · design system premium · paginación · módulos activados (estado cuenta/kardex/SAT) · CRM Kanban · centro de cobranza · recordatorios · migración cotizador a tokens. Detalle por commit en `git log` y en las notas de sesión.

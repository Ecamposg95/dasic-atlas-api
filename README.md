# Atlas ONE — DASIC Industrial (ERP/CRM)

Sistema **ERP/CRM industrial** de DASIC Industrial: cotizador inteligente (costo + utilidad, multimoneda) acoplado a inventario, CRM de pipeline, cobranza con aging, remisiones, reportería y una **consola de plataforma** (super-admin) separada.

> **Stack actual (migrado 2026-05-22):** SPA **React 18 + Vite + TypeScript + Tailwind + shadcn/ui + Zustand + TanStack Query** servida por backend **FastAPI + SQLAlchemy 2.x + PostgreSQL**, desplegada en **Railway** (autodeploy desde `main`).
>
> ⚠️ Si lees docs viejos que dicen *"SSR Jinja/Alpine"* o *"multi-tenant siempre"*: **ya no aplican.** La fuente de verdad es **`CLAUDE.md`** (raíz) y **`docs/Atlas-ONE-Proyecto.md`** (overview generoso para Obsidian). El sistema es **mono-tenant en la práctica** (`organization_id` existe en columnas pero es inerte).

## Arquitectura (resumen)

- **Backend** `app/`: FastAPI. Modelos por dominio (`app/models/*.py`), routers `/api/*`, seeds/bootstrap en `app/core/lifespan.py` + `app/db/seeds.py`. `create_all()` crea tablas nuevas al boot; Alembic es la fuente canónica del schema, pero **el Procfile no corre alembic** → toda columna nueva en tabla existente necesita entrada paralela en `_BACKFILL_DDL`.
- **Frontend** `web/src/`: cada página vive en `features/<x>/` (`types.ts` + `hooks/use<X>.ts` + `pages/` + `components/`). Primitivas tokenizadas en `components/ui/`, chrome en `components/layout/`, rutas en `router.tsx`. Build a `app/static/dist/` (commiteado).
- **Auth:** JWT en cookie HttpOnly `access_token` (no mover al cliente).

## Módulos

Dashboard · **CRM Pipeline** (Kanban) · **Cotizador** (PDF/Word/remisión) · Borradores · Seguimiento · **Recordatorios** · Clientes/Contactos · Compras · Fantasmas · Remisiones · Reportes de servicio · Gastos · Inventario (kardex) · Servicios · Precios · Diccionarios/SAT · **Centro de cobranza** (aging) · FX · Reportes · **Consola Super-Admin** (usuarios, config runtime, auditoría, salud, mantenimiento).

## Reglas no negociables

- **Folios, totales y movimientos de stock = server-side.** Stock solo vía filas `MovimientoStock`.
- **No crear `.html` nuevos** en `app/templates/` (legacy de respaldo). Toda UI nueva en `web/src/features/<x>/`.
- **Re-exportar** modelos/schemas nuevos en `__init__.py` (+`__all__`) o la app crashea al arrancar (py_compile no lo detecta).
- **Enums en query:** usar `RolUsuario.X`, nunca strings crudos (valores DB: `superadmin/admin/asistente/vendedor/operativo`).
- **`cd web && npm run build`** antes de push; commitear `app/static/dist/`.

## Correr local

```bash
# Backend (necesita DATABASE_URL + SECRET_KEY)
uvicorn app.main:app --reload          # Swagger: http://127.0.0.1:8000/docs

# Frontend
cd web && npm install && npm run dev    # Vite :5173 (proxy a :8000)
cd web && npm run build                 # build de producción

# Alembic
alembic upgrade head
alembic revision --autogenerate -m "descripcion"
```

**Env requeridas:** `DATABASE_URL`, `SECRET_KEY`. Opcionales: `BANXICO_TOKEN`, `ANTHROPIC_API_KEY`, `SMTP_*`, `SUPERADMIN_EMAIL`+`SUPERADMIN_PASSWORD` (crea superadmin dedicado), `BOOTSTRAP_SUPERADMIN_EMAIL` (promueve existente).

## ¿Eres un agente AI / nuevo en el repo?

Lee en orden: **`CLAUDE.md`** → **`docs/Atlas-ONE-Proyecto.md`** → **`context/02_REPO_CURRENT_STATE.md`** → `context/CRM_SPEC.md` / `context/RBAC.md`. Nota: `context/UI_PATTERNS.md` y partes de `context/` describen el stack SSR previo y son **parcialmente legacy**.

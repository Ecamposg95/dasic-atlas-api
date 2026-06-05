# Context Index (DASIC CRM Industrial)

Este directorio contiene la documentación viva del proyecto. La referencia de arquitectura viene de Atlas ERP/POS, pero el preset activo, el esquema operativo del producto, e incentivo de negocio es **DASIC ERP Industrial**.

> [!] **ESTE DIRECTORIO ES PARCIALMENTE LEGACY.** Varios docs describen el stack SSR (Jinja2 + Alpine) y multi-tenant que el proyecto tuvo hasta abril-2026. Eso **ya no aplica**. La fuente de verdad del stack actual es **`CLAUDE.md` (raíz del repo)** y **`docs/Atlas-ONE-Proyecto.md`**.

Documentos canónicos vigentes:
- **`CLAUDE.md` (raíz)** — stack real, reglas, arquitectura. (`context/CLAUDE.md` es un boceto Next.js/Prisma hipotético — NO es la implementación.)
- **`docs/Atlas-ONE-Proyecto.md`** — overview completo (módulos, design system, gotchas, roadmap).
- `02_REPO_CURRENT_STATE.md` — estado actual del repo.
- `CRM_SPEC.md` / `RBAC.md` — spec de dominio (CRM_SPEC es visión; los modelos Pipeline/Deal ya existen en `app/models/crm.py`).

## Golden Rules (actualizadas 2026-06-05)

1. **SPA React, no SSR** (migrado 2026-05-22): toda UI nueva en `web/src/features/<x>/`. NO crear `.html` nuevos en `app/templates/` (legacy de respaldo). ~~Jinja/Alpine~~.
2. **Mono-tenant en la práctica**: `organization_id` existe en columnas pero es inerte (`Usuario` no lo tiene). NO asumir aislamiento por org. ~~Multi-tenant siempre~~.
3. **Server-side**: folios, totales (subtotal/IVA/total) y movimientos de stock (`MovimientoStock`) se calculan en el backend. Nunca folios en el front.
4. **Alembic + `_BACKFILL_DDL`**: el Procfile no corre alembic; columnas nuevas en tablas existentes necesitan entrada paralela en `app/db/seeds.py::_BACKFILL_DDL`. Tablas nuevas las crea `create_all`.
5. **Diseño por dominio**: `app/models/<dominio>.py`, sin archivos todólogos. Re-exportar clases nuevas en `__init__.py` (+`__all__`) o la app crashea al arrancar.
6. **Auth con cookie HttpOnly** (`access_token`). No mover al cliente.
7. **Build antes de push**: `cd web && npm run build`; commitear `app/static/dist/`.

## Lectura Recomendada a Agentes de AI o Nuevos Contribuyentes (Orden)

1. **`CLAUDE.md` (raíz)** — stack real y reglas.
2. **`docs/Atlas-ONE-Proyecto.md`** — overview de módulos, design system y gotchas.
3. `02_REPO_CURRENT_STATE.md` — fotografía del repo y pendientes.
4. `CRM_SPEC.md` / `RBAC.md` — dominio y permisos.
5. (Legacy, contexto histórico) `DASIC_Plataforma_Base.md`, `UI_PATTERNS.md`, `ROADMAP.md`, `STACK_ADOPTION_CHECKLIST.md`.

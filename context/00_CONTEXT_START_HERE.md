# Context Index (DASIC CRM Industrial)

Este directorio contiene la documentación viva del proyecto. La referencia de arquitectura viene de Atlas ERP/POS, pero el preset activo, el esquema operativo del producto, e incentivo de negocio es **DASIC ERP Industrial**.

Documentos canónicos más importantes:
- `atlas_erp_pos_stack.md` (Baseline de infraestructura técnica original).
- `DASIC_Plataforma_Base.md` (Baseline del Roadmap a 90 días con enfoque a Stocks, Dashboard y Smart Quoter CRM).
- `UI_PATTERNS.md` (La biblia obligatoria del diseño Jinja+Tailwind para consistencia Front-end).

## Golden Rules

1. **Multi-tenant siempre**: toda tabla de negocio incluye `organization_id` (UUID) y toda query filtra por `organization_id`. Capa modelada por dominio en `models/nucleus.py`.
2. **Alembic obligatorio**: toda evolución del esquema de DB local y de prod debe ejecutarse por `alembic revision` (SQLAlchemy 2.0).
3. **Diseño por Dominio (Domain-Driven)**: Componentes en la base se ramifican bajo dominios semánticos (users, catalog, quotes, admin). No crear archivos "todólogos".
4. **Auth mediante Core Central**: `core/lifespan.py`, SSR sin endpoints desacoplados en el Front, y Auth con cookies HttpOnly.
5. **UI con Alpine.js/Tailwind:** Ninguna importación de librería SPA ajena al UI Stack autorizado.

## Lectura Recomendada a Agentes de AI o Nuevos Contribuyentes (Orden)

Si acabas de integrarte al proyecto, asimila el código con este orden imperativo:

1. `00_CONTEXT_START_HERE.md` (Este documento).
2. `DASIC_Plataforma_Base.md` (Blueprint comercial, KPIs y visión del cotizador-stock rápido).
3. `02_REPO_CURRENT_STATE.md` (Fotografía exacta y lista de tareas donde el proyecto está "pausado" el día de hoy).
4. `STACK_ADOPTION_CHECKLIST.md` (Estado granular del refactor y validación).
5. `CRM_SPEC.md` / `RBAC.md` (Especificaciones del CRM MVP por construir y matriz de permisos de Branch y global).
6. `UI_PATTERNS.md` (Reglas visuales y componentes).
7. `ROADMAP.md` (Hoja de ruta iterativa integral).

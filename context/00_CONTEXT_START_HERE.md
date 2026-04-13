# Context Index (DASIC CRM Industrial)

Este directorio contiene la documentacion viva del proyecto. La referencia de arquitectura viene de Atlas ERP/POS, pero el preset activo y el objetivo de producto es **DASIC ERP Industrial** enfocado en un **CRM muy potente** (pipeline, actividades, WhatsApp manual, cotizaciones ligadas a oportunidades).

Documento canonico de desarrollo:

- `atlas_erp_pos_stack.md`

Este archivo define el baseline tecnico. El resto de documentos aterrizan ese baseline al contexto DASIC.

## Golden Rules

1. **Multi-tenant siempre**: toda tabla de negocio incluye `organization_id` (UUID) y toda query filtra por `organization_id`.
1. **Multi-branch**: los usuarios pueden ser globales (HQ) o branch-scoped. Si es branch-scoped, la visibilidad se limita a su `branch_id` salvo roles de nivel gerente+.
1. **SSR, no SPA**: UI server-side con Jinja2 + Tailwind CDN + Alpine.js. Nada de routing client-side.
1. **RBAC + visibilidad por asignacion**: no basta con roles; para roles operativos (VENTAS/CRM) se aplica ownership/asignacion.
1. **Auth SSR con cookies HttpOnly**: JWT en cookie HttpOnly (y opcional cookie de org/branch). Evitar `localStorage`.
1. **PostgreSQL directo**: sin fallback a SQLite.
1. **Alembic obligatorio**: toda evolucion del esquema va por migraciones.

## Lectura Recomendada (orden)

1. `01_ATLAS_REFERENCE.md` (referencia de arquitectura)
1. `atlas_erp_pos_stack.md` (baseline canonico)
1. `02_REPO_CURRENT_STATE.md` (estado actual del repo)
1. `STACK_ADOPTION_CHECKLIST.md` (estado de adopcion y deltas)
1. `adr/README.md` (registro formal de decisiones)
1. `CRM_SPEC.md` (modelo, endpoints, flujos)
1. `RBAC.md` (roles, permisos, reglas de visibilidad)
1. `ARCHITECTURE.md` (capas, dependencias, convenciones)
1. `ROADMAP.md` (fases de implementacion)
1. `API_CONVENTIONS.md` (headers, paginacion, errores)
1. `MOONSHOT_VISION.md` (vision: CRM que supera a Monday/Salesforce/HubSpot/Zoho)

# Stack Adoption Checklist (Atlas -> DASIC)

Este checklist convierte `context/atlas_erp_pos_stack.md` en plan ejecutable.

Estados:

- `ADOPTADO`: ya implementado en el repo.
- `EN_PROGRESO`: parcialmente implementado.
- `PENDIENTE`: definido, no implementado.
- `NO_APLICA`: no entra en este producto.

## 1) Nucleus

- DB session y engine centralizados (`app/db/`) — `ADOPTADO`
- `DATABASE_URL` por entorno + `.env` — `ADOPTADO`
- PostgreSQL como objetivo local/prod — `ADOPTADO`
- Mixins `TenantMixin/AuditMixin/UUIDMixin` — `PENDIENTE`
- `Organization` + `Branch` + `UserOrganization` — `PENDIENTE`

## 2) Seguridad

- JWT y dependencias de auth separadas (`app/security/`) — `ADOPTADO`
- `SECRET_KEY` desde entorno (sin hardcode) — `EN_PROGRESO`
- Cookie HttpOnly como flujo principal SSR — `EN_PROGRESO`
- RBAC por dependencias + ownership — `EN_PROGRESO`

## 3) Arquitectura por capas

- `app/models`, `app/schemas`, `app/routers`, `app/services` — `ADOPTADO`
- Routers delgados + servicios con logica de negocio — `EN_PROGRESO`
- Convencion `/api/*` para endpoints API — `ADOPTADO`

## 4) CRM Industrial (core)

- Accounts/Contacts/Locations — `PENDIENTE`
- Pipelines multipropósito por org — `PENDIENTE`
- Deals + stage movement + assign — `PENDIENTE`
- Activities + WhatsApp manual (Nivel A) — `PENDIENTE`
- Timeline events — `PENDIENTE`

## 5) Quality Gates

- Aislamiento tenant por `organization_id` en todas las queries — `PENDIENTE`
- Branch scope tests — `PENDIENTE`
- RBAC + ownership tests — `PENDIENTE`
- Alembic como flujo obligatorio de cambios de schema — `PENDIENTE`

## Delta DASIC (controlado)

Registrar aqui cualquier diferencia intencional respecto al baseline Atlas.

1. Driver PostgreSQL: `psycopg` (v3) en lugar de `psycopg2-binary`.
1. Naming operativo de base local: `dasic_crm_local`.
1. Linea de producto: CRM-first (no POS-first).

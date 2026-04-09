# Roadmap de Implementacion (DASIC CRM Industrial)

Este roadmap es el orden recomendado de trabajo para convertir el prototipo actual en un CRM industrial multi-tenant basado en patrones de Atlas.

## Fase 0: Documentacion y alineacion

1. Crear `context/` (este directorio)
1. Reescribir `README.md` para reflejar: CRM-first, PostgreSQL, multi-tenant, cookies HttpOnly

## Fase 1: Base tecnica estable

1. Corregir imports para que `uvicorn app.main:app` sea estable
1. Normalizar paths de `templates/` y `static/`
1. Alinear hashing (bcrypt o argon2) y dependencias

## Fase 2: PostgreSQL + config por entorno

1. `DATABASE_URL` obligatorio (sin SQLite fallback)
1. Config central (`SECRET_KEY`, expiracion)
1. Conexion SQLAlchemy 2.x

## Fase 3: Alembic (migraciones)

1. Inicializar Alembic
1. Migracion inicial del esquema base
1. Workflow: cambios de modelos == revision Alembic

## Fase 4: Nucleus multi-tenant + multi-branch

1. Modelos: `Organization(UUID)`, `Branch(UUID)`, `User`, `UserOrganization`
1. Dependencias: `get_current_user`, `get_current_org`, `get_current_branch`
1. Enforcements: header `X-Organization-ID` y validacion contra JWT

## Fase 5: RBAC + visibilidad

1. Implementar `require_roles([...])`
1. Implementar filtros de visibilidad por ownership/asignacion
1. Branch scope para entidades que tengan `branch_id`

## Fase 6: CRM Engine MVP

1. Accounts, Contacts, Locations
1. Pipelines + Stages (multiples pipelines)
1. Deals + move stage + assign
1. Activities (incl WhatsApp Nivel A)
1. Timeline events

## Fase 7: SSR CRM-first

1. Layout base con Tailwind CDN + Alpine.js
1. Pantallas: dashboard, accounts, account detail, pipeline kanban, deal detail, activities, admin pipelines
1. Auth SSR con cookies HttpOnly

## Fase 8: Cotizaciones integradas (siguiente)

1. Quote ligado a Deal/Account
1. Partidas
1. PDF
1. Timeline: quote created/sent

## Fase 9: QA minima

1. Tests de aislamiento tenant
1. Tests branch scope
1. Tests RBAC/ownership

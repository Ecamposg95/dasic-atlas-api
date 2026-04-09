# RBAC (DASIC CRM Industrial)

Roles cerrados y reglas de visibilidad para un CRM industrial multi-tenant.

## Platform roles (cross-tenant)

- `SUPERADMIN`: acceso a todas las organizaciones (solo para plataforma)
- `SUPPORT`: soporte limitado y auditado
- `NONE`

## Tenant roles (por organizacion)

1. `DUEÑO`
1. `ADMINISTRADOR`
1. `GERENTE_COMERCIAL`
1. `VENTAS`
1. `CRM`
1. `AUDITOR`
1. `LECTOR`

## Reglas de visibilidad (ownership)

Entidades CRM principales (Accounts, Deals, Activities) deben aplicar ownership/asignacion.

- `DUEÑO`/`ADMINISTRADOR`/`GERENTE_COMERCIAL`: visibilidad org-wide.
- `VENTAS`/`CRM`: visibilidad limitada a:
  - `owner_user_id == current_user.id` o
  - `assigned_to_user_id == current_user.id` o
  - asignacion explicita (si se implementa una tabla de assignment)
- `AUDITOR`: lectura org-wide (sin writes)
- `LECTOR`: lectura limitada (dashboard + lista/consulta; sin export masivo ni acciones)

## Branch scope

- Si `current_user.branch_id != NULL`, se restringe a esa branch en entidades que tengan `branch_id`.
- Usuarios HQ (`branch_id = NULL`) pueden consultar cualquier branch dentro de la org.

## Permisos (MVP)

### Pipelines y stages

- Crear/editar pipelines/stages: `ADMINISTRADOR`, `DUEÑO`
- Ver: todos los roles tenant

### Accounts (clientes)

- Crear: `CRM`, `VENTAS`, `GERENTE_COMERCIAL`, `ADMINISTRADOR`, `DUEÑO`
- Editar: `CRM`, `VENTAS` (si es owner/asignado), `GERENTE_COMERCIAL+`
- Ver: segun visibilidad

### Deals (oportunidades)

- Crear: `VENTAS`, `CRM`, `GERENTE_COMERCIAL+`
- Mover etapa: `VENTAS`, `CRM` (si es owner/asignado), `GERENTE_COMERCIAL+`
- Reasignar: `GERENTE_COMERCIAL`, `ADMINISTRADOR`, `DUEÑO`
- Cerrar ganado/perdido: `VENTAS`, `CRM` (owner/asignado), `GERENTE_COMERCIAL+`

### Activities (incluye WhatsApp manual)

- Crear: `VENTAS`, `CRM`, `GERENTE_COMERCIAL+`
- Completar/cerrar: asignado o `GERENTE_COMERCIAL+`
- Ver: segun visibilidad del deal/account asociado

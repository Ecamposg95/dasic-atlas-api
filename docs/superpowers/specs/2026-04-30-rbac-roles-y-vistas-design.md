# RBAC: Roles, accesos y vistas DASIC

**Fecha:** 2026-04-30
**Estado:** spec aprobado verbalmente. Sirve como contrato para la implementación.
**Módulos afectados:** `app/security/`, todos los routers, plantillas Jinja2 y JS Alpine.

## Contexto y problema

El proyecto define cinco roles en `app/models/enums.py::RolUsuario` (SUPERADMIN, ADMINISTRADOR, GERENTE_COMERCIAL, VENTAS, OPERATIVO), pero el control de acceso real es desigual:

- Sólo se enforce con dependencias FastAPI (`allow_admin`, `allow_admin_asistente`, `allow_all_staff`) que filtran por **rol** pero **no por dueño del recurso**. Un vendedor puede ver y editar cotizaciones que no son suyas.
- El rol `OPERATIVO` (almacén) está declarado pero nunca se usa.
- El frontend no esconde menús ni botones según rol — todo se muestra y los endpoints rechazan; UX rota para roles bajos.
- No hay un endpoint que el frontend pueda consultar para saber "qué puedo hacer".

Esto bloquea el onboarding de nuevos usuarios reales (vendedores, almacén) y rompe el principio de menor privilegio.

## Objetivos

1. **Cuatro roles operativos** explícitos con responsabilidades claras: `ADMINISTRADOR`, `GERENTE_COMERCIAL`, `VENTAS`, `OPERATIVO`. `SUPERADMIN` queda como alias técnico (mismo poder que admin).
2. **Matriz declarativa** de permisos en un solo lugar (`app/security/permissions.py`).
3. **Owner scoping** para `VENTAS`: ve y edita solo sus propias cotizaciones, sus propios clientes, sus propias OCs.
4. **Endpoint `/api/me`** con flags de capacidades para que el frontend oculte UI sin tener que conocer la matriz.
5. **Frontend role-aware**: sidebar, botones y formularios muestran/ocultan según rol.
6. **Fail closed**: ante duda, denegar.

## No-objetivos

- No agregar más roles (los cinco enum existentes son suficientes).
- No multi-tenant; ya se descartó.
- No ACL fino por recurso/registro (más allá del owner scoping). Si un gerente quiere acceso temporal a algo de otro vendedor, lo hace via admin.
- No auditoría de accesos en este sprint (log básico sí, dashboard de auditoría no).

## Decisiones clave

### D1. Cuatro roles operativos + alias

| Enum | Operativo | Descripción |
|---|---|---|
| `SUPERADMIN`, `ADMINISTRADOR` (alias `ADMIN`) | **Admin** | Dueño/operador. Todo, incluido CRUD usuarios. |
| `GERENTE_COMERCIAL` (alias `ASISTENTE`) | **Gerente** | Supervisa ventas del equipo. No toca usuarios. |
| `VENTAS` (alias `VENDEDOR`) | **Ventas** | Cotiza, vende. Solo ve lo suyo. |
| `OPERATIVO` | **Almacén** | Inventario, recepción de OC, ajustes con motivo. No ve cotizaciones ni precios de venta. |

Internamente la matriz usa los enum nombres canónicos. Las aliases existen sólo para tolerar valores legacy en DB.

### D2. Matriz centralizada

`app/security/permissions.py` declara permisos como tuplas `(action, resource)`:

```python
PERMISSIONS = {
    RolUsuario.ADMINISTRADOR: {ALL},  # *.*
    RolUsuario.GERENTE_COMERCIAL: {
        ("read", "cotizacion"), ("write", "cotizacion"), ("convert", "cotizacion"),
        ("read", "cliente"),    ("write", "cliente"),
        ("read", "producto"),   ("write", "producto"),
        ("read", "oc"),         ("write", "oc"),
        ("read", "dashboard:team"),
        ("read", "reportes"),   ("export", "reportes"),
        # NO: usuarios, ajuste manual stock (ese es de admin/almacén)
    },
    RolUsuario.VENTAS: {
        ("read:own", "cotizacion"), ("write:own", "cotizacion"), ("convert:own", "cotizacion"),
        ("read:own", "cliente"),    ("create", "cliente"),  ("write:own", "cliente"),
        ("read", "producto"),       # solo precios de venta, no costo
        ("read:own", "oc"),
        ("read", "dashboard:own"),
    },
    RolUsuario.OPERATIVO: {
        ("read", "producto"),       ("write", "producto"),  ("ajuste", "stock"),
        ("read", "oc"),             ("recibir", "oc"),
        ("read", "dashboard:inventory"),
    },
}
```

Tres helpers:

- `can(user, action, resource) -> bool` — chequeo binario.
- `require(user, action, resource)` — levanta 403 si no.
- `scope_query_by_owner(query, user, model)` — agrega `WHERE vendedor_id = user.id` cuando el rol es VENTAS y la acción es `:own`.

Los decoradores existentes (`allow_admin`, etc.) se mantienen como compat pero los routers nuevos usan `require()`.

### D3. Owner scoping para VENTAS

Aplicar a:
- `OrdenVenta` (cotizaciones y ventas) → filtrar por `vendedor_id`.
- `Cliente` → un cliente "le pertenece" al primer vendedor que lo creó. Modelo no tiene `creado_por_id`; agregar columna en migración.
- `OrdenCompra` → filtrar por la cotización vinculada (`cotizacion_id`); si no hay, gerente/admin lo ven, ventas no.

Lectura: VENTAS solo ve los suyos. Escritura/edición/cancelación: igual. Conversión a venta: solo las suyas.

GERENTE y ADMIN ven todo.

### D4. `/api/me` con capabilities

```json
GET /api/me
{
  "id": 1,
  "email": "vendedor@dasic.com",
  "nombre": "Juan Pérez",
  "rol": "ventas",
  "rol_label": "Ventas",
  "capabilities": {
    "ver_cotizaciones": "own",
    "crear_cotizacion": true,
    "convertir_a_venta": "own",
    "ver_costos": false,
    "gestionar_usuarios": false,
    "ajustar_stock": false,
    "ver_dashboard_equipo": false,
    "modulos_visibles": ["cotizador", "seguimiento", "clientes", "reportes"],
    ...
  }
}
```

El frontend hidrata un Alpine store `$store.user` y usa `$store.user.can('ajustar_stock')` para mostrar/ocultar.

### D5. Sidebar role-aware

Sidebar declara cada link con `roles_allowed`. Helper Jinja `if current_user.rol in [...]` o, mejor, leer `$store.user.modulos_visibles` desde Alpine.

| Módulo | Admin | Gerente | Ventas | Operativo |
|---|---|---|---|---|
| Dashboard | ✓ (full) | ✓ (team) | ✓ (own) | ✓ (inventory) |
| Cotizador | ✓ | ✓ | ✓ | ✗ |
| Seguimiento | ✓ | ✓ | ✓ (own) | ✗ |
| Inventario | ✓ | ✓ | ✓ (read-only) | ✓ |
| Clientes | ✓ | ✓ | ✓ (own) | ✗ |
| Compras | ✓ | ✓ | ✓ (own) | ✓ (recepción) |
| Gastos | ✓ | ✓ | ✗ | ✗ |
| Reportes | ✓ | ✓ | ✓ (own) | ✗ |
| Usuarios | ✓ | ✗ | ✗ | ✗ |

### D6. UI por rol

Botones/secciones con `x-show="$store.user.can('X')"`:
- Botón "Ajuste manual" en inventario → operativo y admin.
- Columna "Costo" en inventario → admin/gerente/operativo (ventas no).
- Botón "Convertir a venta" → admin/gerente siempre, ventas sólo sobre sus propias cotizaciones.
- Botón "Cancelar cotización" → admin/gerente siempre, ventas sólo si es del usuario.
- Sidebar item "Usuarios" → solo admin.

Cuando el rol no aplica, el componente sale completamente del DOM (no `disabled`); el endpoint sigue protegido como defensa en profundidad.

### D7. Migraciones requeridas

- `clientes.creado_por_id INTEGER NULL REFERENCES usuarios(id)` — para el owner scoping de cliente. Backfill: NULL en filas existentes (admin/gerente las ven, ventas no las ven hasta reasignar).

## Modelo de datos

Cambios:
- `clientes`: + `creado_por_id INTEGER NULL FK usuarios.id` (index).

No se tocan: `usuarios`, `ordenes_venta` (ya tiene `vendedor_id`), `ordenes_compra` (link a cotización ya existe).

## API

Endpoints nuevos:

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/me` | User + capabilities. Cualquier usuario logueado. |

Endpoints modificados (sin cambiar contrato externo, sólo gating + scoping):

- `GET /api/ventas/historial` — VENTAS solo ve sus folios.
- `GET /api/ventas/{id}` — 404 si no es del user (VENTAS).
- `PUT/POST /api/ventas/{id}/{action}` — 403 idem.
- `POST /api/ventas/` — al crear, `vendedor_id = current_user.id` (ya lo hace).
- `GET /api/clientes/` — VENTAS solo los suyos (creado_por_id = user.id).
- `GET /api/clientes/{id}/estado-cuenta` — idem.
- `GET /api/compras/` — VENTAS solo OCs vinculadas a sus cotizaciones.
- `GET /api/dashboard/*` — ya scoped (vendedor solo lo suyo).
- `GET /api/inventario/*` — VENTAS no puede ajustar; OPERATIVO sí.
- `GET /api/productos/` — VENTAS no recibe `costo_compra` (ya existe `ProductoResponseVendedor`, asegurar que se aplica).

## Edge cases

- **Cliente sin `creado_por_id` (legacy)**: visible solo para admin/gerente. Ventas no lo ve hasta que admin lo reasigne. Mensaje en UI sugiriendo "este cliente está sin asignar".
- **Vendedor cancela cotización ajena**: 403 explícito con `mensaje: "No es tu cotización"`.
- **Admin se da de baja a sí mismo**: ya bloqueado en `eliminar_usuario`. Mantener.
- **Gerente promovido a admin durante la sesión**: la cookie JWT se actualiza al re-login. Documentar.
- **Operativo intenta abrir cotizador**: redirect a `/inventario` con flash message.

## Test plan (manual smoke)

| Caso | Quien | Acción | Esperado |
|---|---|---|---|
| Login admin → ve sidebar completo | admin | abrir / | 8 items |
| Login gerente → no ve Usuarios | gerente | abrir / | sidebar sin Usuarios |
| Login ventas → no ve Gastos ni Usuarios | ventas | abrir / | 6 items |
| Login operativo → ve solo Inventario+Compras+Dashboard | operativo | abrir / | 3 items |
| Vendedor A pide cot id=X (de vendedor B) | ventas A | GET /ventas/X | 404 |
| Vendedor edita cot ajena | ventas A | PUT /ventas/X | 403 |
| Operativo intenta crear cotización | operativo | POST /ventas/ | 403 |
| Operativo ajusta stock | operativo | POST /inventario/movimientos | 200 |
| Ventas ajusta stock | ventas | POST /inventario/movimientos | 403 |
| Ventas ve costos en inventario | ventas | GET /productos/?limit=1 | response sin `costo_compra` |
| /api/me devuelve capabilities según rol | cualquiera | GET /api/me | flags coherentes |

## Riesgos

- **Roles legacy en DB**: filas con rol `'admin'` o `'asistente'` se interpretan correctamente por `RolUsuario.from_input`, pero hay que validar que la matriz use el enum canónico.
- **Cambios silenciosos**: aplicar gating sin probar puede romper flujos. Mitigación: smoke checklist antes del push final.
- **Frontend desincronizado**: si la matriz cambia en backend pero `/api/me` no se ajusta, UI esconde algo que sí debería mostrar (o viceversa). Mitigación: derivar `capabilities` del mismo módulo `permissions.py`.

## Próximos pasos

1. Implementar `app/security/permissions.py` con la matriz.
2. Migración + columna `clientes.creado_por_id`.
3. Endpoint `/api/me`.
4. Aplicar `require()` y `scope_query_by_owner()` en routers.
5. Sidebar Jinja role-aware + Alpine `$store.user`.
6. Smoke testing por rol.
7. Onboarding doc actualizada con sección "RBAC".

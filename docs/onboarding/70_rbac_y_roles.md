# RBAC y roles

Implementación: `app/security/permissions.py`. Spec: `docs/superpowers/specs/2026-04-30-rbac-roles-y-vistas-design.md`.

## Roles

| Enum (`RolUsuario`) | Aliases legacy | Operativo |
|---|---|---|
| `ADMINISTRADOR` | `ADMIN`, `SUPERADMIN` | Admin (todo) |
| `GERENTE_COMERCIAL` | `ASISTENTE` | Gerente |
| `VENTAS` | `VENDEDOR` | Vendedor |
| `OPERATIVO` | — | Almacén |

## Matriz por módulo

| Módulo | Admin | Gerente | Ventas | Almacén |
|---|---|---|---|---|
| Dashboard | Full | Team | Own | Inventory only |
| Cotizador | ✓ | ✓ | ✓ | ✗ |
| Seguimiento (historial) | Full | Full | Own | ✗ |
| Inventario | ✓ | ✓ | Read-only | ✓ |
| Clientes | Full | Full | Own + create | ✗ |
| Compras / OCs | ✓ | ✓ | Own | Read + recibir |
| Reportes | Full | Full | Own | ✗ |
| Gastos | ✓ | ✓ | ✗ | ✗ |
| Usuarios | ✓ | ✗ | ✗ | ✗ |

## Acciones específicas

| Acción | Admin | Gerente | Ventas | Almacén |
|---|---|---|---|---|
| Crear cotización | ✓ | ✓ | ✓ | ✗ |
| Convertir a venta | ✓ | ✓ | Sólo las suyas | ✗ |
| Cancelar cotización | ✓ | ✓ | Sólo las suyas | ✗ |
| Generar OC desde cot. | ✓ | ✓ | Sólo las suyas | ✗ |
| Recibir OC (entrada stock) | ✓ | ✓ | ✗ | ✓ |
| Ajuste manual de stock | ✓ | ✓ | ✗ | ✓ |
| Alta/edit de producto | ✓ | ✓ | ✗ | ✓ |
| Ver costo de compra | ✓ | ✓ | ✗ | ✓ |
| Crear/editar usuario | ✓ | ✗ | ✗ | ✗ |
| Reset password de otro | ✓ | ✗ | ✗ | ✗ |

## Cómo se enforce

### Backend

1. **Decoradores FastAPI legacy** (`allow_admin`, `allow_admin_asistente`, `allow_all_staff` en `app/security/jwt.py`) — chequeo grueso por rol al entrar al endpoint.
2. **`require(user, action, resource)`** — chequeo fino con la matriz central. Levanta 403.
3. **`is_owner_scoped(user, action, resource)`** + filtro SQL — para owner scoping. Aplicado en:
   - `/api/clientes/` → filtra por `creado_por_id`.
   - `/api/ventas/historial` → filtra por `vendedor_id`.
   - `/api/ventas/{id}/convertir`, `/cancelar` → 404 si no es del user.
4. **Schemas separados por rol** — `ProductoResponseVendedor` no incluye `costo_compra`; `ProductoResponseAdmin` sí. La lógica está en `app/routers/productos.py::listar_productos`.

### Frontend

`/api/auth/me` devuelve el user + flags de capabilities + lista `modulos_visibles`. El frontend hidrata `Alpine.store('user')` al boot de `base.html` y usa:

- `x-show="$store.user.canVer('cotizador')"` → esconde sidebar items.
- `x-show="$store.user.can('ver_costos')"` → esconde columnas/celdas con costo.
- `x-show="$store.user.can('editar_producto')"` → esconde botón "Nuevo Producto".

Esto es **defensa en profundidad** — si el frontend tiene un bug y muestra algo, el backend igual rechaza.

## Cómo agregar un permiso nuevo

1. Decidí la tupla `(action, resource)`. Agregala al set del rol en `app/security/permissions.py::PERMISSIONS`.
2. Si querés exponerla al frontend como un flag, agregala a `CAPABILITY_FLAGS`.
3. En el endpoint backend, llama `require(current_user, action, resource)` o `is_owner_scoped(...)` para filtrar.
4. En la plantilla, `x-show="$store.user.can('mi_flag')"`.
5. Smoke test con un usuario de cada rol (script en `docs/onboarding/30_dev_workflow.md`).

## Cómo agregar un rol nuevo

Si necesitás un rol más allá de los 4 actuales (no recomendado):

1. Agregar al enum `RolUsuario` en `app/models/enums.py`.
2. Agregar al mapping en `from_input` y `api_value`.
3. Crear su set de tuplas en `PERMISSIONS`.
4. Agregar lista en `MODULOS_VISIBLES_BY_ROL`.
5. Agregar label en `_ROL_LABELS`.
6. Si tienen una capa de checks legacy (`allow_admin_asistente` etc.), revisar si el nuevo rol cae ahí.

## Owner scoping: cómo funciona

Para `VENTAS`, las queries que listan recursos los filtran por dueño. El helper:

```python
from app.security.permissions import is_owner_scoped

query = db.query(MyModel)
if is_owner_scoped(current_user, "read", "cotizacion"):
    query = query.filter(MyModel.vendedor_id == current_user.id)
```

Para `Cliente` el dueño es `creado_por_id` (lo agregamos en migración `20260430_02`). Clientes legacy con `creado_por_id IS NULL` sólo son visibles para admin/gerente — los vendedores no los ven hasta que admin se los reasigne.

## Smoke test rápido por rol

```bash
# como admin: crear los 3 roles de prueba
for ROL in gerente_comercial ventas operativo; do
  curl -s -b /tmp/c-admin -X POST http://127.0.0.1:8001/api/usuarios/ \
    -H 'Content-Type: application/json' \
    -d "{\"nombre\":\"QA $ROL\",\"email\":\"qa_${ROL}@dasic.com\",\"password\":\"qa123456\",\"rol\":\"$ROL\",\"activo\":true}"
done

# login con cada uno
for ROL in gerente_comercial ventas operativo; do
  curl -s -c /tmp/c-$ROL -X POST http://127.0.0.1:8001/api/auth/login \
    -d "username=qa_${ROL}@dasic.com&password=qa123456" \
    -H 'Content-Type: application/x-www-form-urlencoded' > /dev/null
done

# /api/auth/me por rol
for ROL in admin gerente_comercial ventas operativo; do
  echo "--- $ROL ---"
  curl -s -b /tmp/c-$ROL http://127.0.0.1:8001/api/auth/me | python3 -m json.tool | head -15
done
```

Resultado esperado:
- admin: `modulos_visibles` = 9 items, todos los flags `true`.
- gerente_comercial: 8 items, `gestionar_usuarios=false`.
- ventas: 6 items, `ver_costos=false`, `ajustar_stock=false`, dashboard `own`.
- operativo: 3 items (dashboard, inventario, compras), `ajustar_stock=true`, `ver_cotizaciones=false`.

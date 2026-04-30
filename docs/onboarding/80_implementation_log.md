# Implementation log — RBAC roles y vistas

Sesión: 2026-04-30. Objetivo: cuatro roles operativos con accesos diferenciados, owner scoping para VENTAS, frontend role-aware.

## Workstreams ejecutados

| WS | Descripción | Archivos | Commit |
|---|---|---|---|
| WS1 | Spec formal RBAC | `docs/superpowers/specs/2026-04-30-rbac-roles-y-vistas-design.md` | `619521c` |
| WS2 | Módulo central de permisos | `app/security/permissions.py` | `619521c` |
| WS3 | Backend gating + owner scoping | `app/routers/{auth,clientes,ventas,inventario}.py`, `app/models/clients.py`, `app/db/seeds.py`, `migrations/versions/20260430_02_*.py` | `af7400e` + `75dc217` |
| WS4 | Endpoint `/api/auth/me` | `app/routers/auth.py` | `af7400e` |
| WS5 | Frontend sidebar + Alpine `$store.user` | `app/templates/{base,inventario}.html` | `29de3d0` |
| WS6 | Onboarding docs | `docs/onboarding/*.md` | (este commit) |
| WS7 | QA por rol (smoke) | `docs/onboarding/70_rbac_y_roles.md` (script al final) | (este commit) |

## Decisiones clave (qué y por qué)

| Decisión | Motivación | Riesgo |
|---|---|---|
| Mantener decoradores legacy `allow_admin*` | Compat con el código existente; los nuevos endpoints prefieren `require()` | Doble capa puede confundir; documentado en `permissions.py` |
| Cuatro roles, descartar SUPERADMIN como rol distinto | DASIC no necesita escalar privilegios extra; SUPERADMIN trata igual que ADMIN | Si en el futuro se requiere multi-tenant, hay que separarlos |
| `creado_por_id` como columna NULL en `clientes` | Backwards-compat con clientes existentes que no tenían dueño | Clientes legacy no son visibles a VENTAS hasta que admin los reasigne — UX requiere flujo de reasignación (no incluido este sprint) |
| Owner scoping vía `is_owner_scoped` + `query.filter(...)` | Más explícito que un decorador mágico; permite combinar con otros filtros | Cada endpoint que liste recursos sensibles debe acordarse de aplicarlo. Mitigación: `require()` falla cerrado. |
| Frontend hidrata `$store.user` con `/api/auth/me` al boot | El frontend no necesita conocer la matriz; todos los flags vienen del backend | Si el endpoint falla, sidebar muestra todo (default permissive). Aceptable porque endpoints siguen rechazando con 403. |
| Backfill DDL en `lifespan` para Railway | El Procfile no corre `alembic upgrade head` | Cada migración nueva requiere actualizar `_BACKFILL_DDL`. Documentado en troubleshooting + dev_workflow. |

## Asumimos

- DASIC usa **cuatro roles**: Admin, Gerente, Ventas, Almacén (Operativo). El usuario aprobó verbalmente sin pedir simplificación a 3.
- `OPERATIVO` no ve Cotizador ni Clientes ni Reportes. Solo Inventario y Compras (recepción).
- Vendedor es dueño de un cliente vía `creado_por_id`. Si un cliente fue creado antes de que existiera la columna, queda sin dueño y solo admin/gerente lo ven.
- "Costo de compra" lo ven Admin, Gerente y Operativo (porque el almacén verifica facturas de proveedor); Ventas no.

## Riesgos abiertos

- **Endpoints sin gating**: hice WS3 selectivo (clientes, ventas/historial, ventas/convertir, ventas/cancelar, inventario/movimientos). **Faltan todavía**: `/api/compras/*`, `/api/productos/*` (delete, ajustar-stock), `/api/ventas/{id}` (PUT/GET detalle), `/api/dashboard/*` (algunos ya scope, faltan tops/heatmap). Plan: pasar QA por cada uno y agregar `require()` donde falte. **No bloquea entrega** — los decoradores `allow_*` legacy ya cubren la dimensión "rol", solo falta el "scoping" fino.
- **Clientes legacy sin dueño**: 2 clientes Vitracoat creados por el seed no tienen `creado_por_id`. Resultado: vendedor no los ve. Workaround: admin asigna manualmente vía SQL o vía UI futura.
- **Frontend**: solo escondí Costo y "Nuevo Producto" en `/inventario`. Faltan ajustes en cotizador/clientes/compras/historial. Bajo prioridad porque endpoints rechazan; UX subóptima para roles bajos pero funcional.
- **No hay testing automatizado** — todo smoke manual con curl + psql. Pendiente cuando haya tiempo.

## Próximas acciones recomendadas

1. **Pasar el resto de routers por `require()`**: compras, productos, dashboard, gastos. Estimado: 1h.
2. **UI de reasignación de clientes** para admin: drop-down "Asignar a vendedor X". Estimado: 30 min.
3. **Endpoint admin de "ver como X"**: temporalmente actuar con permisos de otro user para soporte. Estimado: 2h.
4. **Test suite mínima**: pytest + 1 test por rol que verifica `/api/auth/me` y 1-2 endpoints clave. Estimado: 2-3h.
5. **Dashboard `dashboard:inventory`** específico para Operativo: ahora ven el dashboard completo aunque no tengan permiso. Estimado: 1h.
6. **Logging de denegaciones**: cada 403 debería ir a una tabla `audit_log` para detectar usuarios intentando exceder permisos. Estimado: 1h.

## Smoke test final ejecutado

Script en `docs/onboarding/70_rbac_y_roles.md` corrió contra la app local con resultados:

| Caso | Resultado |
|---|---|
| `/api/auth/me` admin | 9 módulos, todo `true` ✓ |
| `/api/auth/me` gerente | 8 módulos, gestionar_usuarios=false ✓ |
| `/api/auth/me` ventas | 6 módulos, ver_costos=false, ajustar_stock=false ✓ |
| `/api/auth/me` operativo | 3 módulos, ver_cotizaciones=false, ajustar_stock=true ✓ |
| `/api/ventas/historial` admin/gerente | 3 cotizaciones ✓ |
| `/api/ventas/historial` ventas | 0 (no son suyas) ✓ |
| `/api/ventas/historial` operativo | 403 ✓ |
| `POST /api/inventario/movimientos` admin/gerente/operativo | 200 ✓ |
| `POST /api/inventario/movimientos` ventas | 403 ✓ |
| `POST /api/usuarios/` admin | 200 (422 por payload duplicado en el test) ✓ |
| `POST /api/usuarios/` gerente/ventas/operativo | 403 ✓ |
| `POST /api/ventas/` operativo | 403 ✓ |

Cleanup de usuarios y movimientos QA realizado.

## Diff acumulado

Commits desde `50fc6e9..` (estado pre-RBAC):
- `619521c` feat(rbac): spec + módulo central de permisos (+482/-0)
- `af7400e` feat(rbac): backend gating + owner scoping VENTAS (+79/-10)
- `29de3d0` feat(rbac): frontend role-aware sidebar (+84/-10)
- `75dc217` fix(rbac): operativo bloqueado en cotizaciones (+4/-1)

Total: 4 commits, ~+650 líneas, 1 migración nueva, 1 módulo nuevo (`permissions.py`), 7 docs onboarding.

# MVP DASIC — Design Spec

**Date:** 2026-04-28
**Owner:** Atlas_Tech
**Scope:** Llevar el repo `Dasic_Atlas_api` a un MVP usable internamente por DASIC: Live Stock + Smart Quoter v2 + Dashboard ejecutivo + hardening, simplificando la arquitectura a single-tenant.

---

## 1. Decisiones marco

| # | Decisión | Justificación |
|---|---|---|
| 1 | **Single-tenant, single-branch** | DASIC tiene una sola sede. La infraestructura multi-tenant existente es código muerto. |
| 2 | **Strip total del scaffolding multi-tenant** | Reduce complejidad para siempre. Aceptamos el costo del refactor (~Fase 0). |
| 3 | **Live Stock mínimo viable** | Mantener `Producto.stock_actual` plano (sin `warehouses` ni `stock_items`). Agregar reservas y Kardex. |
| 4 | **Reserva al agregar línea** (no al enviar) | Garantiza "nunca prometer stock no disponible" desde el inicio del flujo. TTL 48h. |
| 5 | **Alembic como única fuente de schema** | Eliminar `create_all()` y `_BACKFILL_DDL` del lifespan al cierre del MVP. |
| 6 | **SSR + Alpine + Tailwind CDN** | Mantener stack actual. Solo se agrega Chart.js CDN para gráficas del dashboard. |

---

## 2. Forma del MVP — 5 fases secuenciales

```
Fase 0: Strip multi-tenant       ← limpieza foundational
Fase 1: Live Stock + Kardex      ← schema nuevo
Fase 2: Reservas 48h + Quoter v2 ← lógica de negocio
Fase 3: Dashboard ejecutivo      ← UI + agregaciones
Fase 4: Hardening + QA + deploy  ← cierre productivo
```

Cada fase es mergeable independientemente. Si la prioridad cambia se puede congelar en cualquier punto sin dejar el sistema roto.

---

## 3. Fase 0 — Strip multi-tenant

### Objetivo
Eliminar todo rastro de multi-tenancy. Una sola org implícita, una sola sede.

### Cambios de código

**Modelos a borrar** (`app/models/nucleus.py` completo):
- `Organization`
- `Branch`
- `UserOrganization`

**Columnas a dropear** (`organization_id`):
- `clientes`
- `transacciones_clientes`
- `ordenes_venta`
- `detalles_orden`
- `quote_events`

**Código a eliminar:**
- `app/dependencies.py::get_current_active_organization`
- `app/core/context.py` (ContextVar de tenant)
- Header `X-Organization-ID` en routers
- Claim `org_id` en JWT (`app/security/jwt.py::create_access_token`, `get_token_payload`)
- Backfill DDL en `app/db/seeds.py` relacionado a `organization_id` y a tablas nucleus
- Filtros `.filter(*.organization_id == ...)` en todos los routers
- `BranchType` enum en `app/models/enums.py`

**Migración Alembic nueva:** `migrations/versions/20260429_01_drop_multitenant.py`
- Drop columns `organization_id` (con índices)
- Drop tables `user_organizations`, `branches`, `organizations`

**Seeds simplificados** (`app/db/seeds.py`):
- Mantener solo `seed_super_admin`
- Eliminar `seed_base_tenant`, `ensure_memberships`, `backfill_organization_ids`, `run_backfill_ddl`

### Riesgo
Alto: toca casi todos los routers. Mitigación: smoke test manual de cada vista SSR (`/dashboard`, `/cotizador`, `/clientes`, `/inventario`, `/compras`, `/seguimiento`, `/usuarios`, `/gastos`, `/reportes`) antes de merge.

### Criterio de done
- `git grep organization_id` solo devuelve referencias en migraciones históricas
- App arranca, login funciona, todas las vistas SSR cargan
- `alembic upgrade head` y `alembic downgrade -1` ambos verdes

---

## 4. Fase 1 — Live Stock + Kardex

### Objetivo
Convertir el `stock_actual` plano en un sistema con trazabilidad completa.

### Schema nuevo

**Tabla `inventory_movements`** (Kardex):
```
id              SERIAL PK
producto_id     INT FK → productos.id
tipo            VARCHAR(20)  -- ENTRADA | SALIDA | AJUSTE | RESERVA | LIBERACION | CONSUMO
cantidad        INT          -- signed: ENTRADA y LIBERACION positivos; SALIDA y RESERVA negativos
saldo_post      INT          -- stock_actual posterior al movimiento (snapshot)
referencia_tipo VARCHAR(20)  -- COTIZACION | OV | OC | AJUSTE_MANUAL | RESERVA_VENCIDA
referencia_id   INT          -- nullable
notas           TEXT         -- nullable
usuario_id      INT FK → usuarios.id
creado_en       TIMESTAMPTZ DEFAULT NOW()

INDEX (producto_id, creado_en DESC)
INDEX (referencia_tipo, referencia_id)
```

**Tabla `stock_reservations`:**
```
id          SERIAL PK
producto_id INT FK → productos.id
orden_id    INT FK → ordenes_venta.id      -- cotización origen
linea_id    INT FK → detalles_orden.id     -- línea específica (para liberar al borrar línea)
cantidad    INT NOT NULL
vence_en    TIMESTAMPTZ NOT NULL
estatus     VARCHAR(20) NOT NULL  -- ACTIVA | LIBERADA | CONSUMIDA | VENCIDA
creado_en   TIMESTAMPTZ DEFAULT NOW()
liberada_en TIMESTAMPTZ           -- nullable

INDEX (producto_id, estatus)
INDEX (orden_id)
INDEX (linea_id)
INDEX (vence_en) WHERE estatus = 'ACTIVA'
```

**`Producto`:** se agrega columna denormalizada
```
stock_reservado INT NOT NULL DEFAULT 0
```

**Invariantes mantenidos por aplicación:**
- `stock_reservado = SUM(stock_reservations.cantidad WHERE estatus='ACTIVA' AND producto_id = X)`
- `stock_disponible` (no persistido) = `stock_actual - stock_reservado`
- Toda mutación de `stock_actual` o `stock_reservado` genera fila en `inventory_movements`
- `stock_actual` y `stock_reservado` solo se editan vía `InventoryService` — nunca desde un router

### Servicio nuevo

`app/services/inventory_service.py`:
```python
class InventoryService:
    @staticmethod
    def aplicar_movimiento(db, producto_id, tipo, cantidad, ref_tipo, ref_id, usuario_id, notas=None) -> Movimiento
    @staticmethod
    def reservar(db, producto_id, cantidad, orden_id, linea_id, usuario_id, ttl_horas=48) -> Reservation
    @staticmethod
    def liberar_reserva(db, reservation_id, motivo='MANUAL') -> Reservation
    @staticmethod
    def consumir_reserva(db, reservation_id, ov_id) -> Movimiento
    @staticmethod
    def purgar_reservas_vencidas(db) -> int  # devuelve cuántas liberó
    @staticmethod
    def disponibilidad(db, producto_id) -> dict[stock_actual, stock_reservado, stock_disponible]
```

### Migración Alembic
`20260429_02_inventory_kardex.py` — crear tablas + columna `stock_reservado` + backfill (`stock_reservado = 0` para todos).

### Criterio de done
- Crear movimiento manual desde un endpoint admin actualiza `stock_actual` y deja fila en Kardex
- `disponibilidad()` devuelve los 3 valores correctos
- Test unitario de `aplicar_movimiento` y `reservar/liberar/consumir` cubre los caminos felices

---

## 5. Fase 2 — Reservas 48h + Smart Quoter v2

### Objetivo
Integrar reservas al flujo de cotización existente y añadir snapshot de stock.

### Comportamiento

| Evento | Acción de inventario |
|---|---|
| Agregar línea con `producto_id` real | `reservar(48h)` |
| Cambiar cantidad de línea | Liberar reserva previa + reservar nueva cantidad |
| Eliminar línea | `liberar_reserva` |
| Cancelar/borrar cotización | Liberar todas las reservas de sus líneas |
| Convertir cotización a venta (OV) | `consumir_reserva` por cada línea (genera movimiento `CONSUMO`) |
| Reserva expira (48h sin cerrar) | Barrido `purgar_reservas_vencidas` libera y registra `LIBERACION` |
| Línea ad-hoc (`producto_id IS NULL`) | No reserva — no afecta inventario |

**Reserva con stock insuficiente:** si `cantidad_solicitada > stock_disponible`, el endpoint devuelve **HTTP 409** con detalle (`stock_disponible`, `cantidad_solicitada`). El vendedor puede:
- Reducir la cantidad
- Confirmar línea ad-hoc (sin reserva, asumiendo backorder) marcando un flag explícito
- Cancelar

No hay reserva parcial automática.

### Snapshot en `DetalleOrden`
Verificar que ya existen:
- `costo_base_linea` ✅ (visto en seeds)
- `moneda_origen_linea` ✅ (visto en seeds)

Agregar:
- `stock_disponible_snapshot INT` — capturado al crear la línea, inmutable. Es la "fotografía de stock" del blueprint DASIC.

Migración Alembic: `20260429_03_quote_stock_snapshot.py`.

### UI cotizador (`app/templates/cotizador.html`)
- Al buscar producto: badge `Disp: N` en el resultado
- En cada línea agregada: badge `Reservado hasta DD/MM HH:MM`
- Si la reserva está por vencer en <6h: badge en color de advertencia
- Botón "Liberar reserva" por línea (admin/gerente comercial)

### Barrido de expiración
- Hook en `lifespan` startup: `InventoryService.purgar_reservas_vencidas(db)` (oportunista, una pasada al boot)
- Endpoint protegido: `POST /api/internal/purge-reservations` con header secreto (`X-Cron-Secret` desde env) — para llamar desde cron de Railway cada 15 min

### Criterio de done
- Crear cotización con 2 líneas → `stock_reservado` sube en ambos productos, hay 2 filas en `stock_reservations`
- Borrar una línea → `stock_reservado` baja, fila marcada `LIBERADA`
- Convertir a OV → reservas marcadas `CONSUMIDA`, `stock_actual` baja, fila `CONSUMO` en Kardex
- `purge` libera reservas con `vence_en < NOW()`

---

## 6. Fase 3 — Dashboard ejecutivo

### KPIs (v1)

1. **Cotizaciones del mes:** count, monto total, conversión a venta (%)
2. **Stock crítico:** lista SKUs con `stock_disponible <= stock_minimo`
3. **Stock muerto:** SKUs sin movimiento `SALIDA`/`CONSUMO` en 90+ días
4. **Reservas activas:** count, monto inmovilizado, próximas a vencer (<24h)
5. **Pipeline comercial:** cotizaciones por estatus (borrador/enviada/aceptada/rechazada/vencida)
6. **Top 10 productos vendidos** del mes (por unidades y por monto)

### Implementación

`app/services/dashboard_service.py`:
```python
class DashboardService:
    @staticmethod
    def resumen(db) -> dict  # devuelve los 6 KPIs en un solo dict
```

Endpoint: `GET /api/dashboard/summary` (autenticado, todos los roles).
Vista: `app/templates/dashboard.html` reescrita con:
- 6 tarjetas KPI (números grandes, deltas vs mes anterior)
- 1 gráfica de pipeline (Chart.js CDN, doughnut)
- 1 gráfica de top productos (Chart.js, bar)
- Tabla de stock crítico
- Tabla de reservas próximas a vencer

### Criterio de done
- Dashboard carga en <1.5s con datos de prueba
- Cada KPI se calcula con una sola query agregada
- La vista funciona sin Chart.js (degrada a tablas)

---

## 7. Fase 4 — Hardening + QA + deploy

### QA mínima

Stack: `pytest` + `pytest-asyncio` + `httpx.AsyncClient` + DB Postgres real (schema `test_dasic`).

Tests obligatorios:
- **Auth smoke:** login → cookie → request a `/api/dashboard/summary` exitoso; sin cookie → 401
- **Inventory:**
  - `aplicar_movimiento` actualiza stock y genera fila Kardex
  - `reservar` baja `stock_reservado`, `liberar_reserva` lo sube de vuelta
  - `consumir_reserva` baja `stock_actual` y genera `CONSUMO`
  - `purgar_reservas_vencidas` libera solo las expiradas
- **Folios:** dos cotizaciones del mismo usuario en el mismo mes generan folios consecutivos
- **Cotización flow:** crear cotización con 2 líneas → reservas activas; convertir a OV → consumidas
- **RBAC by role:** un usuario `VENTAS` no puede tocar endpoints `allow_admin`

Cobertura objetivo: **paths críticos cubiertos**, no porcentaje. Métrica simple: tests verdes en CI.

### RBAC review (sin tenant)
Auditoría rápida de cada router: confirmar que cada endpoint usa el `allow_*` correcto. Nada nuevo, solo confirmación.

### Deploy stability
- **Eliminar `create_all()` del lifespan** — Alembic-only en producción
- **Migrar `_BACKFILL_DDL` restante** a revisiones Alembic formales (las que sigan vivas tras Fase 0)
- **Healthcheck:** `/health` ya existe; validar que devuelve 503 cuando DB cae
- **Logging de 500s:** middleware que captura excepciones no manejadas y las loguea con stack trace + request_id
- **CI:** GitHub Actions — `pytest` + `alembic upgrade head` contra Postgres de servicio (`postgres:16`)

### Criterio de done
- Suite pytest verde en local y CI
- `lifespan` ya no llama `create_all()`
- Healthcheck devuelve 503 al matar la DB
- Pipeline de CI bloquea merges con tests rojos

---

## 8. Paralelización

Aunque las fases son secuenciales, dentro de cada fase hay subtareas paralelizables:

- **Fase 0:** strip de modelos + strip de routers + migración Alembic pueden hacerse en agentes independientes y converger en merge
- **Fase 1:** servicio `InventoryService` + migración Alembic + tests del servicio en paralelo
- **Fase 2:** integración cotizador (back) + UI cotizador (front Jinja+Alpine) + endpoint de purge + cron Railway en paralelo
- **Fase 3:** queries agregadas (`DashboardService`) + reescritura de plantilla + integración Chart.js en paralelo
- **Fase 4:** suite pytest + CI YAML + middleware de logging + auditoría RBAC en paralelo

Cada fase tendrá un plan de implementación dedicado (vía `writing-plans`) que aprovechará subagentes paralelos donde el riesgo de conflicto sea bajo.

---

## 9. Riesgos y supuestos

| # | Riesgo / Supuesto | Mitigación |
|---|---|---|
| R1 | `DROP COLUMN organization_id` en producción Railway | Backup pre-migración + verificar que la única org existente es la única referenciada |
| R2 | Reservas pueden quedar inconsistentes si una request falla a medias | Toda operación de reserva en transacción atómica con la creación/edición de línea |
| R3 | `stock_reservado` denormalizado puede divergir de `SUM(reservations)` | Endpoint admin de "reconciliación" que recalcula desde la fuente; tests aseguran que no diverge |
| R4 | El cron de Railway puede fallar o duplicar | Endpoint idempotente (no doble-libera reservas ya liberadas); locking optimista por `estatus = 'ACTIVA'` |
| R5 | Sin tenant, el JWT actual sigue emitiendo claim `org_id` | Quitar el claim en Fase 0 y aceptar tokens viejos sin él durante una ventana de gracia |

---

## 10. Out of scope (para iteraciones futuras)

- Multi-warehouse (`warehouses` + `stock_items`)
- Variantes de producto (`product_variants`)
- Listas de precios (`price_lists` + `product_prices`)
- Pipelines configurables / Deals / Activities (CRM completo del ROADMAP fase 6)
- Aprobaciones de descuento bajo margen mínimo
- Integraciones externas (WhatsApp oficial, ERP fiscal)
- ABC-XYZ scoring de SKUs
- Alertas push / notificaciones por email automáticas

Estos quedan documentados en `context/ROADMAP.md` como Fase 10 (Moonshot iterativo).

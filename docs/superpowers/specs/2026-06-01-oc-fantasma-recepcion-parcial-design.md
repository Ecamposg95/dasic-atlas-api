# US-026 / US-027 — Fantasma en OC + Recepción parcial — Design

**Fecha:** 2026-06-01
**Alcance:** US-026 (productos fantasma cotizados conservan desc/marca/SAT/costo/moneda en la OC) y US-027 (recepción parcial incremental de OC con cantidad_recibida/fecha).

## Contexto actual (auditado)

- `GET /api/compras/cotizacion/{quote_id}/grouping` (compras.py:367) **ya incluye** las líneas fantasma (`det.fantasma_id`) como candidatas, agrupándolas por proveedor. Es la ruta real que usa el cotizador.
- `POST /api/compras/cotizacion/{quote_id}/confirmar` (compras.py:453) **ya crea** `DetalleCompra` para líneas fantasma (`producto_id=NULL`, guarda `sku_libre`+`descripcion_libre`+`moneda_origen_linea`+`costo_base_linea`) y marca el fantasma `estado=EN_OC`. **Pero NO conserva marca ni claves SAT** (a `DetalleCompra` le faltan esas columnas).
- `POST /api/compras/{id}/recibir` (compras.py:807) hace ENTRADA por la cantidad **total** de cada línea con `producto_id`, salta fantasmas, marca OC `estatus="recibido"` (irreversible). No hay recepción parcial; `DetalleCompra` no tiene `cantidad_recibida` ni `fecha_recepcion`.
- `EstatusOC` en el frontend ya define `recibida_parcial` (sin uso). El `estatus` de `OrdenCompra` es string libre.
- `DetalleOrden` (cotización) ya tiene `fantasma_id`, `sku_libre`, `descripcion_libre`, `clave_prod_serv`, `clave_unidad_sat`, `marca` (EPIC 02).
- `aplicar_movimiento(db, *, producto, tipo, cantidad, referencia_tipo, referencia_id, motivo, usuario)` registra ENTRADA auditada.

## Decisiones de producto (acordadas)

1. **US-027: recepción incremental acumulativa.** La OC se recibe varias veces; cada recepción captura "cuánto llegó ahora" por línea; el sistema acumula `cantidad_recibida` y mueve ENTRADA **solo por el delta**. OC → `recibida_parcial` mientras falte algo; → `recibido` cuando todas las líneas se completan.
2. **Líneas fantasma en recepción: solo registran.** Acumulan `cantidad_recibida`/`fecha` (para trazabilidad y cierre de la OC) pero **NO mueven stock**. El stock entra al promover el fantasma (US-009, ya hecho). Mantiene el flujo desacoplado.

## Arquitectura

### 1. Modelo de datos (migración aditiva `20260601_04`)

`detalles_compra`:
- US-026: `marca VARCHAR(80) NULL`, `clave_prod_serv VARCHAR(8) NULL`, `clave_unidad_sat VARCHAR(10) NULL` (snapshot SAT/marca de la línea).
- US-027: `cantidad_recibida INTEGER NOT NULL DEFAULT 0`, `fecha_recepcion TIMESTAMPTZ NULL`.

Espejo obligatorio en `app/db/seeds.py::_BACKFILL_DDL`. Todo NULL/default → OCs existentes intactas.

`app/models/purchases.py::DetalleCompra` gana esas 5 columnas (imports: `Boolean` no; ya hay `DateTime`/`Integer`/`String`; `text` para el server_default de `cantidad_recibida`).

### 2. US-026 — conservar marca/SAT en la OC

- En `confirmar_ocs_desde_cotizacion` (compras.py:453), al construir cada `DetalleCompra`, copiar del `DetalleOrden`:
  `marca=det.marca`, `clave_prod_serv=det.clave_prod_serv`, `clave_unidad_sat=det.clave_unidad_sat` (aplica a líneas fantasma y de catálogo por igual; es snapshot por línea).
- `GET /api/compras/{id}` (detalle de OC) expone por línea `marca`, `clave_prod_serv`, `clave_unidad_sat` (además de los de recepción). El modal de detalle de OC los muestra como subtexto.

### 3. US-027 — recepción parcial incremental

**Helper** `_aplicar_recepcion(db, orden, deltas, fecha, usuario)` (en compras.py):
- `deltas`: dict `{detalle_compra_id: cantidad_que_llego_ahora}`.
- Por cada `DetalleCompra` de la OC con `delta > 0`:
  - Valida `cantidad_recibida + delta <= cantidad` (si no, 400).
  - Si `producto_id` no es NULL: `aplicar_movimiento(ENTRADA, delta, referencia_tipo="oc", referencia_id=orden.id, motivo="Recepción OC {folio}")`.
  - Si `producto_id` es NULL (fantasma): **no** mueve stock.
  - `det.cantidad_recibida += delta`; `det.fecha_recepcion = fecha or now()`.
- Recalcula estatus de la OC: si **todas** las líneas tienen `cantidad_recibida >= cantidad` → `"recibido"`; elif alguna tiene `cantidad_recibida > 0` → `"recibida_parcial"`; else sin cambio.
- Retorna `{ procesados, estatus }`.

**Endpoint** `POST /api/compras/{id}/recibir-parcial`:
- Body `RecepcionParcialInput { lineas: List[{detalle_compra_id: int, cantidad: int}], fecha: Optional[datetime] = None }`.
- Valida OC existe y `estatus in (borrador, enviada, confirmada, recibida_parcial)` (si ya `recibido` → 400).
- Construye `deltas` desde el body (ignora cantidad<=0), llama al helper, commit. Retorna `{ ok, folio, estatus, procesados }`.

**Refactor** `POST /api/compras/{id}/recibir` (total): construye `deltas = {det.id: det.cantidad - det.cantidad_recibida}` para líneas con pendiente > 0 y llama al mismo helper → "recibir todo lo pendiente", idempotente y sin doble conteo. Mantiene compatibilidad con el botón actual.

**Schema:** `RecepcionParcialInput` (+ línea anidada) en `app/schemas/purchases.py`, **re-exportada en `app/schemas/__init__.py`** (import + `__all__`) — ver [[feedback-schemas-reexport]].

### 4. Frontend (`web/src/features/compras/`)

- `types.ts`: `OrdenCompraLinea` += `cantidad_recibida: number`, `fecha_recepcion: string | null`, `marca?`, `clave_prod_serv?`, `clave_unidad_sat?`.
- `RegistrarRecepcionModal`: de checkbox a **tabla por línea**: columnas SKU/descripción, pedido, ya recibido, **recibir ahora** (input number, máx = `cantidad - cantidad_recibida`), + un date input para la fecha. Botón "Recibir todo lo pendiente" (pre-llena cada input con el pendiente). Submit → `POST /recibir-parcial`. Hook `useRecibirParcial`.
- `OrdenCompraDetalleModal`: muestra `cantidad_recibida / cantidad` por línea y marca/SAT como subtexto.
- Lista de OCs: badge para `recibida_parcial` (el tipo ya existe; agregar el color/label).

### 5. Cobertura de User Stories

| US | Criterio | Cómo se cubre |
|----|----------|---------------|
| US-026 | Fantasmas candidatos a OC | `/grouping` ya los incluye (existente). |
| US-026 | Seleccionables y vinculados | `/confirmar` ya crea DetalleCompra + marca EN_OC (existente). |
| US-026 | Conservan desc/marca/SAT/costo/moneda | desc/costo/moneda ya; **se agregan marca + claves SAT**. |
| US-027 | Marcar producto recibido | `recibir-parcial` por línea. |
| US-027 | Recibir → promover a stock | catálogo entra a stock; fantasma se promueve aparte (US-009). |
| US-027 | Fecha de llegada | `fecha_recepcion` por línea. |
| US-027 | Cantidad recibida | `cantidad_recibida` acumulativa. |
| US-027 | Actualiza inventario | ENTRADA por delta para líneas de catálogo. |

## Fuera de alcance (YAGNI)

- Auto-promover fantasma al recibir (se eligió manual — US-009).
- Incluir fantasmas en el `/borrador` legacy (la ruta real es `/grouping`, que ya los incluye).
- marca/SAT en el PDF de OC (`/imprimir`).
- Deshacer/revertir recepciones (cada recepción es acumulativa hacia adelante).
- Tocar el endpoint `/orden` (OC única) — su uso excluye fantasmas por diseño y no es la ruta canónica.

## Riesgos y verificación

- **Sin test suite** (CLAUDE.md): backend `python3 -m py_compile`; frontend `cd web && npm run build`. Manual post-deploy.
- **Migración aditiva** → bajo riesgo; requiere espejo en `_BACKFILL_DDL`.
- **Re-export de schema** nuevo en `__init__.py` (gotcha que ya causó un crash — [[feedback-schemas-reexport]]).
- **Sin doble conteo de stock:** el delta por recepción + la validación `cantidad_recibida + delta <= cantidad` garantizan que cada unidad entra a stock una sola vez; `/recibir` total reusa el mismo helper sobre el pendiente.
- **Stock auditado:** toda ENTRADA pasa por `aplicar_movimiento` (regla de inventario de CLAUDE.md).

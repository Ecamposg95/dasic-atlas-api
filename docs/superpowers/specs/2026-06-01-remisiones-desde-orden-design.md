# EPIC 06 — Remisiones desde Orden de Venta — Design

**Fecha:** 2026-06-01
**Alcance:** US-019, US-021, US-022, US-023, US-024 (US-020 folio `R-` ya existe).
**Objetivo:** Convertir el módulo de remisiones (hoy read-only: listar/ver/registrar recepción) en un flujo de creación con UI tipo cotizador, PDF imprimible y control de precios, reutilizando el snapshot de una orden de venta existente.

## Contexto actual (auditado)

- `Remision` (`app/models/remisiones.py`) tiene `orden_venta_id` **NOT NULL** → toda remisión nace de una orden.
- `crear_remision` (`app/routers/remisiones.py:90`) **rechaza órdenes en estatus `COTIZACION`**: la orden debe estar convertida a venta antes de remisionar. Este diseño respeta esa regla — la remisión nace de una **orden de venta**, no de una cotización en borrador.
- `_generar_folio_remision` ya produce `R-YYMM<NNNN>` con advisory lock (US-020 ✔).
- `DetalleRemision` guarda solo `descripcion`, `sku`, `cantidad`, `observaciones_linea` + FK `detalle_orden_id` (nullable). **No** guarda precios ni unidad SAT.
- **No existe** UI de creación (el botón "Nueva remisión" está deshabilitado) ni generador de PDF.
- Patrón de PDF de referencia: `compras.py::imprimir_oc` (`GET /{id}/imprimir`) devuelve `HTMLResponse` renderizado con Jinja `Environment(BaseLoader())` desde un template string. La remisión seguirá este patrón (HTML imprimible, no binario).

## Decisiones de producto (acordadas)

1. **Origen:** solo desde una orden de venta existente (se conserva `orden_venta_id` NOT NULL). No hay remisión standalone.
2. **Edición al armar:** pre-carga las líneas de la orden; el usuario puede ajustar cantidades (entrega parcial, default = cantidad de la orden), deseleccionar líneas, editar observaciones por línea, y **agregar líneas fantasma ad-hoc** no presentes en la orden (US-024).
3. **Precios:** toggle "mostrar precios" por remisión, **default OCULTO**. Los precios se snapshotean desde la orden por si se activan.
4. **PDF:** generador nuevo (HTML imprimible), cantidad muestra unidad SAT — "10 (H87)" (US-023).

## Arquitectura

### 1. Modelo de datos (migración aditiva `20260601_03`)

`remisiones`:
- `moneda VARCHAR(3) NULL` — snapshot de `orden.moneda` al crear.
- `mostrar_precios BOOLEAN NOT NULL DEFAULT FALSE`.

`detalles_remision`:
- `clave_unidad_sat VARCHAR(10) NULL` — para US-023 (cantidad + unidad en PDF).
- `precio_unitario DECIMAL(10,2) NULL` — snapshot del precio de venta de la línea.
- `subtotal DECIMAL(12,2) NULL` — `precio_unitario × cantidad_entregada`.

Las líneas fantasma ad-hoc usan `detalle_orden_id = NULL` (igual que hoy). Todas las columnas NULL/default → remisiones existentes intactas. **Espejo obligatorio en `app/db/seeds.py::_BACKFILL_DDL`** (Railway no corre Alembic).

### 2. Backend (`app/routers/remisiones.py`, `app/schemas/remisiones.py`)

**a) `GET /api/remisiones/orden/{orden_id}/borrador`** *(nuevo)*
Arma el draft desde la orden de venta para precargar la página de creación. Valida que la orden exista y no sea `COTIZACION`. Devuelve por cada `DetalleOrden`:
`{ detalle_orden_id, descripcion (descripcion_libre or producto.nombre), sku (sku_libre or producto.sku_comercial/sku), clave_unidad_sat (snapshot de línea or producto), precio_unitario, cantidad_orden }`
más `{ orden_folio, cliente_nombre, moneda }` a nivel cabecera.

**b) `POST /api/remisiones/` (extendido)**
Schema `DetalleRemisionInput` +`clave_unidad_sat`, `precio_unitario` (ambos opcionales, solo se usan para líneas ad-hoc). `RemisionCreate` +`mostrar_precios: bool = False`.
Al crear, por cada línea:
- Si `detalle_orden_id` viene: el **backend re-lee `DetalleOrden`** y copia descripcion/sku/clave_unidad_sat/precio_unitario desde ahí (server-authoritative — no confía en precios del cliente). `subtotal = precio_unitario × cantidad`. Valida `cantidad ≤ DetalleOrden.cantidad` (no se entrega más de lo vendido).
- Si es ad-hoc (`detalle_orden_id = None`): usa descripcion/sku/clave_unidad_sat/precio_unitario del payload; `subtotal = precio_unitario × cantidad` si hay precio.
Snapshotea `moneda = orden.moneda` y `mostrar_precios` en la remisión.

**c) `GET /api/remisiones/{id}/imprimir`** *(nuevo, `HTMLResponse`)*
Template Jinja (string + `BaseLoader`, patrón `compras.py`). Encabezado "REMISIÓN", folio `R-`, cliente, fecha, transportista. Tabla de líneas: `#`, descripción, **cantidad con unidad SAT** (`{{ cantidad }} ({{ clave_unidad_sat or 'PZA' }})` — US-023). Columnas precio unitario/subtotal y total **solo si `mostrar_precios`** (US-022). Observaciones al pie. Reusa el CSS/estructura del PDF de cotización para consistencia visual.

**d) `GET /api/remisiones/{id}`** (extendido): incluir `mostrar_precios`, `moneda`, y por línea `clave_unidad_sat`, `precio_unitario`, `subtotal`.

### 3. Frontend (`web/src/features/remisiones/`)

**a) `pages/CrearRemisionPage.tsx`** *(nuevo)* — ruta `/remisiones/nueva?orden=<id>`:
- Si no hay `?orden`, muestra un selector de órdenes de venta (estatus != cotización) — reusa un listado simple.
- Carga el borrador (`/orden/{orden_id}/borrador`), muestra banner con cliente/orden/moneda.
- Tabla de líneas: checkbox (incluir), descripción, `cantidad` editable (`max` = cantidad de la orden), observaciones por línea. Líneas deseleccionadas no se envían.
- Botón **"Agregar fantasma"**: reusa/adapta `AgregarFantasmaModal` del cotizador (descripción, sku, clave unidad SAT, cantidad, precio opcional) → agrega una línea ad-hoc (`detalle_orden_id: null`).
- Toggle **"Mostrar precios en PDF"** (default off).
- Campos transportista + observaciones generales.
- Botón "Generar remisión" → `POST /api/remisiones/` → navega a RemisionesPage o abre el PDF.

**b) `pages/RemisionesPage.tsx`** *(modificado)*:
- Habilitar "Nueva remisión" → abre selector de orden o navega a `/remisiones/nueva`.
- Botón **"PDF"** por fila → abre `/api/remisiones/{id}/imprimir` en pestaña nueva.
- `types.ts`: extender los tipos con los campos nuevos.

**c) Routing:** registrar la ruta protegida nueva (`router.tsx` + handler `_serve_spa_protected` en `app/main.py` para `/remisiones/nueva`, siguiendo el patrón de las demás rutas SPA).

### 4. Cobertura de User Stories

| US | Cómo se cubre |
|----|---------------|
| US-019 | `CrearRemisionPage` con selector de orden, líneas, fantasma, cantidades, observaciones (layout tipo cotizador). |
| US-020 | Folio `R-YYMM<NNNN>` (ya existe). |
| US-021 | `GET /{id}/imprimir` + botón PDF. |
| US-022 | `mostrar_precios` toggle, default oculto; render condicional en PDF. |
| US-023 | `clave_unidad_sat` snapshot por línea; PDF muestra "cantidad (unidad)". |
| US-024 | Botón "Agregar fantasma" inserta línea ad-hoc (`detalle_orden_id: null`). |

## Fuera de alcance (YAGNI)

- Remisión standalone sin orden de venta.
- Upsert del fantasma agregado en remisión al pool de fantasmas (la remisión no es documento de compra; el fantasma ad-hoc solo vive en la remisión).
- Edición de una remisión ya creada (hoy tampoco existe; la recepción ya tiene su flujo).
- Marca en el PDF de remisión (no solicitada).
- Movimientos de stock al remisionar (fuera de EPIC 06; la salida de inventario ocurre en el flujo de venta/recepción de OC).

## Riesgos y verificación

- **Sin test suite** (CLAUDE.md): validar backend con `python3 -m py_compile`, frontend con `cd web && npm run build`. Checks manuales en navegador recomendados post-deploy (crear remisión parcial, agregar fantasma, generar PDF con/sin precios).
- **Migración:** aditiva, todas NULL/default → bajo riesgo; requiere espejo en `_BACKFILL_DDL`.
- **Precios server-authoritative:** el backend ignora precios del cliente para líneas de orden (los re-lee de `DetalleOrden`), evitando manipulación.
- **Validación de cantidad:** `cantidad ≤ DetalleOrden.cantidad` evita remisionar de más.

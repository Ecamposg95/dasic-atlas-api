# Spec (a) — Campos SAT en producto y fantasma + captura + PDFs

**Fecha:** 2026-06-01
**EPIC:** 02 — Productos y Productos Fantasma
**User stories cubiertas:** US-005, US-006, US-008, y la *homologación de campos* de US-007.
**Fuera de alcance (Spec b):** US-009 — promoción de fantasma a producto real / stock, atada a recepción de OC.

## Objetivo

Homologar productos normales y productos fantasma para que ambos lleven los
mismos campos fiscales SAT (CFDI 4.0) y de identificación (marca, observaciones),
que esos campos se capturen desde el cotizador y desde el catálogo, y que viajen
hasta los PDFs de cotización y remisión.

## Estado actual relevante (descubierto en investigación)

- `Producto` (`app/models/catalog.py`) **ya tiene** `clave_prod_serv` (VARCHAR 8)
  y `clave_unidad_sat` (VARCHAR 10), incluidos en `schemas/catalog.py`
  (Create/Update/Response). → US-005/006 a nivel BD/API ya existen; falta solo
  exponerlos en el frontend de inventario.
- `ProductoFantasma` (`app/models/fantasmas.py`) tiene descripción, sku_libre,
  costo_referencia, moneda_referencia, proveedor_sugerido, estado,
  promovido_a_producto_id, veces_solicitado. **Le faltan** marca, SAT y
  observaciones.
- `DetalleOrden` (`app/models/sales.py`) ya usa snapshots de línea para fantasmas
  (`sku_libre`, `descripcion_libre`, `moneda_origen_linea`, `costo_base_linea`,
  `observaciones_linea`, `fantasma_id`). Patrón establecido para agregar SAT.
- El upsert del pool de fantasmas vive en
  `app/services/fantasmas_service.py::upsert_from_detalle`.
- El PDF de cotización es un template Jinja embebido en `app/routers/ventas.py`
  (~líneas 439-474, itera `items_list`). El PDF de remisión vive en
  `app/routers/remisiones.py`.

## Decisiones de diseño (confirmadas con el usuario)

1. **Marca en fantasma:** ambos `marca` (texto) + `marca_id` (FK), igual que
   `Producto` (gana `marca_id` cuando ambos vienen).
2. **PDFs:** incluir clave SAT y clave unidad SAT en los PDFs de cotización y
   remisión en este EPIC (no diferir).
3. **Snapshot vs join:** las claves SAT se guardan como **snapshot en
   `DetalleOrden`** (2 columnas nuevas), no se resuelven por join en el render.
   Razón: las cotizaciones son documentos históricos; el PDF queda estable
   aunque el producto/fantasma cambie después. Coherente con
   `sku_libre`/`descripcion_libre`.
4. **Estructura:** este es el Spec (a). US-009 es el Spec (b) independiente.

## 1. Cambios de modelo de datos

Una sola migración Alembic + entrada paralela en
`app/db/seeds.py::_BACKFILL_DDL` (Railway no corre alembic — `Procfile` solo
levanta uvicorn; toda migración nueva requiere su `ALTER TABLE ... ADD COLUMN
IF NOT EXISTS` espejo).

**`productos_fantasma`** (+5 columnas, todas NULL):

| Columna | Tipo | Notas |
|---|---|---|
| `marca` | VARCHAR(80) NULL | texto libre, espejo de `Producto.marca` |
| `marca_id` | INT NULL FK `marcas(id)` ON DELETE SET NULL | canónico; gana sobre texto |
| `clave_prod_serv` | VARCHAR(8) NULL | clave producto/servicio SAT |
| `clave_unidad_sat` | VARCHAR(10) NULL | clave unidad SAT |
| `observaciones` | TEXT NULL | notas libres |

**`detalles_orden`** (+2 columnas, snapshot de línea, NULL):

| Columna | Tipo | Notas |
|---|---|---|
| `clave_prod_serv` | VARCHAR(8) NULL | snapshot al guardar la cotización |
| `clave_unidad_sat` | VARCHAR(10) NULL | snapshot al guardar la cotización |

**`productos`:** sin cambios (ya tiene ambos campos SAT).

Todas las columnas son NULL ⇒ filas existentes intactas (US-005 criterio
"validar que no afecte productos existentes"; US-007).

## 2. Backend

- **`app/schemas/fantasmas.py`:** `ProductoFantasmaBase`, `...Update`,
  `...Response` + `marca`, `marca_id`, `clave_prod_serv`, `clave_unidad_sat`,
  `observaciones`. La Response resuelve el nombre de marca desde `marca_rel`
  (autocompletar `marca` desde la FK, fallback al texto), igual que Producto.
- **`app/models/fantasmas.py`:** agregar las 5 columnas + relationship
  `marca_rel` a `Marca`.
- **`app/routers/fantasmas.py`:** `_serialize_fantasma_row` expone los 5 campos;
  `actualizar_fantasma` (PATCH) los acepta y persiste (resolviendo marca_id↔marca
  igual que el endpoint de productos).
- **`app/services/fantasmas_service.py::upsert_from_detalle`:** nuevos parámetros
  `marca`, `marca_id`, `clave_prod_serv`, `clave_unidad_sat`, `observaciones`;
  se setean al crear y se completan al actualizar si están vacíos (no pisar lo
  ya capturado, salvo costo que sí se refresca como hoy).
- **`app/models/sales.py`:** `DetalleOrden` + `clave_prod_serv`,
  `clave_unidad_sat`.
- **`app/schemas/sales.py`:** el schema de línea (creación de cotización) acepta
  `marca`, `clave_prod_serv`, `clave_unidad_sat`, `observaciones` para líneas
  fantasma.
- **`app/routers/ventas.py` (guardar/actualizar cotización):** al construir cada
  `DetalleOrden`, poblar el snapshot SAT:
  - línea **catálogo** (`producto_id` no-null) → copiar `producto.clave_prod_serv`
    y `producto.clave_unidad_sat`.
  - línea **fantasma** → de los campos capturados en el modal (payload de línea).
  - línea **servicio** → NULL (sin SAT por ahora).
  Y pasar marca/marca_id/SAT/observaciones a `upsert_from_detalle`.

## 3. Frontend

**Inventario (US-005/006):**
- `web/src/features/inventario/types.ts`: agregar `clave_prod_serv`,
  `clave_unidad_sat` (ya vienen en la API response).
- `ProductoFormModal.tsx`: sección "SAT (CFDI)" con 2 inputs
  (Clave producto/servicio SAT, Clave unidad SAT), opcionales.
- `InventarioPage.tsx`: columna SAT en la tabla (mínimo `clave_prod_serv`;
  `clave_unidad_sat` como subtexto/columna compacta).

**Cotizador fantasma (US-008):**
- `AgregarFantasmaModal.tsx`: inputs Clave SAT + Clave unidad SAT + Marca +
  Observaciones (homologación con producto).
- `store.ts` / `types.ts` (cotizador): la línea del cart lleva `claveProdServ`,
  `claveUnidadSat`, `marca`, `observaciones`.
- `lib/serialize.ts`: incluir esos campos en el payload de `DetalleOrden`.

**FantasmasPage (US-007 display):**
- Mostrar marca / clave SAT / clave unidad / observaciones (en tabla o panel de
  detalle), editables vía el PATCH existente.

## 4. PDFs

- **Cotización** (template Jinja en `app/routers/ventas.py` ~439): renderizar
  clave SAT / clave unidad desde el snapshot de línea
  (`item.clave_prod_serv` / `item.clave_unidad_sat`), fallback a
  `item.producto.clave_*` para líneas de catálogo antiguas sin snapshot.
- **Remisión** (`app/routers/remisiones.py`): idem.
- Presentación: subtexto bajo el SKU/descr o columna compacta — definir en el
  plan de implementación según el ancho disponible del template.

## 5. Riesgos y mitigaciones

- **No romper existentes:** todas las columnas NULL; sin backfill de datos.
- **Borrado de marca:** `marca_id` FK ON DELETE SET NULL.
- **Documentos históricos:** snapshot en `DetalleOrden` mantiene PDFs estables.
- **Railway sin alembic:** entrada espejo obligatoria en `_BACKFILL_DDL`.
- **Líneas de catálogo antiguas sin snapshot:** el PDF cae a `producto.clave_*`.

## 6. Criterios de aceptación cubiertos

- US-005: campo Clave SAT en tabla + form de productos, guardado en BD, sin
  afectar existentes. (BD/API ya existían; este spec agrega frontend.)
- US-006: campo Clave unidad SAT en tabla + form, capturable en fantasma,
  usable en PDFs.
- US-007 (campos): fantasma con descripción, marca, clave SAT, clave unidad,
  costo, moneda origen, observaciones; aparece en cotizaciones y remisiones.
  (La conversión a producto real es US-009 / Spec b.)
- US-008: modal de fantasma con clave SAT + clave unidad; se guardan; se muestran
  en PDF de cotización y remisión.

## 7. Verificación

- `python -m py_compile` sobre los módulos backend tocados (no hay test suite).
- `cd web && npm run build` (tsc + vite) para el frontend.
- Verificación manual recomendada en navegador (no disponible en este entorno:
  runtime local bloqueado sin DB).

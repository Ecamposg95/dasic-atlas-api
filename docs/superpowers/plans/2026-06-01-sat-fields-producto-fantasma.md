# Campos SAT en producto y fantasma + captura + PDFs — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Homologar productos y productos fantasma con campos SAT (clave producto/servicio + clave unidad), marca y observaciones, capturables desde catálogo y cotizador, y visibles en los PDFs de cotización y remisión.

**Architecture:** Una migración agrega 5 columnas a `productos_fantasma` y 2 (snapshot SAT) a `detalles_orden` (`productos` ya tiene SAT). El backend expone/persiste los campos en schemas, el service de upsert y el guardado de cotización. El frontend los captura en el form de inventario y en el modal de fantasma, y los muestra en FantasmasPage. Los PDFs renderizan el SAT desde el snapshot de línea con fallback al producto.

**Tech Stack:** FastAPI + SQLAlchemy 2.x + Alembic + psycopg (Postgres); React 18 + Vite + TS + Tailwind + TanStack Query + Zustand.

**Verificación (este repo NO tiene suite de tests — CLAUDE.md):** backend con `python -m py_compile <archivos>`; frontend con `cd web && npm run build` (corre `tsc -b` + vite). Checks manuales en navegador quedan recomendados (runtime local bloqueado). Cada migración nueva requiere su espejo en `app/db/seeds.py::_BACKFILL_DDL` porque el `Procfile` de Railway no corre alembic.

---

## Fase 1 — Modelo de datos

### Task 1: Migración Alembic + espejo en _BACKFILL_DDL

**Files:**
- Create: `migrations/versions/20260601_01_sat_homologacion_fantasma.py`
- Modify: `app/db/seeds.py` (lista `_BACKFILL_DDL`, ~línea 189)

- [ ] **Step 1: Crear la migración**

```python
"""sat_homologacion_fantasma — homologa fantasma con producto (marca + SAT + obs)
y agrega snapshot SAT a la línea de cotización para PDFs.

Todas las columnas son NULL → filas existentes intactas. marca_id usa
ON DELETE SET NULL para que borrar una marca no rompa fantasmas.

Revision ID: 20260601_01
Revises: 20260526_01
Create Date: 2026-06-01
"""
from alembic import op
import sqlalchemy as sa

revision = "20260601_01"
down_revision = "20260526_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # productos_fantasma: homologación con producto
    op.add_column("productos_fantasma", sa.Column("marca", sa.String(80), nullable=True))
    op.add_column("productos_fantasma", sa.Column("marca_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_productos_fantasma_marca_id", "productos_fantasma", "marcas",
        ["marca_id"], ["id"], ondelete="SET NULL",
    )
    op.add_column("productos_fantasma", sa.Column("clave_prod_serv", sa.String(8), nullable=True))
    op.add_column("productos_fantasma", sa.Column("clave_unidad_sat", sa.String(10), nullable=True))
    op.add_column("productos_fantasma", sa.Column("observaciones", sa.Text(), nullable=True))
    # detalles_orden: snapshot SAT por línea (para PDFs estables)
    op.add_column("detalles_orden", sa.Column("clave_prod_serv", sa.String(8), nullable=True))
    op.add_column("detalles_orden", sa.Column("clave_unidad_sat", sa.String(10), nullable=True))


def downgrade() -> None:
    op.drop_column("detalles_orden", "clave_unidad_sat")
    op.drop_column("detalles_orden", "clave_prod_serv")
    op.drop_column("productos_fantasma", "observaciones")
    op.drop_column("productos_fantasma", "clave_unidad_sat")
    op.drop_column("productos_fantasma", "clave_prod_serv")
    op.drop_constraint("fk_productos_fantasma_marca_id", "productos_fantasma", type_="foreignkey")
    op.drop_column("productos_fantasma", "marca_id")
    op.drop_column("productos_fantasma", "marca")
```

- [ ] **Step 2: Agregar el espejo en `_BACKFILL_DDL`**

En `app/db/seeds.py`, dentro de la lista `_BACKFILL_DDL`, añadir (al final del bloque, antes del cierre `]`):

```python
    # EPIC 02 / Spec (a) — homologación fantasma + snapshot SAT en línea
    "ALTER TABLE IF EXISTS productos_fantasma ADD COLUMN IF NOT EXISTS marca VARCHAR(80)",
    "ALTER TABLE IF EXISTS productos_fantasma ADD COLUMN IF NOT EXISTS marca_id INTEGER REFERENCES marcas(id) ON DELETE SET NULL",
    "ALTER TABLE IF EXISTS productos_fantasma ADD COLUMN IF NOT EXISTS clave_prod_serv VARCHAR(8)",
    "ALTER TABLE IF EXISTS productos_fantasma ADD COLUMN IF NOT EXISTS clave_unidad_sat VARCHAR(10)",
    "ALTER TABLE IF EXISTS productos_fantasma ADD COLUMN IF NOT EXISTS observaciones TEXT",
    "ALTER TABLE IF EXISTS detalles_orden ADD COLUMN IF NOT EXISTS clave_prod_serv VARCHAR(8)",
    "ALTER TABLE IF EXISTS detalles_orden ADD COLUMN IF NOT EXISTS clave_unidad_sat VARCHAR(10)",
```

- [ ] **Step 3: Verificar**

Run: `python -m py_compile migrations/versions/20260601_01_sat_homologacion_fantasma.py app/db/seeds.py`
Expected: sin salida (OK).

- [ ] **Step 4: Commit**

```bash
git add migrations/versions/20260601_01_sat_homologacion_fantasma.py app/db/seeds.py
git commit -m "feat(db): columnas SAT/marca/obs en fantasma + snapshot SAT en línea (US-005..008)"
```

### Task 2: Columnas en los modelos ORM

**Files:**
- Modify: `app/models/fantasmas.py`
- Modify: `app/models/sales.py` (clase `DetalleOrden`)

- [ ] **Step 1: `ProductoFantasma` (app/models/fantasmas.py)**

Agregar después de `sku_libre` (col) y antes de `costo_referencia`:

```python
    marca = Column(String(80), nullable=True)
    marca_id = Column(Integer, ForeignKey("marcas.id", ondelete="SET NULL"), nullable=True, index=True)
    clave_prod_serv = Column(String(8), nullable=True)
    clave_unidad_sat = Column(String(10), nullable=True)
    observaciones = Column(Text, nullable=True)
```

Y en las relationships (junto a `proveedor_sugerido`):

```python
    marca_rel = relationship("Marca", foreign_keys=[marca_id])
```

Asegurar que `Text` esté importado (el import ya trae `Text` — verificar la línea `from sqlalchemy import ...`; agregar `Text` si falta).

- [ ] **Step 2: `DetalleOrden` (app/models/sales.py)**

Agregar junto a los snapshots de línea existentes (cerca de `moneda_origen_linea`/`costo_base_linea`):

```python
    # Snapshot SAT por línea (US-006/008): se copia al guardar la cotización,
    # de Producto para catálogo y del modal para fantasma. Los PDFs renderizan
    # desde aquí para quedar estables ante cambios posteriores del catálogo.
    clave_prod_serv = Column(String(8), nullable=True)
    clave_unidad_sat = Column(String(10), nullable=True)
```

- [ ] **Step 3: Verificar**

Run: `python -m py_compile app/models/fantasmas.py app/models/sales.py`
Expected: sin salida (OK).

- [ ] **Step 4: Commit**

```bash
git add app/models/fantasmas.py app/models/sales.py
git commit -m "feat(models): SAT/marca/obs en ProductoFantasma + snapshot SAT en DetalleOrden"
```

---

## Fase 2 — Backend: schemas, service, routers

### Task 3: Schemas de fantasma

**Files:**
- Modify: `app/schemas/fantasmas.py`

- [ ] **Step 1: Extender Base/Update/Response**

```python
class ProductoFantasmaBase(BaseModel):
    descripcion_original: str
    sku_libre: Optional[str] = None
    costo_referencia: Decimal
    moneda_referencia: str = "MXN"
    proveedor_sugerido_id: Optional[int] = None
    marca: Optional[str] = None
    marca_id: Optional[int] = None
    clave_prod_serv: Optional[str] = Field(None, max_length=8)
    clave_unidad_sat: Optional[str] = Field(None, max_length=10)
    observaciones: Optional[str] = None


class ProductoFantasmaResponse(ProductoFantasmaBase):
    id: int
    descripcion_normalizada: str
    estado: str
    promovido_a_producto_id: Optional[int] = None
    veces_solicitado: int
    creado_en: datetime
    ultimo_visto_en: datetime

    class Config:
        from_attributes = True


class ProductoFantasmaUpdate(BaseModel):
    descripcion_original: Optional[str] = None
    sku_libre: Optional[str] = None
    costo_referencia: Optional[Decimal] = None
    moneda_referencia: Optional[str] = None
    proveedor_sugerido_id: Optional[int] = None
    marca: Optional[str] = None
    marca_id: Optional[int] = None
    clave_prod_serv: Optional[str] = Field(None, max_length=8)
    clave_unidad_sat: Optional[str] = Field(None, max_length=10)
    observaciones: Optional[str] = None
```

Agregar `Field` al import de pydantic: `from pydantic import BaseModel, Field`.

- [ ] **Step 2: Verificar**

Run: `python -m py_compile app/schemas/fantasmas.py`
Expected: sin salida (OK).

- [ ] **Step 3: Commit**

```bash
git add app/schemas/fantasmas.py
git commit -m "feat(schemas): campos SAT/marca/obs en schemas de fantasma"
```

### Task 4: Service de upsert

**Files:**
- Modify: `app/services/fantasmas_service.py`

- [ ] **Step 1: Extender `upsert_from_detalle`**

Reemplazar la firma y cuerpo para aceptar y persistir los nuevos campos (sin pisar lo ya capturado al actualizar, salvo costo que se refresca como hoy):

```python
def upsert_from_detalle(
    db: Session,
    *,
    descripcion: str,
    sku_libre: Optional[str],
    costo: Decimal,
    moneda: str,
    proveedor_sugerido_id: Optional[int],
    marca: Optional[str] = None,
    marca_id: Optional[int] = None,
    clave_prod_serv: Optional[str] = None,
    clave_unidad_sat: Optional[str] = None,
    observaciones: Optional[str] = None,
) -> Optional[int]:
    desc_norm = _normalizar(descripcion)
    if not desc_norm or not costo or Decimal(costo) <= 0:
        return None

    moneda = (moneda or "MXN").upper()

    existente = (
        db.query(models.ProductoFantasma)
        .filter(
            models.ProductoFantasma.descripcion_normalizada == desc_norm,
            models.ProductoFantasma.moneda_referencia == moneda,
        )
        .first()
    )

    if existente:
        existente.veces_solicitado = (existente.veces_solicitado or 0) + 1
        existente.costo_referencia = Decimal(costo)
        if sku_libre and not existente.sku_libre:
            existente.sku_libre = sku_libre
        if proveedor_sugerido_id and not existente.proveedor_sugerido_id:
            existente.proveedor_sugerido_id = proveedor_sugerido_id
        if marca and not existente.marca:
            existente.marca = marca
        if marca_id and not existente.marca_id:
            existente.marca_id = marca_id
        if clave_prod_serv and not existente.clave_prod_serv:
            existente.clave_prod_serv = clave_prod_serv
        if clave_unidad_sat and not existente.clave_unidad_sat:
            existente.clave_unidad_sat = clave_unidad_sat
        if observaciones and not existente.observaciones:
            existente.observaciones = observaciones
        db.flush()
        return existente.id

    nuevo = models.ProductoFantasma(
        descripcion_normalizada=desc_norm,
        descripcion_original=descripcion.strip(),
        sku_libre=sku_libre or None,
        costo_referencia=Decimal(costo),
        moneda_referencia=moneda,
        proveedor_sugerido_id=proveedor_sugerido_id,
        marca=marca or None,
        marca_id=marca_id,
        clave_prod_serv=clave_prod_serv or None,
        clave_unidad_sat=clave_unidad_sat or None,
        observaciones=observaciones or None,
        estado="PENDIENTE",
        veces_solicitado=1,
    )
    db.add(nuevo)
    db.flush()
    return nuevo.id
```

- [ ] **Step 2: Verificar**

Run: `python -m py_compile app/services/fantasmas_service.py`
Expected: sin salida (OK).

- [ ] **Step 3: Commit**

```bash
git add app/services/fantasmas_service.py
git commit -m "feat(service): upsert de fantasma persiste marca/SAT/observaciones (US-008)"
```

### Task 5: Router de fantasmas (serializar + PATCH)

**Files:**
- Modify: `app/routers/fantasmas.py`

- [ ] **Step 1: Exponer los campos en `_serialize_fantasma_row`**

Dentro del dict que retorna, agregar (resolviendo nombre de marca desde la FK con fallback al texto):

```python
    try:
        marca_nombre = f.marca_rel.nombre if f.marca_id and f.marca_rel else (f.marca or None)
    except Exception:  # noqa: BLE001
        marca_nombre = f.marca or None
```

y en el `return {...}`:

```python
        "marca": marca_nombre,
        "marca_id": f.marca_id,
        "clave_prod_serv": f.clave_prod_serv,
        "clave_unidad_sat": f.clave_unidad_sat,
        "observaciones": f.observaciones,
```

- [ ] **Step 2: Aceptar los campos en `actualizar_fantasma` (PATCH)**

Dentro del bloque `try:` (junto a los `if payload.X is not None:`), agregar:

```python
        if payload.marca is not None:
            f.marca = payload.marca or None
        if payload.marca_id is not None:
            f.marca_id = payload.marca_id
        if payload.clave_prod_serv is not None:
            f.clave_prod_serv = payload.clave_prod_serv or None
        if payload.clave_unidad_sat is not None:
            f.clave_unidad_sat = payload.clave_unidad_sat or None
        if payload.observaciones is not None:
            f.observaciones = payload.observaciones or None
```

- [ ] **Step 3: Verificar**

Run: `python -m py_compile app/routers/fantasmas.py`
Expected: sin salida (OK).

- [ ] **Step 4: Commit**

```bash
git add app/routers/fantasmas.py
git commit -m "feat(api): fantasmas expone y edita marca/SAT/observaciones (US-007)"
```

### Task 6: Línea de cotización — schema de entrada + snapshot SAT al guardar

**Files:**
- Modify: `app/schemas/sales.py` (schema de creación de línea)
- Modify: `app/routers/ventas.py` (construcción de `DetalleOrden` + llamada a `upsert_from_detalle`)

- [ ] **Step 1: Schema de línea acepta campos fantasma**

En `app/schemas/sales.py`, localizar el schema de la línea de detalle usado al crear/actualizar cotización (el que ya tiene `sku_libre`, `descripcion_libre`, `proveedor_sugerido_id`). Agregar como opcionales:

```python
    marca: Optional[str] = None
    marca_id: Optional[int] = None
    clave_prod_serv: Optional[str] = Field(None, max_length=8)
    clave_unidad_sat: Optional[str] = Field(None, max_length=10)
    observaciones: Optional[str] = None
```

(Verificar que `Field` esté importado en ese módulo.)

- [ ] **Step 2: Poblar snapshot SAT al construir `DetalleOrden`**

En `app/routers/ventas.py`, localizar donde se crea cada `DetalleOrden(...)` al guardar/actualizar la cotización. Para cada línea, calcular el snapshot SAT antes de construir el detalle:

```python
        # Snapshot SAT por línea (US-006/008): catálogo copia de Producto;
        # fantasma usa lo capturado en el modal; servicio queda sin SAT.
        if producto is not None:
            _clave_prod = producto.clave_prod_serv
            _clave_unidad = producto.clave_unidad_sat
        else:
            _clave_prod = getattr(item, "clave_prod_serv", None)
            _clave_unidad = getattr(item, "clave_unidad_sat", None)
```

y pasarlos al constructor del detalle:

```python
            clave_prod_serv=_clave_prod,
            clave_unidad_sat=_clave_unidad,
```

- [ ] **Step 3: Pasar campos al upsert del fantasma**

En la misma función, donde se llama a `fantasmas_service.upsert_from_detalle(...)` para líneas fantasma, agregar los argumentos:

```python
            marca=getattr(item, "marca", None),
            marca_id=getattr(item, "marca_id", None),
            clave_prod_serv=getattr(item, "clave_prod_serv", None),
            clave_unidad_sat=getattr(item, "clave_unidad_sat", None),
            observaciones=getattr(item, "observaciones", None),
```

- [ ] **Step 4: Verificar**

Run: `python -m py_compile app/schemas/sales.py app/routers/ventas.py`
Expected: sin salida (OK).

- [ ] **Step 5: Commit**

```bash
git add app/schemas/sales.py app/routers/ventas.py
git commit -m "feat(api): snapshot SAT en línea + threading al upsert de fantasma (US-008)"
```

---

## Fase 3 — Frontend: inventario (US-005/006)

### Task 7: Tipos + form de producto

**Files:**
- Modify: `web/src/features/inventario/types.ts`
- Modify: `web/src/features/inventario/components/ProductoFormModal.tsx`

- [ ] **Step 1: Tipos**

En `types.ts`, agregar al tipo de Producto (y al payload de create/update si existen tipos separados):

```ts
  clave_prod_serv?: string | null;
  clave_unidad_sat?: string | null;
```

- [ ] **Step 2: Inputs en el form**

En `ProductoFormModal.tsx`, leer el archivo para seguir el patrón de campos existente (state + Input + binding al payload). Agregar dos inputs en una sección "SAT (CFDI)" (opcionales):

```tsx
{/* SAT (CFDI 4.0) — opcionales hasta facturar */}
<div className="grid grid-cols-2 gap-3">
  <div>
    <label className="block text-[11px] uppercase tracking-wider text-slate-400 mb-1">Clave producto/servicio SAT</label>
    <Input value={claveProdServ} onChange={(e) => setClaveProdServ(e.target.value)} maxLength={8} placeholder="Ej. 31181701" className="h-8 text-xs font-mono" />
  </div>
  <div>
    <label className="block text-[11px] uppercase tracking-wider text-slate-400 mb-1">Clave unidad SAT</label>
    <Input value={claveUnidadSat} onChange={(e) => setClaveUnidadSat(e.target.value)} maxLength={10} placeholder="Ej. H87" className="h-8 text-xs font-mono" />
  </div>
</div>
```

Añadir el state correspondiente (`useState`), inicializarlo desde el producto en edición, e incluir `clave_prod_serv`/`clave_unidad_sat` en el payload que se manda a la mutación de create/update.

- [ ] **Step 3: Verificar**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores TS.

- [ ] **Step 4: Commit**

```bash
git add web/src/features/inventario/types.ts web/src/features/inventario/components/ProductoFormModal.tsx
git commit -m "feat(inventario): captura clave SAT y clave unidad SAT en form de producto (US-005/006)"
```

### Task 8: Columna SAT en la tabla de inventario

**Files:**
- Modify: `web/src/features/inventario/pages/InventarioPage.tsx`

- [ ] **Step 1: Mostrar SAT**

Leer `InventarioPage.tsx` para identificar la tabla/columnas. Agregar una columna "SAT" que muestre `clave_prod_serv` (con `clave_unidad_sat` como subtexto), siguiendo el patrón de columnas existente. Para filas sin clave, mostrar `—` en `text-slate-600`.

- [ ] **Step 2: Verificar**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores TS.

- [ ] **Step 3: Commit**

```bash
git add web/src/features/inventario/pages/InventarioPage.tsx
git commit -m "feat(inventario): columna SAT en la tabla de productos (US-005/006)"
```

---

## Fase 4 — Frontend: cotizador fantasma (US-008)

### Task 9: Tipos + store del cotizador

**Files:**
- Modify: `web/src/features/cotizador/types.ts`
- Modify: `web/src/features/cotizador/store.ts` (`addLineaAdhoc` y el tipo de `CartItem`)

- [ ] **Step 1: Extender el tipo de línea**

En `types.ts`, agregar al `CartItem` (y al tipo del argumento de `addLineaAdhoc`). **Usar snake_case** para alinear con la convención de campos ad-hoc existentes (`sku_libre`, `proveedor_sugerido_id`, `entrega_min`):

```ts
  marca?: string | null;
  marca_id?: number | null;
  clave_prod_serv?: string | null;
  clave_unidad_sat?: string | null;
  observaciones?: string | null;
```

- [ ] **Step 2: `addLineaAdhoc` propaga los campos**

En `store.ts`, leer la firma de `addLineaAdhoc` y propagar los nuevos campos al objeto de línea que se inserta en el cart (siguiendo cómo ya propaga `descripcion`, `sku_libre`, `costo`, etc.).

- [ ] **Step 3: Verificar**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores TS.

- [ ] **Step 4: Commit**

```bash
git add web/src/features/cotizador/types.ts web/src/features/cotizador/store.ts
git commit -m "feat(cotizador): línea ad-hoc lleva marca/SAT/observaciones (US-008)"
```

### Task 10: Inputs SAT/marca/observaciones en el modal de fantasma

**Files:**
- Modify: `web/src/features/cotizador/components/AgregarFantasmaModal.tsx`

- [ ] **Step 1: State**

Agregar state (junto a los existentes `descripcion`, `skuLibre`, etc.):

```tsx
  const [marca, setMarca] = useState('');
  const [claveProdServ, setClaveProdServ] = useState('');
  const [claveUnidadSat, setClaveUnidadSat] = useState('');
  const [observaciones, setObservaciones] = useState('');
```

Resetearlos en el handler `onOpen` (donde se resetean los demás), a `''`.

- [ ] **Step 2: Inputs**

Dentro del cuerpo scrolleable del modal (`flex-1 overflow-y-auto`), agregar después del bloque de costo/moneda/utilidad/cantidad:

```tsx
<div className="grid grid-cols-2 gap-3">
  <div>
    <label className="block text-[11px] uppercase tracking-wider text-slate-400 mb-1">Marca</label>
    <Input value={marca} onChange={(e) => setMarca(e.target.value)} placeholder="Marca del producto" className="h-8 text-xs" />
  </div>
  <div>
    <label className="block text-[11px] uppercase tracking-wider text-slate-400 mb-1">Clave prod/serv SAT</label>
    <Input value={claveProdServ} onChange={(e) => setClaveProdServ(e.target.value)} maxLength={8} placeholder="Ej. 31181701" className="h-8 text-xs font-mono" />
  </div>
  <div>
    <label className="block text-[11px] uppercase tracking-wider text-slate-400 mb-1">Clave unidad SAT</label>
    <Input value={claveUnidadSat} onChange={(e) => setClaveUnidadSat(e.target.value)} maxLength={10} placeholder="Ej. H87" className="h-8 text-xs font-mono" />
  </div>
  <div>
    <label className="block text-[11px] uppercase tracking-wider text-slate-400 mb-1">Observaciones</label>
    <Input value={observaciones} onChange={(e) => setObservaciones(e.target.value)} placeholder="Notas" className="h-8 text-xs" />
  </div>
</div>
```

- [ ] **Step 3: Incluir en `addLineaAdhoc` (onSave)**

En la llamada a `addLineaAdhoc({...})` dentro de `onSave`, agregar (claves snake_case en la línea; las variables de state del modal siguen en camelCase):

```tsx
      marca: marca.trim() || undefined,
      clave_prod_serv: claveProdServ.trim() || undefined,
      clave_unidad_sat: claveUnidadSat.trim() || undefined,
      observaciones: observaciones.trim() || undefined,
```

- [ ] **Step 4: Actualizar `formIsDirty`**

En `formIsDirty()` (de US-001), añadir a la condición:

```tsx
      marca.trim() !== '' ||
      claveProdServ.trim() !== '' ||
      claveUnidadSat.trim() !== '' ||
      observaciones.trim() !== '' ||
```

- [ ] **Step 5: Verificar**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores TS.

- [ ] **Step 6: Commit**

```bash
git add web/src/features/cotizador/components/AgregarFantasmaModal.tsx
git commit -m "feat(cotizador): modal fantasma captura marca/SAT/observaciones (US-008)"
```

### Task 11: Serialización al payload de DetalleOrden

**Files:**
- Modify: `web/src/features/cotizador/lib/serialize.ts`

- [ ] **Step 1: Incluir campos en el payload**

Leer `serialize.ts` para ver cómo se mapea cada `CartItem` a la línea del payload (donde ya van `sku_libre`, `descripcion_libre`, `proveedor_sugerido_id`). Como la línea ya usa snake_case (Task 9), los campos pasan directo sin mapeo de caso:

```ts
    marca: item.marca ?? null,
    marca_id: item.marca_id ?? null,
    clave_prod_serv: item.clave_prod_serv ?? null,
    clave_unidad_sat: item.clave_unidad_sat ?? null,
    observaciones: item.observaciones ?? null,
```

- [ ] **Step 2: Verificar**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores TS.

- [ ] **Step 3: Commit**

```bash
git add web/src/features/cotizador/lib/serialize.ts
git commit -m "feat(cotizador): serializa marca/SAT/observaciones al guardar (US-008)"
```

---

## Fase 5 — Frontend: FantasmasPage (US-007 display)

### Task 12: Mostrar marca/SAT/observaciones en FantasmasPage

**Files:**
- Modify: `web/src/features/fantasmas/pages/FantasmasPage.tsx`
- Modify: el tipo `Fantasma` (en ese archivo o su `types.ts`) para incluir los campos nuevos.

- [ ] **Step 1: Tipo**

Agregar al tipo `Fantasma`:

```ts
  marca?: string | null;
  marca_id?: number | null;
  clave_prod_serv?: string | null;
  clave_unidad_sat?: string | null;
  observaciones?: string | null;
```

- [ ] **Step 2: Mostrar en la tabla/detalle**

Leer `FantasmasPage.tsx` y añadir marca y claves SAT en la fila (columna o subtexto bajo la descripción), con `—` cuando falten. Si hay un panel/modal de edición del fantasma (PATCH), incluir inputs para editarlos.

- [ ] **Step 3: Verificar**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores TS.

- [ ] **Step 4: Commit**

```bash
git add web/src/features/fantasmas/
git commit -m "feat(fantasmas): muestra marca/SAT/observaciones (US-007)"
```

---

## Fase 6 — PDFs (US-006/008)

### Task 13: SAT en PDF de cotización

**Files:**
- Modify: `app/routers/ventas.py` (template Jinja del PDF, ~líneas 439-474)

- [ ] **Step 1: Renderizar SAT por línea**

En el `{% for d in items_list %}` del template, donde se renderiza la celda de SKU/descripción, agregar el SAT desde el snapshot de línea con fallback al producto. Ejemplo de subtexto bajo la descripción:

```jinja
{% set _csat = item.clave_prod_serv or (item.producto.clave_prod_serv if item.producto else None) %}
{% set _usat = item.clave_unidad_sat or (item.producto.clave_unidad_sat if item.producto else None) %}
{% if _csat or _usat %}<div class="item-sat">SAT: {{ _csat or '—' }} · Unidad: {{ _usat or '—' }}</div>{% endif %}
```

Agregar una regla CSS mínima `.item-sat { font-size: 7pt; color: #666; }` en el bloque `<style>` del template.

- [ ] **Step 2: Verificar**

Run: `python -m py_compile app/routers/ventas.py`
Expected: sin salida (OK).

- [ ] **Step 3: Commit**

```bash
git add app/routers/ventas.py
git commit -m "feat(pdf): clave SAT/unidad en PDF de cotización (US-006/008)"
```

### Task 14: SAT en PDF de remisión

**Files:**
- Modify: `app/routers/remisiones.py`

- [ ] **Step 1: Renderizar SAT por línea**

Leer `remisiones.py` para localizar el generador del PDF y cómo itera las líneas. Aplicar el mismo patrón que Task 13: mostrar `clave_prod_serv` / `clave_unidad_sat` desde el snapshot de la línea (la remisión nace de la cotización; las líneas son `DetalleOrden` o un derivado que conserva esos campos), con fallback al producto.

- [ ] **Step 2: Verificar**

Run: `python -m py_compile app/routers/remisiones.py`
Expected: sin salida (OK).

- [ ] **Step 3: Commit**

```bash
git add app/routers/remisiones.py
git commit -m "feat(pdf): clave SAT/unidad en PDF de remisión (US-006/008)"
```

---

## Fase 7 — Build final + push

### Task 15: Build del SPA y push

- [ ] **Step 1: Build final**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores; `app/static/dist/` regenerado.

- [ ] **Step 2: Commit del dist + push**

```bash
git add app/static/dist
git commit -m "build: recompila SPA (dist) — EPIC 02 Spec (a) campos SAT"
git push origin main
```

---

## Notas de verificación manual (post-deploy, recomendado)

- Crear/editar un producto con clave SAT y clave unidad → ver en tabla de inventario.
- Crear cotización con un fantasma capturando marca + SAT → guardar → revisar en FantasmasPage que el fantasma quedó con esos campos.
- Generar PDF de la cotización → confirmar que aparece la clave SAT/unidad en la línea fantasma.
- Generar remisión de esa cotización → confirmar SAT en el PDF.
- Editar un producto existente SIN tocar SAT → confirmar que no se rompe (campos NULL).

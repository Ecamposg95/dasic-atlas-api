# Remisiones desde Orden de Venta — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Crear remisiones desde una orden de venta con UI tipo cotizador (líneas pre-cargadas, cantidades parciales, agregar fantasma), PDF imprimible y toggle de precios.

**Architecture:** Migración aditiva agrega snapshot de precio/unidad SAT a `detalles_remision` y `moneda`/`mostrar_precios` a `remisiones`. El backend expone un borrador desde la orden, persiste la remisión (precios re-leídos de `DetalleOrden`, server-authoritative) y genera un PDF HTML. El frontend añade una página de creación bajo `/spa/remisiones-nueva` y habilita "Nueva remisión" + botón PDF en `RemisionesPage`.

**Tech Stack:** FastAPI + SQLAlchemy 2.x + Alembic + psycopg (Postgres); React 18 + Vite + TS + Tailwind + TanStack Query + React Router v6.

**Verificación (este repo NO tiene suite de tests — CLAUDE.md):** backend con `python3 -m py_compile <archivos>`; frontend con `cd web && npm run build`. Cada migración requiere su espejo en `app/db/seeds.py::_BACKFILL_DDL` (el Procfile de Railway no corre alembic). Checks manuales en navegador quedan recomendados post-deploy.

**Referencia de diseño:** `docs/superpowers/specs/2026-06-01-remisiones-desde-orden-design.md`.

---

## Fase 1 — Modelo de datos

### Task 1: Migración Alembic + espejo en _BACKFILL_DDL

**Files:**
- Create: `migrations/versions/20260601_03_remisiones_creacion.py`
- Modify: `app/db/seeds.py` (lista `_BACKFILL_DDL`, antes del `]` de cierre)

- [ ] **Step 1: Crear la migración**

```python
"""remisiones_creacion — snapshot de precio/unidad SAT en línea de remisión +
moneda y toggle mostrar_precios a nivel remisión (EPIC 06).

Todas las columnas son NULL o tienen server_default → filas existentes intactas.

Revision ID: 20260601_03
Revises: 20260601_02
Create Date: 2026-06-01
"""
from alembic import op
import sqlalchemy as sa

revision = "20260601_03"
down_revision = "20260601_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("remisiones", sa.Column("moneda", sa.String(3), nullable=True))
    op.add_column(
        "remisiones",
        sa.Column("mostrar_precios", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("detalles_remision", sa.Column("clave_unidad_sat", sa.String(10), nullable=True))
    op.add_column("detalles_remision", sa.Column("precio_unitario", sa.DECIMAL(10, 2), nullable=True))
    op.add_column("detalles_remision", sa.Column("subtotal", sa.DECIMAL(12, 2), nullable=True))


def downgrade() -> None:
    op.drop_column("detalles_remision", "subtotal")
    op.drop_column("detalles_remision", "precio_unitario")
    op.drop_column("detalles_remision", "clave_unidad_sat")
    op.drop_column("remisiones", "mostrar_precios")
    op.drop_column("remisiones", "moneda")
```

- [ ] **Step 2: Espejo en `_BACKFILL_DDL`**

En `app/db/seeds.py`, dentro de la lista `_BACKFILL_DDL`, agregar antes del `]` de cierre:

```python
    # ====================================================================
    # 20260601_03 — EPIC 06: creación de remisiones. Snapshot de precio/
    # unidad SAT por línea + moneda y toggle mostrar_precios por remisión.
    # ====================================================================
    "ALTER TABLE IF EXISTS remisiones ADD COLUMN IF NOT EXISTS moneda VARCHAR(3)",
    "ALTER TABLE IF EXISTS remisiones ADD COLUMN IF NOT EXISTS mostrar_precios BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE IF EXISTS detalles_remision ADD COLUMN IF NOT EXISTS clave_unidad_sat VARCHAR(10)",
    "ALTER TABLE IF EXISTS detalles_remision ADD COLUMN IF NOT EXISTS precio_unitario NUMERIC(10,2)",
    "ALTER TABLE IF EXISTS detalles_remision ADD COLUMN IF NOT EXISTS subtotal NUMERIC(12,2)",
```

- [ ] **Step 3: Verificar**

Run: `python3 -m py_compile migrations/versions/20260601_03_remisiones_creacion.py app/db/seeds.py`
Expected: sin salida (OK).

- [ ] **Step 4: Commit**

```bash
git add migrations/versions/20260601_03_remisiones_creacion.py app/db/seeds.py
git commit -m "feat(db): columnas para creación de remisiones — precio/unidad SAT + moneda/mostrar_precios"
```

### Task 2: Columnas en los modelos ORM

**Files:**
- Modify: `app/models/remisiones.py`

- [ ] **Step 1: Actualizar imports y columnas**

El import actual es `from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text`. Reemplazarlo por:

```python
from sqlalchemy import Boolean, Column, DateTime, DECIMAL, ForeignKey, Integer, String, Text, text
```

En la clase `Remision`, después de `observaciones = Column(Text, nullable=True)`, agregar:

```python
    moneda = Column(String(3), nullable=True)
    mostrar_precios = Column(Boolean, nullable=False, server_default=text("false"))
```

En la clase `DetalleRemision`, después de `observaciones_linea = Column(Text, nullable=True)`, agregar:

```python
    clave_unidad_sat = Column(String(10), nullable=True)
    precio_unitario = Column(DECIMAL(10, 2), nullable=True)
    subtotal = Column(DECIMAL(12, 2), nullable=True)
```

- [ ] **Step 2: Verificar**

Run: `python3 -m py_compile app/models/remisiones.py`
Expected: sin salida (OK).

- [ ] **Step 3: Commit**

```bash
git add app/models/remisiones.py
git commit -m "feat(models): precio/unidad SAT en DetalleRemision + moneda/mostrar_precios en Remision"
```

---

## Fase 2 — Backend: schemas

### Task 3: Extender schemas de remisión

**Files:**
- Modify: `app/schemas/remisiones.py`

- [ ] **Step 1: Agregar campos a los schemas**

Reemplazar `DetalleRemisionInput` y `RemisionCreate` por:

```python
class DetalleRemisionInput(BaseModel):
    detalle_orden_id: Optional[int] = None
    descripcion: str
    sku: Optional[str] = None
    cantidad: int
    observaciones_linea: Optional[str] = None
    # Solo se usan para líneas fantasma ad-hoc (detalle_orden_id is None).
    # Para líneas de orden, el backend re-lee estos valores de DetalleOrden.
    clave_unidad_sat: Optional[str] = None
    precio_unitario: Optional[Decimal] = None


class RemisionCreate(BaseModel):
    orden_venta_id: int
    transportista: Optional[str] = None
    observaciones: Optional[str] = None
    mostrar_precios: bool = False
    detalles: List[DetalleRemisionInput]
```

Agregar el import de Decimal al inicio del archivo (junto a los otros imports de typing/datetime):

```python
from decimal import Decimal
```

- [ ] **Step 2: Verificar**

Run: `python3 -m py_compile app/schemas/remisiones.py`
Expected: sin salida (OK).

- [ ] **Step 3: Commit**

```bash
git add app/schemas/remisiones.py
git commit -m "feat(schemas): mostrar_precios + clave_unidad_sat/precio en input de remisión"
```

---

## Fase 3 — Backend: router (borrador, create, detail, PDF)

### Task 4: Endpoint de borrador desde la orden

**Files:**
- Modify: `app/routers/remisiones.py`

- [ ] **Step 1: Agregar el endpoint borrador**

Después de la función `_generar_folio_remision` (antes de `listar_remisiones`), agregar:

```python
@router.get("/orden/{orden_id}/borrador", dependencies=[Depends(allow_all_staff)])
def borrador_remision_desde_orden(orden_id: int, db: Session = Depends(get_db)):
    """Arma el draft de una remisión desde una orden de venta: una línea por
    cada DetalleOrden con su precio/unidad SAT snapshot y la cantidad sugerida
    (= la de la orden). El frontend precarga la página de creación con esto."""
    orden = db.query(models.OrdenVenta).filter(models.OrdenVenta.id == orden_id).first()
    if not orden:
        raise HTTPException(404, "Orden de venta no encontrada")
    if orden.estatus == models.EstatusOrden.COTIZACION:
        raise HTTPException(400, "La orden todavía es cotización — convierte a venta antes de remisionar")

    lineas = []
    for d in orden.detalles:
        prod = d.producto
        descripcion = d.descripcion_libre or (prod.nombre if prod else None) or "Producto"
        sku = d.sku_libre or (prod.sku_comercial if prod else None) or (prod.sku if prod else None)
        clave_unidad = d.clave_unidad_sat or (prod.clave_unidad_sat if prod else None)
        lineas.append({
            "detalle_orden_id": d.id,
            "descripcion": descripcion,
            "sku": sku,
            "clave_unidad_sat": clave_unidad,
            "precio_unitario": float(d.precio_unitario or 0),
            "cantidad_orden": d.cantidad,
        })

    return {
        "orden_venta_id": orden.id,
        "orden_folio": orden.folio,
        "cliente_nombre": orden.cliente.nombre_empresa if orden.cliente else None,
        "moneda": orden.moneda,
        "lineas": lineas,
    }
```

- [ ] **Step 2: Verificar**

Run: `python3 -m py_compile app/routers/remisiones.py`
Expected: sin salida (OK).

- [ ] **Step 3: Commit**

```bash
git add app/routers/remisiones.py
git commit -m "feat(api): GET /remisiones/orden/{id}/borrador — draft desde orden de venta"
```

### Task 5: Persistir precios/unidad/moneda al crear (server-authoritative)

**Files:**
- Modify: `app/routers/remisiones.py` (función `crear_remision`)

- [ ] **Step 1: Reemplazar el cuerpo de `crear_remision`**

Reemplazar la función `crear_remision` completa por:

```python
@router.post("/", dependencies=[Depends(allow_all_staff)])
def crear_remision(
    payload: schemas.RemisionCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    orden = db.query(models.OrdenVenta).filter(models.OrdenVenta.id == payload.orden_venta_id).first()
    if not orden:
        raise HTTPException(404, "Orden de venta no encontrada")
    if orden.estatus == models.EstatusOrden.COTIZACION:
        raise HTTPException(400, "La orden todavía es cotización — convierte a venta antes de remisionar")
    if not payload.detalles:
        raise HTTPException(400, "Debe incluir al menos una línea")

    # Index de las líneas de la orden para re-leer precio/unidad/desc snapshot.
    det_orden = {d.id: d for d in orden.detalles}

    folio = _generar_folio_remision(db)
    try:
        rem = models.Remision(
            folio=folio,
            orden_venta_id=orden.id,
            moneda=orden.moneda,
            mostrar_precios=payload.mostrar_precios,
            transportista=payload.transportista,
            observaciones=payload.observaciones,
            creado_por_id=current_user.id,
        )
        db.add(rem)
        db.flush()
        for d in payload.detalles:
            if d.cantidad <= 0:
                raise HTTPException(400, "La cantidad de cada línea debe ser > 0")
            if d.detalle_orden_id is not None:
                base = det_orden.get(d.detalle_orden_id)
                if base is None:
                    raise HTTPException(400, f"La línea {d.detalle_orden_id} no pertenece a la orden")
                if d.cantidad > base.cantidad:
                    raise HTTPException(400, f"No se puede remisionar más de lo vendido en la línea {d.detalle_orden_id}")
                prod = base.producto
                descripcion = base.descripcion_libre or (prod.nombre if prod else None) or "Producto"
                sku = base.sku_libre or (prod.sku_comercial if prod else None) or (prod.sku if prod else None)
                clave_unidad = base.clave_unidad_sat or (prod.clave_unidad_sat if prod else None)
                precio = base.precio_unitario or Decimal("0")
            else:
                # Línea fantasma ad-hoc capturada en la remisión (US-024).
                descripcion = d.descripcion
                sku = d.sku
                clave_unidad = d.clave_unidad_sat
                precio = d.precio_unitario or Decimal("0")
            subtotal = (precio * d.cantidad).quantize(Decimal("0.01"))
            db.add(models.DetalleRemision(
                remision_id=rem.id,
                detalle_orden_id=d.detalle_orden_id,
                descripcion=descripcion,
                sku=sku,
                cantidad=d.cantidad,
                observaciones_linea=d.observaciones_linea,
                clave_unidad_sat=clave_unidad,
                precio_unitario=precio,
                subtotal=subtotal,
            ))
        db.commit()
        db.refresh(rem)
        return {"id": rem.id, "folio": rem.folio}
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("remisiones.crear_remision falló")
        raise HTTPException(500, detail=f"{type(exc).__name__}: {exc}")
```

Agregar el import de Decimal al inicio del archivo (junto a `from datetime import datetime`):

```python
from decimal import Decimal
```

- [ ] **Step 2: Verificar**

Run: `python3 -m py_compile app/routers/remisiones.py`
Expected: sin salida (OK).

- [ ] **Step 3: Commit**

```bash
git add app/routers/remisiones.py
git commit -m "feat(api): crear remisión snapshotea precio/unidad/moneda + valida cantidad (US-022/023/024)"
```

### Task 6: Exponer campos nuevos en GET /{id}

**Files:**
- Modify: `app/routers/remisiones.py` (función `detalle_remision`)

- [ ] **Step 1: Agregar campos al response**

En `detalle_remision`, en el dict de retorno agregar a nivel cabecera (después de `"observaciones": rem.observaciones,`):

```python
        "moneda": rem.moneda,
        "mostrar_precios": bool(rem.mostrar_precios),
```

Y en cada línea del list comprehension (después de `"observaciones_linea": d.observaciones_linea,`):

```python
                "clave_unidad_sat": d.clave_unidad_sat,
                "precio_unitario": float(d.precio_unitario) if d.precio_unitario is not None else None,
                "subtotal": float(d.subtotal) if d.subtotal is not None else None,
```

- [ ] **Step 2: Verificar**

Run: `python3 -m py_compile app/routers/remisiones.py`
Expected: sin salida (OK).

- [ ] **Step 3: Commit**

```bash
git add app/routers/remisiones.py
git commit -m "feat(api): GET /remisiones/{id} expone moneda/mostrar_precios + precio/unidad por línea"
```

### Task 7: PDF imprimible de la remisión

**Files:**
- Modify: `app/routers/remisiones.py` (imports + template + endpoint)

- [ ] **Step 1: Agregar imports**

En la cabecera de imports de `app/routers/remisiones.py`, agregar:

```python
from fastapi.responses import HTMLResponse
from jinja2 import BaseLoader, Environment
```

- [ ] **Step 2: Agregar el template y el endpoint**

Al final del archivo, agregar:

```python
PDF_TEMPLATE_REMISION = """<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Remisión {{ rem.folio }}</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: Arial, Helvetica, sans-serif; color:#0f172a; font-size:12px; margin:24px; }
  .head { display:flex; justify-content:space-between; align-items:flex-start; border-bottom:2px solid #0f172a; padding-bottom:8px; margin-bottom:12px; }
  .title { font-size:20px; font-weight:800; letter-spacing:1px; }
  .folio { font-family:monospace; font-size:14px; color:#b45309; font-weight:700; }
  .meta { margin:8px 0 14px; font-size:11px; color:#334155; line-height:1.5; }
  table { width:100%; border-collapse:collapse; }
  th { background:#0f172a; color:#fff; font-size:10px; text-transform:uppercase; padding:6px 8px; text-align:left; }
  td { border-bottom:1px solid #e2e8f0; padding:6px 8px; vertical-align:top; }
  .right { text-align:right; }
  .center { text-align:center; }
  .nota { font-size:9px; color:#64748b; font-style:italic; margin-top:2px; }
  tfoot td { font-weight:700; border-top:2px solid #0f172a; }
  .obs { margin-top:16px; font-size:11px; color:#334155; white-space:pre-line; }
  .firma { margin-top:48px; display:flex; justify-content:space-between; }
  .firma div { width:45%; border-top:1px solid #64748b; padding-top:4px; text-align:center; font-size:10px; color:#64748b; }
</style></head><body>
  <div class="head">
    <div><div class="title">REMISIÓN</div><div class="meta">DASIC Industrial</div></div>
    <div style="text-align:right">
      <div class="folio">{{ rem.folio }}</div>
      <div class="meta">Orden: {{ rem.orden_venta.folio if rem.orden_venta else '—' }}<br>Fecha: {{ rem.fecha_remision.strftime('%d/%m/%Y') if rem.fecha_remision else '' }}</div>
    </div>
  </div>
  <div class="meta">
    <strong>Cliente:</strong> {{ rem.orden_venta.cliente.nombre_empresa if rem.orden_venta and rem.orden_venta.cliente else '—' }}<br>
    {% if rem.transportista %}<strong>Transportista:</strong> {{ rem.transportista }}{% endif %}
  </div>
  <table>
    <thead><tr>
      <th class="center" style="width:30px">#</th>
      <th>Descripción</th>
      <th class="center" style="width:90px">Cantidad</th>
      {% if rem.mostrar_precios %}<th class="right" style="width:90px">P. Unit</th><th class="right" style="width:100px">Subtotal</th>{% endif %}
    </tr></thead>
    <tbody>
      {% for d in rem.detalles %}
      <tr>
        <td class="center">{{ loop.index }}</td>
        <td>{{ d.descripcion }}{% if d.sku %} <span style="color:#64748b;font-family:monospace">({{ d.sku }})</span>{% endif %}{% if d.observaciones_linea %}<div class="nota">{{ d.observaciones_linea }}</div>{% endif %}</td>
        <td class="center">{{ d.cantidad }} ({{ d.clave_unidad_sat or 'PZA' }})</td>
        {% if rem.mostrar_precios %}<td class="right">{{ rem.moneda or '' }} {{ "{:,.2f}".format(d.precio_unitario or 0) }}</td><td class="right">{{ rem.moneda or '' }} {{ "{:,.2f}".format(d.subtotal or 0) }}</td>{% endif %}
      </tr>
      {% endfor %}
    </tbody>
    {% if rem.mostrar_precios %}
    <tfoot><tr>
      <td colspan="4" class="right">Total</td>
      <td class="right">{{ rem.moneda or '' }} {{ "{:,.2f}".format(rem.detalles | sum(attribute='subtotal') or 0) }}</td>
    </tr></tfoot>
    {% endif %}
  </table>
  {% if rem.observaciones %}<div class="obs"><strong>Observaciones:</strong> {{ rem.observaciones }}</div>{% endif %}
  <div class="firma"><div>Entregó</div><div>Recibió</div></div>
</body></html>"""


@router.get("/{id}/imprimir", response_class=HTMLResponse, dependencies=[Depends(allow_all_staff)])
def imprimir_remision(id: int, db: Session = Depends(get_db)):
    rem = db.query(models.Remision).filter(models.Remision.id == id).first()
    if not rem:
        raise HTTPException(404, "Remisión no encontrada")
    env = Environment(loader=BaseLoader())
    return env.from_string(PDF_TEMPLATE_REMISION).render(rem=rem)
```

- [ ] **Step 3: Verificar**

Run: `python3 -m py_compile app/routers/remisiones.py`
Expected: sin salida (OK).

- [ ] **Step 4: Commit**

```bash
git add app/routers/remisiones.py
git commit -m "feat(api): GET /remisiones/{id}/imprimir — PDF HTML con toggle precios + unidad SAT (US-021/022/023)"
```

---

## Fase 4 — Frontend: tipos + hooks

### Task 8: Tipos de la feature de remisiones

**Files:**
- Modify: `web/src/features/remisiones/types.ts`

- [ ] **Step 1: Agregar tipos del borrador y la creación**

Al final de `web/src/features/remisiones/types.ts`, agregar:

```ts
// Borrador devuelto por GET /api/remisiones/orden/{id}/borrador
export type RemisionBorradorLinea = {
  detalle_orden_id: number;
  descripcion: string;
  sku: string | null;
  clave_unidad_sat: string | null;
  precio_unitario: number;
  cantidad_orden: number;
};

export type RemisionBorrador = {
  orden_venta_id: number;
  orden_folio: string | null;
  cliente_nombre: string | null;
  moneda: string | null;
  lineas: RemisionBorradorLinea[];
};

// Línea editable en la página de creación (estado local).
export type RemisionLineaEdit = {
  // Para líneas de orden: el id del DetalleOrden. Para fantasma ad-hoc: null.
  detalle_orden_id: number | null;
  incluir: boolean;
  descripcion: string;
  sku: string | null;
  clave_unidad_sat: string | null;
  precio_unitario: number;
  cantidad: number;
  cantidad_max: number | null; // null para fantasma ad-hoc (sin tope)
  observaciones_linea: string;
};

// Payload de POST /api/remisiones/
export type RemisionDetalleInput = {
  detalle_orden_id: number | null;
  descripcion: string;
  sku: string | null;
  cantidad: number;
  observaciones_linea: string | null;
  clave_unidad_sat: string | null;
  precio_unitario: number | null;
};

export type RemisionCreatePayload = {
  orden_venta_id: number;
  transportista: string | null;
  observaciones: string | null;
  mostrar_precios: boolean;
  detalles: RemisionDetalleInput[];
};

export type RemisionCreateResponse = { id: number; folio: string };

// Item de /api/ventas/historial usado en el selector de orden.
// El backend devuelve `cliente` (nombre de empresa), no `cliente_nombre`.
export type OrdenHistorialItem = {
  id: number;
  folio: string;
  estatus: string;
  cliente?: string | null;
};
```

- [ ] **Step 2: Verificar**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores TS.

- [ ] **Step 3: Commit**

```bash
git add web/src/features/remisiones/types.ts
git commit -m "feat(remisiones): tipos de borrador + creación de remisión"
```

### Task 9: Hooks de borrador, creación y selector de órdenes

**Files:**
- Modify: `web/src/features/remisiones/hooks/useRemisiones.ts`

- [ ] **Step 1: Agregar hooks**

Al final de `web/src/features/remisiones/hooks/useRemisiones.ts`, agregar (y extender el import de tipos en la primera línea para incluir los nuevos):

```ts
import type {
  RemisionBorrador,
  RemisionCreatePayload,
  RemisionCreateResponse,
  OrdenHistorialItem,
} from '../types';

export function useRemisionBorrador(ordenId: number | null) {
  return useQuery({
    queryKey: ['remision-borrador', ordenId],
    queryFn: () => api.get<RemisionBorrador>(`/api/remisiones/orden/${ordenId}/borrador`),
    enabled: ordenId !== null,
  });
}

export function useCrearRemision() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: RemisionCreatePayload) =>
      api.post<RemisionCreateResponse>('/api/remisiones/', payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['remisiones'] });
    },
  });
}

export function useOrdenesRemisionables() {
  // Órdenes ya convertidas a venta (estatus != cotizacion) candidatas a remisión.
  return useQuery({
    queryKey: ['ventas', 'historial', 'remisionables'],
    queryFn: async () => {
      const items = await api.get<OrdenHistorialItem[]>('/api/ventas/historial?limit=200');
      return items.filter((o) => (o.estatus || '').toLowerCase() !== 'cotizacion');
    },
  });
}
```

> Nota: el import de `../types` en la línea 3 del archivo ya existe — agregar los nuevos nombres a ese import en vez de duplicar la sentencia si el linter se queja.

- [ ] **Step 2: Verificar**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores TS.

- [ ] **Step 3: Commit**

```bash
git add web/src/features/remisiones/hooks/useRemisiones.ts
git commit -m "feat(remisiones): hooks de borrador, crear remisión y órdenes remisionables"
```

---

## Fase 5 — Frontend: página de creación + modal fantasma + ruta

### Task 10: Modal para agregar línea fantasma a la remisión

**Files:**
- Create: `web/src/features/remisiones/components/AgregarLineaFantasmaModal.tsx`

- [ ] **Step 1: Crear el componente**

```tsx
import { useState } from 'react';
import { Ghost, X } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import type { RemisionLineaEdit } from '../types';

export function AgregarLineaFantasmaModal({
  open,
  onClose,
  onAdd,
}: {
  open: boolean;
  onClose: () => void;
  onAdd: (linea: RemisionLineaEdit) => void;
}) {
  const [descripcion, setDescripcion] = useState('');
  const [sku, setSku] = useState('');
  const [claveUnidad, setClaveUnidad] = useState('');
  const [cantidad, setCantidad] = useState('1');
  const [precio, setPrecio] = useState('0');
  const [err, setErr] = useState<string | null>(null);

  if (!open) return null;

  function reset() {
    setDescripcion(''); setSku(''); setClaveUnidad(''); setCantidad('1'); setPrecio('0'); setErr(null);
  }

  function onSave() {
    const desc = descripcion.trim();
    if (!desc) { setErr('La descripción es obligatoria.'); return; }
    const q = parseInt(cantidad, 10);
    if (!Number.isFinite(q) || q <= 0) { setErr('La cantidad debe ser mayor a 0.'); return; }
    onAdd({
      detalle_orden_id: null,
      incluir: true,
      descripcion: desc,
      sku: sku.trim() || null,
      clave_unidad_sat: claveUnidad.trim() || null,
      precio_unitario: parseFloat(precio) || 0,
      cantidad: q,
      cantidad_max: null,
      observaciones_linea: '',
    });
    reset();
    onClose();
  }

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-slate-900 border border-amber-700/50 rounded-xl shadow-2xl max-w-lg w-full">
        <div className="flex items-center justify-between px-5 pt-5 pb-3 border-b border-slate-200 dark:border-slate-800">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Ghost className="h-4 w-4 text-amber-500" /> Agregar producto fantasma
          </h3>
          <button type="button" onClick={() => { reset(); onClose(); }} className="text-slate-400 hover:text-slate-600">
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="px-5 py-4 space-y-3">
          <div>
            <label className="block text-xs text-slate-500 mb-1">Descripción *</label>
            <Input value={descripcion} onChange={(e) => setDescripcion(e.target.value)} placeholder="Descripción del producto" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-slate-500 mb-1">SKU</label>
              <Input value={sku} onChange={(e) => setSku(e.target.value)} className="font-mono" />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">Clave unidad SAT</label>
              <Input value={claveUnidad} onChange={(e) => setClaveUnidad(e.target.value)} maxLength={10} placeholder="Ej. H87" className="font-mono" />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">Cantidad *</label>
              <Input type="number" min="1" value={cantidad} onChange={(e) => setCantidad(e.target.value)} />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">Precio unitario</label>
              <Input type="number" step="0.01" min="0" value={precio} onChange={(e) => setPrecio(e.target.value)} className="text-right font-mono" />
            </div>
          </div>
          {err && <div className="text-xs bg-rose-50 dark:bg-rose-900/30 border border-rose-300 dark:border-rose-700/50 rounded p-2 text-rose-700 dark:text-rose-300">{err}</div>}
        </div>
        <div className="flex justify-end gap-2 px-5 py-4 border-t border-slate-200 dark:border-slate-800">
          <Button variant="ghost" size="sm" onClick={() => { reset(); onClose(); }}>Cancelar</Button>
          <Button size="sm" onClick={onSave} className="bg-amber-600 hover:bg-amber-700 text-white">Agregar</Button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verificar**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores TS.

- [ ] **Step 3: Commit**

```bash
git add web/src/features/remisiones/components/AgregarLineaFantasmaModal.tsx
git commit -m "feat(remisiones): modal para agregar línea fantasma ad-hoc (US-024)"
```

### Task 11: Página de creación de remisión

**Files:**
- Create: `web/src/features/remisiones/pages/CrearRemisionPage.tsx`

- [ ] **Step 1: Crear la página**

```tsx
import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Truck, Plus, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from '@/lib/toast';
import {
  useRemisionBorrador,
  useCrearRemision,
  useOrdenesRemisionables,
} from '../hooks/useRemisiones';
import { AgregarLineaFantasmaModal } from '../components/AgregarLineaFantasmaModal';
import type { RemisionLineaEdit } from '../types';

export function CrearRemisionPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const ordenParam = params.get('orden');
  const ordenId = ordenParam ? parseInt(ordenParam, 10) : null;

  const { data: borrador, isLoading } = useRemisionBorrador(ordenId);
  const { data: ordenes } = useOrdenesRemisionables();
  const crear = useCrearRemision();

  const [lineas, setLineas] = useState<RemisionLineaEdit[]>([]);
  const [mostrarPrecios, setMostrarPrecios] = useState(false);
  const [transportista, setTransportista] = useState('');
  const [observaciones, setObservaciones] = useState('');
  const [modalFantasma, setModalFantasma] = useState(false);

  // Precargar las líneas cuando llega el borrador.
  useEffect(() => {
    if (!borrador) return;
    setLineas(
      borrador.lineas.map((l) => ({
        detalle_orden_id: l.detalle_orden_id,
        incluir: true,
        descripcion: l.descripcion,
        sku: l.sku,
        clave_unidad_sat: l.clave_unidad_sat,
        precio_unitario: l.precio_unitario,
        cantidad: l.cantidad_orden,
        cantidad_max: l.cantidad_orden,
        observaciones_linea: '',
      })),
    );
  }, [borrador]);

  const incluidas = useMemo(() => lineas.filter((l) => l.incluir && l.cantidad > 0), [lineas]);

  function updateLinea(idx: number, patch: Partial<RemisionLineaEdit>) {
    setLineas((prev) => prev.map((l, i) => (i === idx ? { ...l, ...patch } : l)));
  }

  function onGuardar() {
    if (!ordenId) { toast({ kind: 'warning', title: 'Selecciona una orden primero' }); return; }
    if (incluidas.length === 0) { toast({ kind: 'warning', title: 'Incluye al menos una línea' }); return; }
    crear.mutate(
      {
        orden_venta_id: ordenId,
        transportista: transportista.trim() || null,
        observaciones: observaciones.trim() || null,
        mostrar_precios: mostrarPrecios,
        detalles: incluidas.map((l) => ({
          detalle_orden_id: l.detalle_orden_id,
          descripcion: l.descripcion,
          sku: l.sku,
          cantidad: l.cantidad,
          observaciones_linea: l.observaciones_linea || null,
          clave_unidad_sat: l.clave_unidad_sat,
          precio_unitario: l.detalle_orden_id == null ? l.precio_unitario : null,
        })),
      },
      {
        onSuccess: (r) => {
          toast({ kind: 'success', title: `Remisión ${r.folio} creada` });
          window.open(`/api/remisiones/${r.id}/imprimir`, '_blank');
          navigate('/spa/remisiones');
        },
        onError: (e: { status?: number; detail?: string }) => {
          if (e.status === 401) { window.location.href = '/spa/login'; return; }
          toast({ kind: 'error', title: 'No se pudo crear', description: e.detail });
        },
      },
    );
  }

  // Sin orden seleccionada → selector de orden.
  if (!ordenId) {
    return (
      <div className="p-6 max-w-3xl mx-auto space-y-4">
        <h1 className="text-2xl font-semibold flex items-center gap-2">
          <Truck className="h-5 w-5 text-cyan-400" /> Nueva remisión
        </h1>
        <p className="text-sm text-slate-500">Selecciona la orden de venta a remisionar:</p>
        <div className="border border-slate-200 dark:border-slate-800 rounded-md divide-y divide-slate-100 dark:divide-slate-800">
          {(ordenes ?? []).map((o) => (
            <button
              key={o.id}
              type="button"
              onClick={() => navigate(`/spa/remisiones-nueva?orden=${o.id}`)}
              className="w-full text-left px-4 py-2 hover:bg-slate-50 dark:hover:bg-slate-800 flex items-center justify-between"
            >
              <span className="font-mono text-sm text-accent-glow">{o.folio}</span>
              <span className="text-xs text-slate-500">{o.cliente ?? ''}</span>
            </button>
          ))}
          {(ordenes ?? []).length === 0 && (
            <div className="px-4 py-6 text-center text-sm text-slate-500">No hay órdenes de venta remisionables.</div>
          )}
        </div>
      </div>
    );
  }

  if (isLoading) {
    return <div className="p-6 text-sm text-slate-500">Cargando orden…</div>;
  }

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold flex items-center gap-2">
          <Truck className="h-5 w-5 text-cyan-400" /> Nueva remisión
        </h1>
        <Button variant="ghost" size="sm" onClick={() => navigate('/spa/remisiones')}>
          <ArrowLeft className="h-4 w-4 mr-1" /> Volver
        </Button>
      </div>

      {borrador && (
        <div className="text-sm bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-md px-4 py-2">
          <span className="font-mono text-accent-glow">{borrador.orden_folio}</span>
          {borrador.cliente_nombre && <span className="ml-3 text-slate-500">{borrador.cliente_nombre}</span>}
          {borrador.moneda && <span className="ml-3 text-slate-500">{borrador.moneda}</span>}
        </div>
      )}

      <div className="border border-slate-200 dark:border-slate-800 rounded-md overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 dark:bg-slate-800 text-xs uppercase text-slate-500">
            <tr>
              <th className="p-2 text-center w-10">Incl.</th>
              <th className="p-2 text-left">Descripción</th>
              <th className="p-2 text-center w-28">Cantidad</th>
              <th className="p-2 text-left">Observaciones</th>
            </tr>
          </thead>
          <tbody>
            {lineas.map((l, idx) => (
              <tr key={idx} className="border-t border-slate-100 dark:border-slate-800">
                <td className="p-2 text-center">
                  <input type="checkbox" checked={l.incluir} onChange={(e) => updateLinea(idx, { incluir: e.target.checked })} />
                </td>
                <td className="p-2">
                  <div className="text-slate-800 dark:text-slate-200">{l.descripcion}</div>
                  {l.sku && <div className="text-[11px] font-mono text-slate-500">{l.sku}</div>}
                </td>
                <td className="p-2 text-center">
                  <Input
                    type="number"
                    min="1"
                    max={l.cantidad_max ?? undefined}
                    value={l.cantidad}
                    onChange={(e) => {
                      const v = parseInt(e.target.value, 10) || 0;
                      const capped = l.cantidad_max != null ? Math.min(v, l.cantidad_max) : v;
                      updateLinea(idx, { cantidad: Math.max(0, capped) });
                    }}
                    className="h-8 text-xs text-center w-20 inline-block"
                  />
                  {l.cantidad_max != null && <div className="text-[10px] text-slate-400">de {l.cantidad_max}</div>}
                </td>
                <td className="p-2">
                  <Input
                    value={l.observaciones_linea}
                    onChange={(e) => updateLinea(idx, { observaciones_linea: e.target.value })}
                    className="h-8 text-xs"
                    placeholder="Nota de la línea"
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Button variant="outline" size="sm" onClick={() => setModalFantasma(true)}>
        <Plus className="h-4 w-4 mr-1" /> Agregar fantasma
      </Button>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div>
          <label className="block text-xs text-slate-500 mb-1">Transportista</label>
          <Input value={transportista} onChange={(e) => setTransportista(e.target.value)} />
        </div>
        <div>
          <label className="block text-xs text-slate-500 mb-1">Observaciones generales</label>
          <Input value={observaciones} onChange={(e) => setObservaciones(e.target.value)} />
        </div>
      </div>

      <label className="flex items-center gap-2 text-sm cursor-pointer">
        <input type="checkbox" checked={mostrarPrecios} onChange={(e) => setMostrarPrecios(e.target.checked)} />
        Mostrar precios en el PDF
      </label>

      <div className="flex justify-end">
        <Button size="sm" onClick={onGuardar} disabled={crear.isPending}>
          {crear.isPending ? 'Guardando…' : 'Generar remisión'}
        </Button>
      </div>

      <AgregarLineaFantasmaModal
        open={modalFantasma}
        onClose={() => setModalFantasma(false)}
        onAdd={(linea) => setLineas((prev) => [...prev, linea])}
      />
    </div>
  );
}
```

- [ ] **Step 2: Verificar**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores TS.

- [ ] **Step 3: Commit**

```bash
git add web/src/features/remisiones/pages/CrearRemisionPage.tsx
git commit -m "feat(remisiones): página de creación con líneas parciales + fantasma + toggle precios (US-019/022/023/024)"
```

### Task 12: Registrar la ruta SPA

**Files:**
- Modify: `web/src/router.tsx`

- [ ] **Step 1: Agregar el lazy y la ruta**

Junto a los otros `const ... = lazyPage(...)` (cerca de la línea 28), agregar:

```tsx
const crearRemision = lazyPage(() => import('@/features/remisiones/pages/CrearRemisionPage'), 'CrearRemisionPage');
```

Dentro de los children del route `/spa` (después de `{ path: 'remisiones', lazy: remisiones },` — esa línea está en la lista de children de `/spa`), agregar:

```tsx
      { path: 'remisiones-nueva', lazy: crearRemision },
```

> No requiere cambios en `app/main.py`: el catch-all `@app.get("/spa/{full_path:path}")` ya sirve el index.html para cualquier sub-ruta de `/spa`.

- [ ] **Step 2: Verificar**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores TS.

- [ ] **Step 3: Commit**

```bash
git add web/src/router.tsx
git commit -m "feat(remisiones): ruta /spa/remisiones-nueva"
```

---

## Fase 6 — Frontend: habilitar acciones en RemisionesPage

### Task 13: Habilitar "Nueva remisión" + botón PDF por fila

**Files:**
- Modify: `web/src/features/remisiones/pages/RemisionesPage.tsx`

- [ ] **Step 1: Imports**

En la línea de import de `lucide-react` (línea 3), agregar `Plus` y `FileText`:

```tsx
import { Truck, ChevronLeft, ChevronRight, Eye, CheckSquare, X, Plus, FileText } from 'lucide-react';
```

Agregar el import de `useNavigate` (junto a los imports de react-router; si no existe, agregarlo):

```tsx
import { Link, useNavigate } from 'react-router-dom';
```

> Si el archivo ya importa `Link` desde `react-router-dom`, fusiona `useNavigate` en ese import en lugar de duplicarlo.

- [ ] **Step 2: Botón PDF en `RemisionRow`**

En `RemisionRow`, dentro del `<div className="flex items-center gap-2 justify-end">` (después del botón "Ver"), agregar:

```tsx
          <Button
            size="sm"
            variant="secondary"
            title="Imprimir PDF"
            onClick={() => window.open(`/api/remisiones/${item.id}/imprimir`, '_blank')}
          >
            <FileText className="h-3.5 w-3.5 mr-1" />
            PDF
          </Button>
```

- [ ] **Step 3: Habilitar "Nueva remisión"**

En `RemisionesPage`, agregar al inicio del componente (después de los `useState`):

```tsx
  const navigate = useNavigate();
```

Localizar el botón "Nueva remisión" (tiene `disabled` y el texto `+ Nueva remisión`, ~línea 303) y reemplazar ese `<Button ...>` por:

```tsx
        <Button size="sm" onClick={() => navigate('/spa/remisiones-nueva')}>
          <Plus className="h-4 w-4 mr-1" />
          Nueva remisión
        </Button>
```

- [ ] **Step 4: Verificar**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores TS.

- [ ] **Step 5: Commit**

```bash
git add web/src/features/remisiones/pages/RemisionesPage.tsx
git commit -m "feat(remisiones): habilita Nueva remisión + botón PDF por fila (US-019/021)"
```

---

## Fase 7 — Build final + push

### Task 14: Build del SPA y push

- [ ] **Step 1: Build final**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores; `app/static/dist/` regenerado.

- [ ] **Step 2: Commit del dist + push**

```bash
git add app/static/dist
git commit -m "build: recompila SPA (dist) — EPIC 06 creación de remisiones"
git push origin main
```

---

## Notas de verificación manual (post-deploy, recomendado)

- Convertir una cotización a venta; en RemisionesPage → "Nueva remisión" → elegir la orden.
- Ajustar una cantidad por debajo de la vendida y deseleccionar una línea → Generar.
- Agregar un fantasma ad-hoc con clave unidad SAT → Generar.
- Abrir el PDF: confirmar folio `R-…`, cantidad "N (unidad)", y que SIN el toggle no aparecen precios; CON el toggle aparecen precio/subtotal/total.
- Intentar remisionar más de lo vendido → el backend responde 400 (validación de cantidad).

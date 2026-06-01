# Fantasma en OC + Recepción parcial — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Conservar marca/SAT en las líneas de OC provenientes de cotización (US-026) y permitir recepción parcial incremental de OC con cantidad recibida y fecha por línea (US-027).

**Architecture:** Migración aditiva agrega snapshot SAT/marca + `cantidad_recibida`/`fecha_recepcion` a `detalles_compra`. `/confirmar` copia el snapshot. Un helper `_aplicar_recepcion` acumula recibido por línea, mueve ENTRADA solo para líneas de catálogo (fantasma sin stock), y recalcula el estatus de la OC (`recibida_parcial`/`recibido`). Nuevo endpoint `recibir-parcial`; `recibir` total se refactoriza sobre el helper. El frontend convierte el modal de recepción en una tabla por línea.

**Tech Stack:** FastAPI + SQLAlchemy 2.x + Alembic + psycopg (Postgres); React 18 + Vite + TS + Tailwind + TanStack Query.

**Verificación (este repo NO tiene suite de tests — CLAUDE.md):** backend `python3 -m py_compile <archivos>`; frontend `cd web && npm run build`. Migración nueva requiere espejo en `app/db/seeds.py::_BACKFILL_DDL`. Los schemas de compras son **Pydantic inline en `compras.py`** (no en `app/schemas/`), así que NO requieren re-export en `__init__.py`.

**Referencia de diseño:** `docs/superpowers/specs/2026-06-01-oc-fantasma-recepcion-parcial-design.md`.

---

## Fase 1 — Modelo de datos

### Task 1: Migración + espejo en _BACKFILL_DDL

**Files:**
- Create: `migrations/versions/20260601_04_oc_recepcion_parcial.py`
- Modify: `app/db/seeds.py`

- [ ] **Step 1: Crear la migración**

```python
"""oc_recepcion_parcial — snapshot SAT/marca en línea de OC (US-026) +
cantidad_recibida/fecha_recepcion para recepción parcial (US-027).

Aditivo: NULL o server_default → OCs existentes intactas.

Revision ID: 20260601_04
Revises: 20260601_03
Create Date: 2026-06-01
"""
from alembic import op
import sqlalchemy as sa

revision = "20260601_04"
down_revision = "20260601_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("detalles_compra", sa.Column("marca", sa.String(80), nullable=True))
    op.add_column("detalles_compra", sa.Column("clave_prod_serv", sa.String(8), nullable=True))
    op.add_column("detalles_compra", sa.Column("clave_unidad_sat", sa.String(10), nullable=True))
    op.add_column("detalles_compra", sa.Column("cantidad_recibida", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("detalles_compra", sa.Column("fecha_recepcion", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("detalles_compra", "fecha_recepcion")
    op.drop_column("detalles_compra", "cantidad_recibida")
    op.drop_column("detalles_compra", "clave_unidad_sat")
    op.drop_column("detalles_compra", "clave_prod_serv")
    op.drop_column("detalles_compra", "marca")
```

- [ ] **Step 2: Espejo en `_BACKFILL_DDL`**

En `app/db/seeds.py`, dentro de la lista `_BACKFILL_DDL`, agregar antes del `]` de cierre:

```python
    # ====================================================================
    # 20260601_04 — US-026/027: snapshot SAT/marca + recepción parcial en
    # líneas de OC. Todo aditivo.
    # ====================================================================
    "ALTER TABLE IF EXISTS detalles_compra ADD COLUMN IF NOT EXISTS marca VARCHAR(80)",
    "ALTER TABLE IF EXISTS detalles_compra ADD COLUMN IF NOT EXISTS clave_prod_serv VARCHAR(8)",
    "ALTER TABLE IF EXISTS detalles_compra ADD COLUMN IF NOT EXISTS clave_unidad_sat VARCHAR(10)",
    "ALTER TABLE IF EXISTS detalles_compra ADD COLUMN IF NOT EXISTS cantidad_recibida INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE IF EXISTS detalles_compra ADD COLUMN IF NOT EXISTS fecha_recepcion TIMESTAMP WITH TIME ZONE",
```

- [ ] **Step 3: Verificar**

Run: `python3 -m py_compile migrations/versions/20260601_04_oc_recepcion_parcial.py app/db/seeds.py`
Expected: sin salida (OK).

- [ ] **Step 4: Commit**

```bash
git add migrations/versions/20260601_04_oc_recepcion_parcial.py app/db/seeds.py
git commit -m "feat(db): SAT/marca + cantidad_recibida/fecha en detalles_compra (US-026/027)"
```

### Task 2: Columnas en el modelo `DetalleCompra`

**Files:**
- Modify: `app/models/purchases.py`

- [ ] **Step 1: Imports + columnas**

Cambiar la línea de import:
```python
from sqlalchemy import Column, DateTime, DECIMAL, ForeignKey, Integer, String
```
por:
```python
from sqlalchemy import Column, DateTime, DECIMAL, ForeignKey, Integer, String, text
```

En la clase `DetalleCompra`, después de `costo_unitario = Column(DECIMAL(10, 2), nullable=False)`, agregar:
```python
    # Snapshot SAT/marca de la línea (US-026): para conservar los datos del
    # fantasma/producto cotizado en la OC.
    marca = Column(String(80), nullable=True)
    clave_prod_serv = Column(String(8), nullable=True)
    clave_unidad_sat = Column(String(10), nullable=True)
    # Recepción parcial incremental (US-027): cantidad acumulada recibida y
    # fecha de la última recepción de esta línea.
    cantidad_recibida = Column(Integer, nullable=False, server_default=text("0"))
    fecha_recepcion = Column(DateTime(timezone=True), nullable=True)
```

- [ ] **Step 2: Verificar**

Run: `python3 -m py_compile app/models/purchases.py`
Expected: sin salida (OK).

- [ ] **Step 3: Commit**

```bash
git add app/models/purchases.py
git commit -m "feat(models): SAT/marca + cantidad_recibida/fecha_recepcion en DetalleCompra"
```

---

## Fase 2 — Backend US-026 (conservar marca/SAT)

### Task 3: `/confirmar` copia marca/SAT + serializador expone los campos

**Files:**
- Modify: `app/routers/compras.py`

- [ ] **Step 1: Copiar snapshot al crear `DetalleCompra` en `confirmar_ocs_desde_cotizacion`**

Localizar el `db.add(models.DetalleCompra( ... ))` dentro de `confirmar_ocs_desde_cotizacion` (tiene `sku_libre=det.sku_libre if not det.producto_id else None` y `costo_base_linea=det.costo_base_linea`). Reemplazar esa construcción por:

```python
                db.add(models.DetalleCompra(
                    orden_compra_id=oc.id,
                    producto_id=det.producto_id,
                    cantidad=cantidad,
                    costo_unitario=costo_unitario,
                    sku_libre=det.sku_libre if not det.producto_id else None,
                    descripcion_libre=det.descripcion_libre if not det.producto_id else None,
                    moneda_origen_linea=det.moneda_origen_linea,
                    costo_base_linea=det.costo_base_linea,
                    marca=det.marca,
                    clave_prod_serv=det.clave_prod_serv,
                    clave_unidad_sat=det.clave_unidad_sat,
                ))
```

- [ ] **Step 2: Exponer los campos en `_serializar_oc`**

En `_serializar_oc`, dentro del dict de cada línea (después de `"costo_unitario": float(d.costo_unitario or 0),`), agregar:

```python
                "marca": d.marca,
                "clave_prod_serv": d.clave_prod_serv,
                "clave_unidad_sat": d.clave_unidad_sat,
                "cantidad_recibida": d.cantidad_recibida or 0,
                "fecha_recepcion": d.fecha_recepcion.isoformat() if d.fecha_recepcion else None,
```

- [ ] **Step 3: Verificar**

Run: `python3 -m py_compile app/routers/compras.py`
Expected: sin salida (OK).

- [ ] **Step 4: Commit**

```bash
git add app/routers/compras.py
git commit -m "feat(api): OC conserva marca/SAT del fantasma + expone recepción por línea (US-026)"
```

---

## Fase 3 — Backend US-027 (recepción parcial incremental)

### Task 4: Schemas inline + helper `_aplicar_recepcion`

**Files:**
- Modify: `app/routers/compras.py`

- [ ] **Step 1: Asegurar imports de typing/datetime**

En la cabecera de `app/routers/compras.py`, confirmar que existan `from datetime import datetime` y `from typing import List, Optional`. Si falta alguno, agregarlo (el módulo ya usa `datetime.utcnow()` y `Optional` en schemas inline; agregar `List` si no está).

- [ ] **Step 2: Agregar schemas inline**

Inmediatamente antes del endpoint `@router.post("/{id}/recibir", ...)` (función `recibir_oc`), agregar:

```python
class RecepcionLineaInput(BaseModel):
    detalle_compra_id: int
    cantidad: int  # cuánto llegó AHORA (delta), no el acumulado


class RecepcionParcialInput(BaseModel):
    lineas: List[RecepcionLineaInput]
    fecha: Optional[datetime] = None


def _aplicar_recepcion(db: Session, orden, deltas: dict, fecha, usuario) -> dict:
    """Aplica recepción incremental sobre las líneas de la OC.

    deltas: {detalle_compra_id: cantidad_que_llego_ahora}. Por cada línea con
    delta>0 valida que cantidad_recibida+delta<=cantidad, acumula
    cantidad_recibida, fija fecha_recepcion, y para líneas de CATÁLOGO
    (producto_id no nulo) emite ENTRADA por el delta. Las líneas fantasma
    (producto_id nulo) solo registran (sin stock; el stock entra al promover).
    Recalcula el estatus de la OC. Retorna {procesados, estatus}."""
    procesados = 0
    for det in orden.detalles:
        delta = int(deltas.get(det.id, 0) or 0)
        if delta <= 0:
            continue
        if (det.cantidad_recibida or 0) + delta > det.cantidad:
            raise HTTPException(400, f"La línea {det.id} excede la cantidad pedida ({det.cantidad})")
        if det.producto_id:
            producto = db.get(models.Producto, det.producto_id)
            if producto:
                aplicar_movimiento(
                    db,
                    producto=producto,
                    tipo=TipoMovimientoStock.ENTRADA.value,
                    cantidad=delta,
                    referencia_tipo="oc",
                    referencia_id=orden.id,
                    motivo=f"Recepción OC {orden.folio or '#'+str(orden.id)}",
                    usuario=usuario,
                )
        det.cantidad_recibida = (det.cantidad_recibida or 0) + delta
        det.fecha_recepcion = fecha or datetime.utcnow()
        procesados += 1

    completas = all((d.cantidad_recibida or 0) >= d.cantidad for d in orden.detalles)
    alguna = any((d.cantidad_recibida or 0) > 0 for d in orden.detalles)
    if completas:
        orden.estatus = "recibido"
    elif alguna:
        orden.estatus = "recibida_parcial"
    return {"procesados": procesados, "estatus": orden.estatus}
```

- [ ] **Step 3: Verificar**

Run: `python3 -m py_compile app/routers/compras.py`
Expected: sin salida (OK).

- [ ] **Step 4: Commit**

```bash
git add app/routers/compras.py
git commit -m "feat(api): helper _aplicar_recepcion + schemas de recepción parcial (US-027)"
```

### Task 5: Endpoint `recibir-parcial` + refactor de `recibir`

**Files:**
- Modify: `app/routers/compras.py`

- [ ] **Step 1: Reemplazar el cuerpo de `recibir_oc` por la versión basada en el helper**

Reemplazar la función `recibir_oc` completa por:

```python
@router.post("/{id}/recibir", dependencies=[Depends(allow_admin_asistente)])
def recibir_oc(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    """Recibe TODO lo pendiente de la OC (delta = cantidad - cantidad_recibida
    por línea) reutilizando _aplicar_recepcion. Idempotente: si ya está todo
    recibido, no hay deltas. Marca la OC como recibida/parcial según resultado."""
    orden = db.query(models.OrdenCompra).filter(models.OrdenCompra.id == id).first()
    if not orden:
        raise HTTPException(404, "OC no encontrada")
    if orden.estatus == "recibido":
        raise HTTPException(400, "La OC ya fue recibida")
    if orden.estatus not in ("borrador", "enviada", "confirmada", "recibida_parcial"):
        raise HTTPException(400, f"Estatus '{orden.estatus}' no permite recepción")
    if not orden.detalles:
        raise HTTPException(400, "OC sin detalles, nada que recibir")

    deltas = {
        d.id: (d.cantidad - (d.cantidad_recibida or 0))
        for d in orden.detalles
        if (d.cantidad - (d.cantidad_recibida or 0)) > 0
    }
    if not deltas:
        raise HTTPException(400, "No hay cantidades pendientes por recibir")

    try:
        res = _aplicar_recepcion(db, orden, deltas, None, current_user)
        db.commit()
        return {
            "ok": True,
            "folio": orden.folio,
            "productos_ingresados": res["procesados"],
            "estatus": res["estatus"],
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("compras.recibir_oc falló (id=%s)", id)
        raise HTTPException(500, detail=f"{type(exc).__name__}: {exc}")
```

- [ ] **Step 2: Agregar el endpoint `recibir-parcial` justo después de `recibir_oc`**

```python
@router.post("/{id}/recibir-parcial", dependencies=[Depends(allow_admin_asistente)])
def recibir_oc_parcial(
    id: int,
    payload: RecepcionParcialInput,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    """Recepción parcial incremental: recibe las cantidades indicadas por línea
    (delta de esta recepción). Acumula cantidad_recibida y mueve stock solo para
    líneas de catálogo. La OC pasa a 'recibida_parcial' o 'recibido'."""
    orden = db.query(models.OrdenCompra).filter(models.OrdenCompra.id == id).first()
    if not orden:
        raise HTTPException(404, "OC no encontrada")
    if orden.estatus == "recibido":
        raise HTTPException(400, "La OC ya fue recibida en su totalidad")
    if orden.estatus not in ("borrador", "enviada", "confirmada", "recibida_parcial"):
        raise HTTPException(400, f"Estatus '{orden.estatus}' no permite recepción")

    deltas = {l.detalle_compra_id: l.cantidad for l in payload.lineas if l.cantidad and l.cantidad > 0}
    if not deltas:
        raise HTTPException(400, "No se indicaron cantidades a recibir")

    try:
        res = _aplicar_recepcion(db, orden, deltas, payload.fecha, current_user)
        db.commit()
        return {
            "ok": True,
            "folio": orden.folio,
            "estatus": res["estatus"],
            "procesados": res["procesados"],
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("compras.recibir_oc_parcial falló (id=%s)", id)
        raise HTTPException(500, detail=f"{type(exc).__name__}: {exc}")
```

- [ ] **Step 3: Verificar**

Run: `python3 -m py_compile app/routers/compras.py`
Expected: sin salida (OK).

- [ ] **Step 4: Commit**

```bash
git add app/routers/compras.py
git commit -m "feat(api): POST /compras/{id}/recibir-parcial + recibir total reusa helper (US-027)"
```

---

## Fase 4 — Frontend: tipos + hook

### Task 6: Tipos de recepción parcial

**Files:**
- Modify: `web/src/features/compras/types.ts`

- [ ] **Step 1: Extender `OrdenCompraLinea`**

En `OrdenCompraLinea`, después de `costo_unitario: number;`, agregar:

```ts
  marca?: string | null;
  clave_prod_serv?: string | null;
  clave_unidad_sat?: string | null;
  cantidad_recibida: number;
  fecha_recepcion: string | null;
```

- [ ] **Step 2: Agregar tipos del payload/respuesta de recepción parcial**

Después del bloque `export type RecepcionResponse = { ... };`, agregar:

```ts
// ── POST /api/compras/{id}/recibir-parcial ────────────────────────────────────
export type RecepcionParcialPayload = {
  lineas: { detalle_compra_id: number; cantidad: number }[];
  fecha?: string | null;
};

export type RecepcionParcialResponse = {
  ok: boolean;
  folio: string | null;
  estatus: EstatusOC;
  procesados: number;
};
```

- [ ] **Step 3: Verificar**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores TS.

- [ ] **Step 4: Commit**

```bash
git add web/src/features/compras/types.ts
git commit -m "feat(compras): tipos de recepción parcial + SAT/marca por línea"
```

### Task 7: Hook `useRecibirParcial`

**Files:**
- Create: `web/src/features/compras/hooks/useRecibirParcial.ts`

- [ ] **Step 1: Crear el hook**

```ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { RecepcionParcialPayload, RecepcionParcialResponse } from '../types';

export function useRecibirParcial(id: number) {
  const qc = useQueryClient();
  return useMutation<RecepcionParcialResponse, { status?: number; detail?: string }, RecepcionParcialPayload>({
    mutationFn: (payload) => api.post<RecepcionParcialResponse>(`/api/compras/${id}/recibir-parcial`, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['ordenesCompra'] });
      qc.invalidateQueries({ queryKey: ['ordenCompraDetalle', id] });
    },
  });
}
```

- [ ] **Step 2: Verificar**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores TS.

- [ ] **Step 3: Commit**

```bash
git add web/src/features/compras/hooks/useRecibirParcial.ts
git commit -m "feat(compras): hook useRecibirParcial"
```

---

## Fase 5 — Frontend: modal por línea + detalle + badge

### Task 8: Reescribir `RegistrarRecepcionModal` como tabla por línea

**Files:**
- Modify: `web/src/features/compras/components/RegistrarRecepcionModal.tsx`

- [ ] **Step 1: Reemplazar el archivo completo**

```tsx
// Recepción parcial incremental de OC. Tabla por línea: el usuario captura
// "recibir ahora" (delta) por línea (máx = pendiente). POST /recibir-parcial.

import { useState } from 'react';
import { Modal, ModalFooter } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from '@/lib/toast';
import { useOrdenCompraDetalle } from '../hooks/useOrdenCompraDetalle';
import { useRecibirParcial } from '../hooks/useRecibirParcial';
import type { OrdenCompraLinea } from '../types';

type Props = {
  id: number;
  folio: string | null;
  onClose: () => void;
};

function pendiente(l: OrdenCompraLinea) {
  return l.cantidad - (l.cantidad_recibida ?? 0);
}

export function RegistrarRecepcionModal({ id, folio, onClose }: Props) {
  const { data: oc, isLoading } = useOrdenCompraDetalle(id);
  const recibir = useRecibirParcial(id);
  const [cantidades, setCantidades] = useState<Record<number, string>>({});
  const [fecha, setFecha] = useState('');

  const lineas = oc?.detalles ?? [];

  function recibirTodo() {
    const next: Record<number, string> = {};
    lineas.forEach((l) => { const p = pendiente(l); if (p > 0) next[l.id] = String(p); });
    setCantidades(next);
  }

  function onSubmit() {
    const payloadLineas = lineas
      .map((l) => ({ detalle_compra_id: l.id, cantidad: parseInt(cantidades[l.id] ?? '0', 10) || 0 }))
      .filter((x) => x.cantidad > 0);
    if (payloadLineas.length === 0) {
      toast({ kind: 'warning', title: 'Captura al menos una cantidad a recibir' });
      return;
    }
    recibir.mutate(
      { lineas: payloadLineas, fecha: fecha || null },
      {
        onSuccess: (data) => {
          toast({
            kind: 'success',
            title: data.estatus === 'recibido' ? 'OC recibida por completo' : 'Recepción parcial registrada',
            description: `${data.procesados} línea(s) actualizada(s).`,
          });
          onClose();
        },
        onError: (e) => {
          if (e.status === 401) { window.location.href = '/spa/login'; return; }
          if (e.status === 403) { toast({ kind: 'error', title: 'Sin permiso', description: 'Se requiere rol admin o asistente.' }); return; }
          toast({ kind: 'error', title: 'Error al recibir OC', description: e.detail });
        },
      },
    );
  }

  return (
    <Modal title={`Recepción de OC ${folio ?? `#${id}`}`} onClose={onClose} size="xl">
      {isLoading ? (
        <p className="text-sm text-slate-500">Cargando líneas…</p>
      ) : (
        <div className="space-y-3 text-sm">
          <div className="flex items-end justify-between gap-3 flex-wrap">
            <label className="text-xs text-slate-500">
              Fecha de recepción
              <Input type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} className="mt-1 w-44" />
            </label>
            <Button variant="outline" size="sm" onClick={recibirTodo}>Recibir todo lo pendiente</Button>
          </div>
          <table className="w-full text-xs">
            <thead className="text-slate-500 uppercase">
              <tr>
                <th className="text-left p-1.5">Descripción</th>
                <th className="p-1.5 text-center w-16">Pedido</th>
                <th className="p-1.5 text-center w-20">Recibido</th>
                <th className="p-1.5 text-center w-28">Recibir ahora</th>
              </tr>
            </thead>
            <tbody>
              {lineas.map((l) => {
                const p = pendiente(l);
                return (
                  <tr key={l.id} className="border-t border-slate-100 dark:border-slate-800">
                    <td className="p-1.5">
                      <div className="text-slate-800 dark:text-slate-200">
                        {l.producto?.nombre ?? l.descripcion_libre ?? l.sku_libre ?? '—'}
                        {l.producto_id == null && <span className="ml-1 text-[10px] text-amber-500">fantasma</span>}
                      </div>
                      {(l.clave_unidad_sat || l.clave_prod_serv) && (
                        <div className="text-[10px] font-mono text-slate-400">SAT {l.clave_prod_serv ?? '—'} · {l.clave_unidad_sat ?? '—'}</div>
                      )}
                    </td>
                    <td className="p-1.5 text-center">{l.cantidad}</td>
                    <td className="p-1.5 text-center">{l.cantidad_recibida ?? 0}</td>
                    <td className="p-1.5 text-center">
                      <Input
                        type="number"
                        min="0"
                        max={p}
                        value={cantidades[l.id] ?? ''}
                        disabled={p <= 0}
                        onChange={(e) => {
                          const v = Math.max(0, Math.min(p, parseInt(e.target.value, 10) || 0));
                          setCantidades((s) => ({ ...s, [l.id]: String(v) }));
                        }}
                        className="h-7 w-20 text-center inline-block"
                      />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <p className="text-[11px] text-slate-400">
            Las líneas de catálogo ingresan a inventario por lo recibido (kardex). Las líneas fantasma solo registran la recepción; su stock entra al promoverlas.
          </p>
        </div>
      )}
      <ModalFooter>
        <Button variant="ghost" size="sm" onClick={onClose} disabled={recibir.isPending}>Cancelar</Button>
        <Button size="sm" onClick={onSubmit} disabled={recibir.isPending || isLoading}>
          {recibir.isPending ? 'Procesando…' : 'Registrar recepción'}
        </Button>
      </ModalFooter>
    </Modal>
  );
}
```

- [ ] **Step 2: Verificar**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores TS.

- [ ] **Step 3: Commit**

```bash
git add web/src/features/compras/components/RegistrarRecepcionModal.tsx
git commit -m "feat(compras): recepción parcial por línea con fecha + recibir-todo (US-027)"
```

### Task 9: Mostrar recibido/SAT en `OrdenCompraDetalleModal` + badge parcial

**Files:**
- Modify: `web/src/features/compras/components/OrdenCompraDetalleModal.tsx`
- Modify: `web/src/features/compras/pages/ComprasPage.tsx`

- [ ] **Step 1: Columna "Recibido" + SAT en el detalle**

Leer `OrdenCompraDetalleModal.tsx`. En la tabla de líneas (la que itera `oc.detalles` con celdas SKU/descripción, Cant., Costo unit., Importe):
- Agregar un encabezado `<th>` "Recibido" después de la columna de cantidad (`Cant.`).
- En cada fila, después de la celda de `{d.cantidad}`, agregar:
```tsx
        <td className="text-center">{d.cantidad_recibida ?? 0}/{d.cantidad}</td>
```
- Bajo la descripción/SKU de cada fila, si hay SAT, agregar un subtexto:
```tsx
        {(d.clave_unidad_sat || d.clave_prod_serv) && (
          <div className="text-[10px] font-mono text-slate-400">SAT {d.clave_prod_serv ?? '—'} · {d.clave_unidad_sat ?? '—'}</div>
        )}
```
(Ajustar el `colSpan` de filas vacías/estado si el componente lo usa, para que cuadre con la nueva columna.)

- [ ] **Step 2: Badge para `recibida_parcial` en `ComprasPage`**

En `ComprasPage.tsx`, en la función `badgeEstatus` (el objeto `map` con `borrador: 'slate'`, `recibido: 'emerald'`, …), agregar la entrada:
```tsx
    recibida_parcial: 'amber',
```
Y en el array de filtros de estatus (`{ value: 'recibido', label: 'Recibida' }`, ~línea 26), agregar después:
```tsx
  { value: 'recibida_parcial', label: 'Recibida parcial' },
```

- [ ] **Step 3: Verificar**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores TS.

- [ ] **Step 4: Commit**

```bash
git add web/src/features/compras/components/OrdenCompraDetalleModal.tsx web/src/features/compras/pages/ComprasPage.tsx
git commit -m "feat(compras): detalle muestra recibido/SAT + badge recibida_parcial (US-026/027)"
```

---

## Fase 6 — Build final + push

### Task 10: Build del SPA y push

- [ ] **Step 1: Build final**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores; `app/static/dist/` regenerado.

- [ ] **Step 2: Commit del dist + push**

```bash
git add app/static/dist
git commit -m "build: recompila SPA (dist) — US-026/027 OC fantasma + recepción parcial"
git push origin main
```

---

## Notas de verificación manual (post-deploy, recomendado)

- Cotización con una línea fantasma → generar OC (grouping/confirmar) → en el detalle de la OC confirmar que la línea muestra su marca/SAT.
- Recepción parcial: OC con A=10, B=5 → recibir A=6, B=5 → la OC queda "recibida parcial"; A muestra 6/10. En Inventario, A subió 6 (B es catálogo: subió 5; si B fuera fantasma, no movería stock).
- Segunda recepción A=4 → la OC pasa a "recibido"; A 10/10.
- Intentar recibir más del pendiente → el input lo limita en UI y el backend responde 400 si se fuerza.
- "Recibir todo lo pendiente" pre-llena los inputs con el faltante de cada línea.
- Línea fantasma recibida → cantidad_recibida sube, sin movimiento de stock; luego Promover (US-009) crea el producto + ENTRADA.

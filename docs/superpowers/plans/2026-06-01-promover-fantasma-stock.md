# Promover Fantasma a Producto + Stock — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promover un producto fantasma a producto real del catálogo con SKU editable/sugerido y entrada de stock auditada (kardex), como acción manual desde un modal.

**Architecture:** Sin migración. El endpoint `POST /api/fantasmas/{id}/promover` se extiende para aceptar `{sku, cantidad, stock_minimo}`, copiar todos los campos del fantasma, validar SKU único y registrar la entrada vía `aplicar_movimiento`. Un endpoint `GET /api/fantasmas/{id}/sugerir-sku` precalcula el SKU. El frontend reemplaza el confirm directo por un `PromoverModal`.

**Tech Stack:** FastAPI + SQLAlchemy 2.x (Postgres); React 18 + Vite + TS + Tailwind + TanStack Query.

**Verificación (este repo NO tiene suite de tests — CLAUDE.md):** backend con `python3 -m py_compile <archivos>`; frontend con `cd web && npm run build`. No hay migración (no se agregan columnas). Checks manuales recomendados post-deploy.

**Referencia de diseño:** `docs/superpowers/specs/2026-06-01-promover-fantasma-stock-design.md`.

---

## Fase 1 — Backend

### Task 1: Schema `PromoverFantasmaInput`

**Files:**
- Modify: `app/schemas/fantasmas.py`

- [ ] **Step 1: Agregar el schema**

Al final de `app/schemas/fantasmas.py`, agregar:

```python
class PromoverFantasmaInput(BaseModel):
    sku: str
    cantidad: int = 0          # entrada inicial de stock; 0 = solo crear catálogo
    stock_minimo: Optional[int] = None
```

(El archivo ya importa `BaseModel`/`Field` de pydantic y `Optional` de typing — no agregar imports.)

- [ ] **Step 2: Verificar**

Run: `python3 -m py_compile app/schemas/fantasmas.py`
Expected: sin salida (OK).

- [ ] **Step 3: Commit**

```bash
git add app/schemas/fantasmas.py
git commit -m "feat(schemas): PromoverFantasmaInput (sku + cantidad + stock_minimo)"
```

### Task 2: Endpoint `sugerir-sku` + `promover` extendido

**Files:**
- Modify: `app/routers/fantasmas.py`

- [ ] **Step 1: Agregar imports**

En la cabecera de imports de `app/routers/fantasmas.py`, después de `from app.security.jwt import allow_admin`, agregar:

```python
from app.models.enums import TipoMovimientoStock
from app.routers.catalogos import siguiente_sku_para
from app.services.stock_service import aplicar_movimiento
```

> Verificado: `catalogos.py` no importa `fantasmas` → sin import circular.

- [ ] **Step 2: Agregar el endpoint `sugerir-sku`**

Justo antes del endpoint `@router.post("/{id}/promover", ...)`, agregar:

```python
@router.get("/{id}/sugerir-sku", dependencies=[Depends(allow_all_staff)])
def sugerir_sku_fantasma(id: int, db: Session = Depends(get_db)):
    """Sugiere un SKU para promover: usa sku_libre si existe; si no y hay
    marca con abreviatura, genera {ABREV}-NNNN; si no, cadena vacía."""
    f = db.query(models.ProductoFantasma).filter(models.ProductoFantasma.id == id).first()
    if not f:
        raise HTTPException(404, "Fantasma no encontrado")
    if f.sku_libre:
        return {"sku_sugerido": f.sku_libre}
    abrev = None
    if f.marca_id and f.marca_rel and f.marca_rel.abreviatura:
        abrev = f.marca_rel.abreviatura
    if abrev:
        return {"sku_sugerido": siguiente_sku_para(db, abrev)}
    return {"sku_sugerido": ""}
```

- [ ] **Step 3: Reemplazar el cuerpo de `promover_fantasma`**

Reemplazar la función `promover_fantasma` completa por:

```python
@router.post("/{id}/promover", dependencies=[Depends(allow_admin)])
def promover_fantasma(
    id: int,
    payload: schemas.PromoverFantasmaInput,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    """Convierte un fantasma a Producto del catálogo. Copia los campos del
    fantasma (incl. marca/SAT), valida SKU único y registra la entrada de
    stock vía kardex (aplicar_movimiento) si cantidad > 0. Marca el fantasma
    como PROMOVIDO y deja referencia al producto creado."""
    f = db.query(models.ProductoFantasma).filter(models.ProductoFantasma.id == id).first()
    if not f:
        raise HTTPException(404, "Fantasma no encontrado")
    if f.estado in ("PROMOVIDO", "DESCARTADO"):
        raise HTTPException(409, f"Fantasma ya está en estado {f.estado}")

    sku = (payload.sku or "").strip()
    if not sku:
        raise HTTPException(400, "El SKU es obligatorio para promover")
    if payload.cantidad < 0:
        raise HTTPException(400, "La cantidad no puede ser negativa")
    existe = db.query(models.Producto).filter(models.Producto.sku == sku).first()
    if existe:
        raise HTTPException(409, f"Ya existe un producto con el SKU {sku}")

    try:
        nuevo = models.Producto(
            sku=sku,
            nombre=f.descripcion_original[:150],
            descripcion=f.descripcion_original,
            costo_compra=f.costo_referencia,
            moneda_compra=f.moneda_referencia,
            marca=f.marca,
            marca_id=f.marca_id,
            clave_prod_serv=f.clave_prod_serv,
            clave_unidad_sat=f.clave_unidad_sat,
            stock_actual=0,
            proveedor_principal_id=f.proveedor_sugerido_id,
        )
        if payload.stock_minimo is not None:
            nuevo.stock_minimo = payload.stock_minimo
        db.add(nuevo)
        db.flush()

        if payload.cantidad > 0:
            aplicar_movimiento(
                db,
                producto=nuevo,
                tipo=TipoMovimientoStock.ENTRADA.value,
                cantidad=int(payload.cantidad),
                referencia_tipo="promocion_fantasma",
                referencia_id=f.id,
                motivo=f"Promoción fantasma → {sku}",
                usuario=current_user,
            )

        f.estado = "PROMOVIDO"
        f.promovido_a_producto_id = nuevo.id
        db.commit()
        return {
            "fantasma_id": f.id,
            "producto_id": nuevo.id,
            "sku": nuevo.sku,
            "stock_inicial": int(payload.cantidad),
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("fantasmas.promover_fantasma falló (fantasma_id=%s)", id)
        raise HTTPException(500, detail=f"{type(exc).__name__}: {exc}")
```

> Nota: `marca` y `marca_id` existen en `Producto` (catalog.py). `clave_prod_serv`/`clave_unidad_sat` también. `aplicar_movimiento` con `ENTRADA` fija `stock_actual` y registra `movimientos_stock`.

- [ ] **Step 4: Verificar**

Run: `python3 -m py_compile app/routers/fantasmas.py`
Expected: sin salida (OK).

- [ ] **Step 5: Commit**

```bash
git add app/routers/fantasmas.py
git commit -m "feat(api): promover fantasma copia marca/SAT + stock auditado (kardex) + sugerir-sku (US-009)"
```

---

## Fase 2 — Frontend

### Task 3: Tipos + modal de promover

**Files:**
- Modify: `web/src/features/fantasmas/types.ts`
- Create: `web/src/features/fantasmas/components/PromoverModal.tsx`

- [ ] **Step 1: Tipos**

Al final de `web/src/features/fantasmas/types.ts`, agregar:

```ts
export type PromoverInput = {
  sku: string;
  cantidad: number;
  stock_minimo: number | null;
};

export type PromoverResponse = {
  fantasma_id: number;
  producto_id: number;
  sku: string;
  stock_inicial: number;
};

export type SugerirSkuResponse = { sku_sugerido: string };
```

- [ ] **Step 2: Crear `PromoverModal.tsx`**

```tsx
import { useEffect, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowUp, X } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';
import { toast } from '@/lib/toast';
import type { Fantasma } from '../types';
import type { PromoverInput, PromoverResponse, SugerirSkuResponse } from '../types';

export function PromoverModal({
  fantasma,
  onClose,
}: {
  fantasma: Fantasma;
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const [sku, setSku] = useState(fantasma.sku_libre ?? '');
  const [cantidad, setCantidad] = useState('0');
  const [stockMinimo, setStockMinimo] = useState('');
  const [err, setErr] = useState<string | null>(null);

  // Pre-llenar el SKU sugerido por el backend (sku_libre o {ABREV}-NNNN).
  useEffect(() => {
    let activo = true;
    api
      .get<SugerirSkuResponse>(`/api/fantasmas/${fantasma.id}/sugerir-sku`)
      .then((r) => { if (activo && r.sku_sugerido) setSku((prev) => prev || r.sku_sugerido); })
      .catch(() => { /* sin sugerencia: el usuario escribe el SKU */ });
    return () => { activo = false; };
  }, [fantasma.id]);

  const mut = useMutation<PromoverResponse, { status?: number; detail?: string }, PromoverInput>({
    mutationFn: (payload) => api.post<PromoverResponse>(`/api/fantasmas/${fantasma.id}/promover`, payload),
    onSuccess: (r) => {
      qc.invalidateQueries({ queryKey: ['fantasmas'] });
      qc.invalidateQueries({ queryKey: ['productos'] });
      toast({ kind: 'success', title: `Promovido a ${r.sku}`, description: r.stock_inicial > 0 ? `Entrada de ${r.stock_inicial} al inventario` : 'Producto creado sin stock inicial' });
      onClose();
    },
    onError: (e) => {
      if (e.status === 401) { window.location.href = '/spa/login'; return; }
      setErr(e.detail ?? 'No se pudo promover');
    },
  });

  function onSubmit() {
    setErr(null);
    const skuTrim = sku.trim();
    if (!skuTrim) { setErr('El SKU es obligatorio.'); return; }
    const cant = parseInt(cantidad, 10);
    if (!Number.isFinite(cant) || cant < 0) { setErr('La cantidad debe ser 0 o mayor.'); return; }
    const min = stockMinimo.trim() === '' ? null : parseInt(stockMinimo, 10);
    mut.mutate({ sku: skuTrim, cantidad: cant, stock_minimo: Number.isFinite(min as number) ? (min as number) : null });
  }

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-slate-900 border border-violet-700/50 rounded-xl shadow-2xl max-w-md w-full">
        <div className="flex items-center justify-between px-5 pt-5 pb-3 border-b border-slate-200 dark:border-slate-800">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <ArrowUp className="h-4 w-4 text-violet-500" /> Promover a producto
          </h3>
          <button type="button" onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="px-5 py-4 space-y-3">
          <p className="text-xs text-slate-500 truncate" title={fantasma.descripcion}>{fantasma.descripcion}</p>
          <div>
            <label className="block text-xs text-slate-500 mb-1">SKU del producto *</label>
            <Input value={sku} onChange={(e) => setSku(e.target.value)} className="font-mono" placeholder="Ej. SCHN-0007" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-slate-500 mb-1">Cantidad recibida</label>
              <Input type="number" min="0" value={cantidad} onChange={(e) => setCantidad(e.target.value)} className="text-right" />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">Stock mínimo (opcional)</label>
              <Input type="number" min="0" value={stockMinimo} onChange={(e) => setStockMinimo(e.target.value)} className="text-right" />
            </div>
          </div>
          <p className="text-[11px] text-slate-400">Cantidad 0 crea el producto sin entrada de stock. Cualquier cantidad &gt; 0 registra una ENTRADA auditada en el kardex.</p>
          {err && <div className="text-xs bg-rose-50 dark:bg-rose-900/30 border border-rose-300 dark:border-rose-700/50 rounded p-2 text-rose-700 dark:text-rose-300">{err}</div>}
        </div>
        <div className="flex justify-end gap-2 px-5 py-4 border-t border-slate-200 dark:border-slate-800">
          <Button variant="ghost" size="sm" onClick={onClose} disabled={mut.isPending}>Cancelar</Button>
          <Button size="sm" onClick={onSubmit} disabled={mut.isPending}>{mut.isPending ? 'Promoviendo…' : 'Promover'}</Button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Verificar**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores TS.

- [ ] **Step 4: Commit**

```bash
git add web/src/features/fantasmas/types.ts web/src/features/fantasmas/components/PromoverModal.tsx
git commit -m "feat(fantasmas): PromoverModal — SKU sugerido/editable + cantidad + stock mínimo (US-009)"
```

### Task 4: Cablear el modal en `FantasmasPage`

**Files:**
- Modify: `web/src/features/fantasmas/pages/FantasmasPage.tsx`

- [ ] **Step 1: Importar el modal**

Cerca de los otros imports de componentes de la feature en `FantasmasPage.tsx`, agregar:

```tsx
import { PromoverModal } from '../components/PromoverModal';
```

- [ ] **Step 2: Estado del modal**

Junto a los otros `useState` de la página (p. ej. donde está `modalDetalle`/`modalEditar`), agregar:

```tsx
  const [promoverTarget, setPromoverTarget] = useState<Fantasma | null>(null);
```

- [ ] **Step 3: Reemplazar `onPromover` para abrir el modal**

Localizar la función `onPromover` (hace `window.confirm` + `promoverMut.mutate(f.id)`) y reemplazarla por:

```tsx
  function onPromover(f: Fantasma) {
    setPromoverTarget(f);
  }
```

Eliminar el `useMutation` `promoverMut` (el bloque `const promoverMut = useMutation<...>({ ... });`) ya que la mutación vive ahora en `PromoverModal`. Si algún otro punto referencia `promoverMut`, quitar esa referencia (solo la usaba `onPromover`).

- [ ] **Step 4: Renderizar el modal**

Junto a los demás modales renderizados al final del JSX de la página (p. ej. donde se renderiza el modal de detalle/editar), agregar:

```tsx
      {promoverTarget && (
        <PromoverModal fantasma={promoverTarget} onClose={() => setPromoverTarget(null)} />
      )}
```

- [ ] **Step 5: Verificar**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores TS. Si el build reporta `promoverMut` o imports sin usar (`useMutation`, `api`, `toast`) que quedaron huérfanos tras quitar la mutación, eliminarlos del archivo hasta que el build pase limpio.

- [ ] **Step 6: Commit**

```bash
git add web/src/features/fantasmas/pages/FantasmasPage.tsx
git commit -m "feat(fantasmas): el botón Promover abre PromoverModal (US-009)"
```

---

## Fase 3 — Build final + push

### Task 5: Build del SPA y push

- [ ] **Step 1: Build final**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores; `app/static/dist/` regenerado.

- [ ] **Step 2: Commit del dist + push**

```bash
git add app/static/dist
git commit -m "build: recompila SPA (dist) — US-009 promover fantasma a stock"
git push origin main
```

---

## Notas de verificación manual (post-deploy, recomendado)

- Editar un fantasma con marca asignada y SIN sku_libre → abrir Promover → confirmar que el SKU se pre-llena con `{ABREV}-NNNN`.
- Promover con cantidad 5 → verificar en Inventario que el producto aparece con stock 5, y en el kardex (`movimientos_stock` / timeline) una ENTRADA de 5 con motivo "Promoción fantasma → SKU".
- Promover con cantidad 0 → producto creado con stock 0, sin movimiento de kardex.
- Intentar promover con un SKU que ya existe → el modal muestra el error 409.
- Confirmar que el fantasma pasa a estado PROMOVIDO y queda vinculado (`promovido_a_producto_id`).

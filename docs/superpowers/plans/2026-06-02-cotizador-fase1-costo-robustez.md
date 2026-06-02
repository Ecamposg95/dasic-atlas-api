# Cotizador Fase 1 (costo origen fijo + robustez P0/P1) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mostrar siempre el costo de origen fijo (divisa+valor) en el carrito y endurecer el cotizador contra guardados inválidos / pérdida de carrito.

**Architecture:** Cambios de visibilidad/etiquetado en CartRow/RowExpanded (el costo de origen ya es fijo), una regla extra de bloqueo de guardado + toast de error en TotalsBar, un guard `beforeunload` en CotizadorPage, y validación de `detalles` (≥1, ≤500) + mensaje amable de cliente en el backend.

**Tech Stack:** React 18 + Vite + TS + Zustand; FastAPI + Pydantic.

**Verificación (este repo NO tiene suite de tests — CLAUDE.md):** frontend `cd web && npm run build`; backend `python3 -m py_compile`. Checks manuales recomendados.

**Referencia de diseño:** `docs/superpowers/specs/2026-06-02-cotizador-fase1-costo-robustez-design.md`.

---

## Fase A — Costo de origen siempre visible

### Task 1: CartRow + RowExpanded muestran el costo de origen fijo

**Files:**
- Modify: `web/src/features/cotizador/components/CartRow.tsx`
- Modify: `web/src/features/cotizador/components/RowExpanded.tsx`

- [ ] **Step 1: CartRow — quitar el gating `mostrarOrigen`**

En `CartRow.tsx`, eliminar la declaración (queda sin uso):
```tsx
  const mostrarOrigen =
    item.productCurrency !== moneda || Number(item.descuento_proveedor || 0) > 0;
```
Y reemplazar el bloque condicional del costo origen:
```tsx
        {mostrarOrigen && (
          <div
            className="text-[10px] text-slate-500 leading-tight"
            title="Costo crudo del catálogo en su moneda nativa (sin TC, sin descuentos)"
          >
            {item.productCurrency} ${fmt(Number(item.cost))}
          </div>
        )}
```
por (siempre visible, etiquetado "Orig"):
```tsx
        <div
          className="text-[10px] text-slate-500 leading-tight"
          title="Costo de origen: crudo del catálogo en su moneda nativa — fijo, NO cambia al cambiar la moneda de la cotización"
        >
          <span className="text-slate-600">Orig</span> {item.productCurrency} ${fmt(Number(item.cost))}
        </div>
```

- [ ] **Step 2: RowExpanded — agregar el valor del costo de origen**

En `RowExpanded.tsx`, en la celda "Moneda origen", después de la línea del `{fuente}`:
```tsx
            <div className="text-[10px] text-slate-500 mt-0.5">{fuente}</div>
```
agregar:
```tsx
            <div className="text-[10px] text-slate-400 mt-0.5 font-mono">
              Costo origen: {item.productCurrency} ${Number(item.cost).toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
```

- [ ] **Step 3: Verificar**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores TS (ojo: si quedó `mostrarOrigen` sin usar, el build falla → confirmar que se eliminó).

- [ ] **Step 4: Commit**

```bash
git add web/src/features/cotizador/components/CartRow.tsx web/src/features/cotizador/components/RowExpanded.tsx
git commit -m "feat(cotizador): muestra siempre el costo de origen fijo (divisa+valor) en el carrito"
```

---

## Fase B — Robustez P0/P1

### Task 2: TotalsBar — bloquear cantidad 0 + toast en fallo de guardado

**Files:**
- Modify: `web/src/features/cotizador/components/TotalsBar.tsx`

- [ ] **Step 1: Import de toast**

Agregar (junto a los otros imports de `@/lib/...`):
```tsx
import { toast } from '@/lib/toast';
```

- [ ] **Step 2: Bloquear líneas con cantidad ≤ 0**

En el bloque de `reasons`, después de `if (cliente_id == null) reasons.push('selecciona cliente');`, agregar:
```tsx
  if (cart.some((l) => l.qty <= 0)) reasons.push('hay líneas con cantidad 0');
```
(`disabled = reasons.length > 0 || guardar.isPending` ya existe → el botón se bloquea.)

- [ ] **Step 3: Toast en fallo de guardado (conservando el carrito)**

En el `onError` de `guardar.mutate(...)`, antes de `setErr(...)`, agregar el toast (la redirección sigue SOLO en `onSuccess`; el carrito no se limpia en error):
```tsx
        onError: (e: { status?: number; detail?: string }) => {
          if (e.status === 401) {
            window.location.href = '/spa/login';
            return;
          }
          toast({ kind: 'error', title: 'No se pudo guardar la cotización', description: e.detail });
          setErr(e.detail || 'No se pudo guardar la cotización');
        },
```

- [ ] **Step 4: Verificar**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores TS.

- [ ] **Step 5: Commit**

```bash
git add web/src/features/cotizador/components/TotalsBar.tsx
git commit -m "feat(cotizador): bloquea guardar con cantidad 0 + toast claro al fallar (conserva carrito)"
```

### Task 3: CotizadorPage — aviso `beforeunload` con cambios sin guardar

**Files:**
- Modify: `web/src/features/cotizador/pages/CotizadorPage.tsx`

- [ ] **Step 1: Guard beforeunload**

Junto a los otros `useEffect` del componente `CotizadorPage`, agregar:
```tsx
  // Aviso nativo del navegador al cerrar/recargar con líneas sin guardar.
  useEffect(() => {
    function onBeforeUnload(e: BeforeUnloadEvent) {
      if (useCotizador.getState().cart.length > 0) {
        e.preventDefault();
        e.returnValue = '';
      }
    }
    window.addEventListener('beforeunload', onBeforeUnload);
    return () => window.removeEventListener('beforeunload', onBeforeUnload);
  }, []);
```
(`useEffect` y `useCotizador` ya están importados en el archivo.)

- [ ] **Step 2: Verificar**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores TS.

- [ ] **Step 3: Commit**

```bash
git add web/src/features/cotizador/pages/CotizadorPage.tsx
git commit -m "feat(cotizador): aviso beforeunload al salir con líneas sin guardar"
```

### Task 4: Backend — validar detalles + mensaje amable de cliente

**Files:**
- Modify: `app/schemas/sales.py`
- Modify: `app/routers/ventas.py`

- [ ] **Step 1: `OrdenVentaCreate.detalles` con `min_length`/`max_length`**

En `app/schemas/sales.py`, en `OrdenVentaCreate`, reemplazar:
```python
    detalles: List[DetalleOrdenCreate]
```
por:
```python
    detalles: List[DetalleOrdenCreate] = Field(..., min_length=1, max_length=500)
```
(`Field` ya está importado en ese módulo.)

- [ ] **Step 2: Mensaje amable si el cliente no existe**

En `app/routers/ventas.py` (línea ~588), reemplazar:
```python
    if not cliente: raise HTTPException(404, "Cliente no encontrado")
```
por:
```python
    if not cliente: raise HTTPException(422, "Selecciona un cliente válido para guardar la cotización.")
```

- [ ] **Step 3: Verificar**

Run: `python3 -m py_compile app/schemas/sales.py app/routers/ventas.py`
Expected: sin salida (OK).

- [ ] **Step 4: Commit**

```bash
git add app/schemas/sales.py app/routers/ventas.py
git commit -m "feat(api): OrdenVentaCreate exige 1-500 líneas + 422 amable si falta cliente"
```

---

## Fase C — Build final + push

### Task 5: Build del SPA y push

- [ ] **Step 1: Build final**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores; `app/static/dist/` regenerado.

- [ ] **Step 2: Commit del dist + push**

```bash
git add app/static/dist
git commit -m "build: recompila SPA (dist) — cotizador fase 1 (costo origen + robustez)"
git push origin main
```

---

## Notas de verificación manual (post-deploy, recomendado)

- En el carrito, cada producto muestra "Orig {MXN/USD} $valor" SIEMPRE (aunque la línea coincida con la moneda de la cotización), y ese número NO cambia al cambiar la moneda de la cotización; el "OC" sí (correcto).
- En el panel expandido aparece "Costo origen: {divisa} $valor".
- Intentar guardar con una línea en cantidad 0 → botón deshabilitado con razón "hay líneas con cantidad 0".
- Simular fallo de guardado (p. ej. red) → aparece toast de error, el carrito se conserva, NO redirige.
- Cerrar/recargar la pestaña con líneas en el carrito → el navegador pide confirmación.
- Backend: POST /api/ventas con `detalles: []` → 422 (≥1 línea requerida).

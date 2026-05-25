# TC explícito en el cotizador — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mostrar al usuario los 3 TCs (DOF, MN→USD, USD→MN) en el header del cotizador como una mini-tabla read-only, con badges verdes para los deltas ±1 y resaltado de la columna que se aplica al cart actual.

**Architecture:** Cambio puramente de UI (frontend SPA). Backend, cálculos y persistencia ya funcionan correctamente con el modelo Excel V_03. Se crea un componente nuevo `TCMiniTable.tsx`, se adelgaza `FXBadge.tsx` a una línea informativa, y se reordena `HeaderCotizacion.tsx` para meter la mini-tabla bajo el input TC. Los valores que muestra la mini-tabla provienen de la misma función (`resolveDirectionalTcs`) que ya consumen `CartRow` y `TotalsBar` para el cálculo real — single source of truth.

**Tech Stack:** React 18 + TypeScript, Zustand (store `useCotizador`), TanStack Query v5 (hook `useFX`), Tailwind, shadcn/ui, Lucide icons.

**Spec:** `docs/superpowers/specs/2026-05-25-tc-explicito-cotizador-design.md`

---

## File Structure

**Crear:**
- `web/src/features/cotizador/components/TCMiniTable.tsx` — presentación de los 3 TCs + refresh row. ≤120 líneas. Lee `store.tc` + `store.tc_mn_a_usd` + `store.tc_usd_a_mn` + `store.moneda` + `store.cart` directamente.

**Modificar:**
- `web/src/features/cotizador/components/HeaderCotizacion.tsx` — sustituir el bloque `<FXBadge />` + botón "Pisar TC manualmente" por `<TCMiniTable />`. El input editable del TC se mantiene como está. El link "Pisar TC manualmente" se mueve dentro de la mini-tabla.
- `web/src/features/cotizador/components/FXBadge.tsx` — adelgazar a una sola línea pequeña (solo `↻ Banxico · YYYY-MM-DD`). Conserva el callback `setTc` al refrescar.

**Sin cambios:**
- `web/src/features/cotizador/store.ts`
- `web/src/features/cotizador/lib/calc.ts`
- `web/src/features/cotizador/lib/serialize.ts`
- `web/src/features/cotizador/components/CartRow.tsx`
- `web/src/features/cotizador/components/RowExpanded.tsx`
- `web/src/features/cotizador/components/TotalsBar.tsx`
- `app/` (backend), `migrations/`

---

### Task 1: Crear `TCMiniTable.tsx`

Componente presentacional. Lee del store y del hook `useFX` (para la línea de refresh arriba). Llama `resolveDirectionalTcs` para obtener los valores que el cálculo realmente aplica.

**Files:**
- Create: `web/src/features/cotizador/components/TCMiniTable.tsx`

- [ ] **Step 1: Crear el archivo con el componente completo**

```tsx
// web/src/features/cotizador/components/TCMiniTable.tsx
import { RefreshCw, ArrowDown, ArrowUp, ShieldAlert } from 'lucide-react';
import { useCotizador } from '../store';
import { resolveDirectionalTcs } from '../lib/calc';
import { useFX, useFXRefresh } from '../hooks/useFX';
import { useIsAdmin } from '@/lib/permissions';
import { toast } from '@/lib/toast';
import type { ApiError } from '@/lib/api';

function fmt4(n: number) {
  return n.toLocaleString('es-MX', { minimumFractionDigits: 4, maximumFractionDigits: 4 });
}

function fmtDelta(n: number) {
  const abs = Math.abs(n);
  return abs.toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function TCMiniTable() {
  const tc = useCotizador((s) => s.tc);
  const tcMnAUsd = useCotizador((s) => s.tc_mn_a_usd);
  const tcUsdAMn = useCotizador((s) => s.tc_usd_a_mn);
  const moneda = useCotizador((s) => s.moneda);
  const cart = useCotizador((s) => s.cart);
  const setTc = useCotizador((s) => s.setTc);
  const esAdmin = useIsAdmin();

  const { data: fx } = useFX();
  const refresh = useFXRefresh();

  // Single source of truth: los mismos valores que CartRow/TotalsBar usan
  // para convertir líneas. Si los direccionales no se override-aron en
  // la cot, salen DOF±1.
  const tcs = resolveDirectionalTcs(tc, tcMnAUsd, tcUsdAMn);
  const deltaMnAUsd = tcs.tc_mn_a_usd - tc;   // típicamente −1
  const deltaUsdAMn = tcs.tc_usd_a_mn - tc;   // típicamente +1

  // Columna "activa" = la que se aplica al cart actual.
  const hayLineasOtraMoneda = cart.some((i) => i.productCurrency && i.productCurrency !== moneda);
  const aplicaMnAUsd = moneda === 'USD' && cart.some((i) => i.productCurrency === 'MXN');
  const aplicaUsdAMn = moneda === 'MXN' && cart.some((i) => i.productCurrency === 'USD');
  const tcNecesario = moneda === 'USD' || hayLineasOtraMoneda;

  const tcInvalido = !Number.isFinite(tc) || tc <= 0;

  async function onRefresh() {
    try {
      const r = await refresh.mutateAsync();
      const nuevoTc = Number(r.usd_mxn);
      if (Number.isFinite(nuevoTc) && nuevoTc > 0) {
        setTc(nuevoTc);
        toast({
          kind: 'success',
          title: 'TC actualizado',
          description: `${r.fuente}: $${nuevoTc.toFixed(4)} (${r.fecha})`,
        });
      }
    } catch (e) {
      const err = e as ApiError;
      toast({ kind: 'error', title: 'No se pudo refrescar', description: err.detail });
    }
  }

  const containerClass = tcNecesario ? '' : 'opacity-60';
  const activeColClass = 'border-accent-glow/60 bg-slate-950/80 text-slate-100';
  const idleColClass = 'border-slate-800 bg-slate-900/40 text-slate-400';
  const deltaBadge =
    'inline-flex items-center gap-0.5 text-[10px] font-bold px-1 py-px rounded ' +
    'bg-emerald-950/50 border border-emerald-700/50 text-emerald-300';

  return (
    <div className={`mt-1 space-y-1 ${containerClass}`}>
      <div className="flex items-center justify-between gap-2">
        <button
          type="button"
          onClick={onRefresh}
          disabled={refresh.isPending || !fx}
          className="text-[10px] flex items-center gap-1 text-slate-400 hover:text-accent-glow transition disabled:opacity-50"
          title="Refrescar TC oficial desde Banxico"
        >
          <RefreshCw className={`h-2.5 w-2.5 ${refresh.isPending ? 'animate-spin' : ''}`} />
          <span>
            {fx
              ? `${fx.fuente} · ${fx.fecha}`
              : 'Cargando TC…'}
          </span>
        </button>
        {esAdmin && (
          <button
            type="button"
            onClick={() => window.dispatchEvent(new CustomEvent('cot:open-pisartc'))}
            className="text-[10px] text-amber-400 hover:underline flex items-center gap-1"
            title="Pisar el TC solo para esta cotización"
          >
            <ShieldAlert className="h-2.5 w-2.5" /> Pisar TC
          </button>
        )}
      </div>

      <div
        className="grid grid-cols-3 gap-1"
        title="Spread ±1 peso. Aplica solo cuando una línea está en divisa distinta a la cotización. Protege a Dasic de variación cambiaria. La OC al proveedor usa el DOF puro (sin spread)."
      >
        {/* DOF */}
        <div className={`rounded border px-1.5 py-1 ${idleColClass}`}>
          <div className="text-[9px] uppercase tracking-wider text-slate-500">DOF · Banxico</div>
          <div className="font-mono text-[11px] tabular-nums">
            {tcInvalido ? '—' : `$${fmt4(tc)}`}
          </div>
        </div>
        {/* MN → USD */}
        <div
          className={`rounded border px-1.5 py-1 ${aplicaMnAUsd ? activeColClass : idleColClass}`}
        >
          <div className="text-[9px] uppercase tracking-wider text-slate-500">MN → USD</div>
          <div className="flex items-center gap-1">
            <span className="font-mono text-[11px] tabular-nums">
              {tcInvalido ? '—' : `$${fmt4(tcs.tc_mn_a_usd)}`}
            </span>
            {!tcInvalido && (
              <span className={deltaBadge}>
                <ArrowDown className="h-2 w-2" />
                {fmtDelta(deltaMnAUsd)}
              </span>
            )}
          </div>
        </div>
        {/* USD → MN */}
        <div
          className={`rounded border px-1.5 py-1 ${aplicaUsdAMn ? activeColClass : idleColClass}`}
        >
          <div className="text-[9px] uppercase tracking-wider text-slate-500">USD → MN</div>
          <div className="flex items-center gap-1">
            <span className="font-mono text-[11px] tabular-nums">
              {tcInvalido ? '—' : `$${fmt4(tcs.tc_usd_a_mn)}`}
            </span>
            {!tcInvalido && (
              <span className={deltaBadge}>
                <ArrowUp className="h-2 w-2" />
                {fmtDelta(deltaUsdAMn)}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verificar que TypeScript compila el archivo aislado**

Run: `cd web && npx tsc --noEmit 2>&1 | grep -E "TCMiniTable|error TS" | head -20`

Expected: sin errores en `TCMiniTable.tsx`. Si aparecen errores en otros archivos (relacionados a `HeaderCotizacion.tsx` o `FXBadge.tsx` aún sin tocar), ignorar — se resuelven en las tareas siguientes.

- [ ] **Step 3: Commit**

```bash
git add web/src/features/cotizador/components/TCMiniTable.tsx
git commit -m "feat(cotizador): TCMiniTable component (DOF + direccionales)"
```

---

### Task 2: Adelgazar `FXBadge.tsx`

Hoy `FXBadge` muestra: `↻ TC oficial: $X.XXXX (fecha · fuente)`. La mini-tabla ya muestra el valor del DOF y la fecha/fuente en su header, así que el `FXBadge` queda obsoleto.

Opción: **eliminar el archivo**. La funcionalidad de refresh ya está embebida en `TCMiniTable.tsx`.

**Files:**
- Delete: `web/src/features/cotizador/components/FXBadge.tsx`

- [ ] **Step 1: Confirmar que `FXBadge` solo se usa en `HeaderCotizacion.tsx`**

Run: `grep -rn "FXBadge\|FXBadge" web/src/ --include="*.tsx" --include="*.ts"`

Expected: solo 2 referencias — el `export function FXBadge` en `FXBadge.tsx` y el `import { FXBadge }` en `HeaderCotizacion.tsx`. Si hay más usos, NO eliminar el archivo y abrir un sub-task de extracción.

- [ ] **Step 2: Eliminar el archivo**

```bash
rm web/src/features/cotizador/components/FXBadge.tsx
```

- [ ] **Step 3: Verificar que el build aún no rompe (porque `HeaderCotizacion` aún lo importa — esperado)**

Run: `cd web && npx tsc --noEmit 2>&1 | grep -E "FXBadge|error TS" | head -5`

Expected: error "Cannot find module './FXBadge'" en `HeaderCotizacion.tsx`. Ese error se arregla en Task 3.

- [ ] **Step 4: No commitear todavía** — el build está roto. El commit ocurre al final de Task 3 junto con la integración.

---

### Task 3: Integrar `TCMiniTable` en `HeaderCotizacion.tsx`

Sustituir el `<FXBadge />` + el botón "Pisar TC manualmente" por `<TCMiniTable />`. El bloque "Pisar TC" ya queda dentro de la mini-tabla (en `TCMiniTable.tsx` Step 1, sección admin del header).

**Files:**
- Modify: `web/src/features/cotizador/components/HeaderCotizacion.tsx`

- [ ] **Step 1: Cambiar el import de `FXBadge` por `TCMiniTable`**

En `HeaderCotizacion.tsx` cambiar la línea 8:

```tsx
// ANTES
import { FXBadge } from './FXBadge';

// DESPUÉS
import { TCMiniTable } from './TCMiniTable';
```

- [ ] **Step 2: Eliminar el import de `ShieldAlert` del header (ya no se usa)**

En la línea 2:

```tsx
// ANTES
import { User, Coins, ArrowRightLeft, CalendarPlus, CalendarClock, ShieldAlert } from 'lucide-react';

// DESPUÉS
import { User, Coins, ArrowRightLeft, CalendarPlus, CalendarClock } from 'lucide-react';
```

- [ ] **Step 3: Eliminar el `useIsAdmin` del header (ya está dentro de `TCMiniTable`)**

En la línea 7:

```tsx
// ANTES
import { useIsAdmin } from '@/lib/permissions';

// DESPUÉS — borrar la línea completa
```

Y eliminar dentro del componente (línea 24):

```tsx
// ANTES
const { config } = useConfig();
const esAdmin = useIsAdmin();

// DESPUÉS
const { config } = useConfig();
```

- [ ] **Step 4: Reemplazar el bloque `mt-1 space-y-0.5` que contiene `<FXBadge />` y el botón "Pisar TC"**

En `HeaderCotizacion.tsx` líneas 93-104, reemplazar:

```tsx
          <div className="mt-1 space-y-0.5">
            <FXBadge />
            {esAdmin && (
              <button
                type="button"
                onClick={() => window.dispatchEvent(new CustomEvent('cot:open-pisartc'))}
                className="text-[10px] text-amber-400 hover:underline flex items-center gap-1"
              >
                <ShieldAlert className="h-2.5 w-2.5" /> Pisar TC manualmente
              </button>
            )}
          </div>
```

Por:

```tsx
          <TCMiniTable />
```

Importante: la mini-tabla ya maneja su propio `opacity-60` cuando `tcNecesario === false` (computado dentro del componente, mismo criterio que el wrapper externo). Para evitar duplicar la atenuación, mantener el `tcNecesario ? '' : 'opacity-60'` en el `div` padre (línea 74) **es redundante pero no rompe nada** — el `opacity-60` es idempotente. Lo dejamos como está para no tocar más lógica.

- [ ] **Step 5: Verificar que TypeScript compila todo el frontend**

Run: `cd web && npx tsc --noEmit 2>&1 | tail -20`

Expected: cero errores. Si hay error en `HeaderCotizacion.tsx` revisar imports; si hay error en otro archivo (no tocado por este plan) reportar pero no bloquear.

- [ ] **Step 6: Build de producción para validar Vite también**

Run: `cd web && npm run build 2>&1 | tail -10`

Expected: `✓ built in <N>s` con el bundle generado en `app/static/dist/`.

- [ ] **Step 7: Commit (incluye Task 2 y Task 3 juntas porque entre ambas dejan el build válido)**

```bash
git add web/src/features/cotizador/components/HeaderCotizacion.tsx \
        web/src/features/cotizador/components/FXBadge.tsx \
        app/static/dist
git commit -m "feat(cotizador): TC explícito en header (mini-tabla 3 cols)

Reemplaza FXBadge con TCMiniTable: muestra DOF + MN→USD + USD→MN
con badges verdes (±1.00) y resalta la columna activa según moneda
de la cot y composición del cart. Spread ya se aplicaba — esto solo
expone la transparencia que pedía Dasic.

- Crea TCMiniTable.tsx (read-only, single source via resolveDirectionalTcs)
- Elimina FXBadge.tsx (su refresh+fuente queda embebido en TCMiniTable)
- HeaderCotizacion: imports limpios, sin ShieldAlert/useIsAdmin"
```

Nota: el `app/static/dist` se incluye en el commit porque el Procfile no corre `npm run build` y Railway necesita el bundle ya generado (ver memoria `feedback-backfill-ddl-railway.md`).

---

### Task 4: Verificación manual en el browser

No hay tests automatizados (no hay harness en el repo); la verificación es visual. Esta tarea es **requisito** antes de declarar el plan completo — según la guía de Claude en este repo: "type checking and test suites verify code correctness, not feature correctness".

**Files:** ninguno. Solo run + observación.

- [ ] **Step 1: Levantar el backend**

```bash
uvicorn app.main:app --reload
```

Expected: Uvicorn corriendo en `http://127.0.0.1:8000`. Login con `admin@dasic.mx / 784512` debería funcionar.

- [ ] **Step 2: Levantar el SPA dev server en otra terminal**

```bash
cd web && npm run dev
```

Expected: Vite corriendo en `http://127.0.0.1:5173` con proxy a 8000.

- [ ] **Step 3: Abrir `/cotizador/nueva` y verificar render base**

Navegar a `http://127.0.0.1:5173/cotizador/nueva` (login si hace falta).

Expected:
- Bajo el input "TC" aparece una mini-tabla de 3 columnas.
- Encima de la tabla: una línea pequeña `↻ BANXICO · 2026-MM-DD` (o `EXCHANGERATE · …` si no hay token de Banxico).
- A la derecha de esa línea (si tu usuario es admin): un link ámbar "Pisar TC".
- DOF muestra el valor actual con 4 decimales.
- MN → USD muestra DOF − 1 con badge verde "▼ 1.00".
- USD → MN muestra DOF + 1 con badge verde "▲ 1.00".
- Sin cart, la mini-tabla está atenuada (`opacity-60`).

- [ ] **Step 4: Agregar un producto USD del catálogo, cot en MXN (default)**

Buscar un producto cuyo `moneda_compra === 'USD'` y agregarlo al cart.

Expected:
- La columna **USD → MN** se resalta (borde glow, fondo más oscuro).
- DOF y MN → USD quedan atenuadas.
- El `CartRow` muestra el badge "USD → MXN" en la línea.
- El total que ves en `TotalsBar` cuadra con `costo_usd × (DOF + 1) × qty × (1 + utilidad/100)`. Validar mentalmente con una línea (ej. cost $100 USD, qty 1, util 30%, TC=18.0 → 100 × 19 × 1.3 = 2,470 MXN).

- [ ] **Step 5: Cambiar la moneda de la cot a USD**

En el select "Moneda" del header, escoger `USD`.

Expected:
- La columna **MN → USD** se resalta solo si hay líneas MXN en el cart (no las hay si solo agregaste USD en Step 4).
- USD → MN queda atenuada porque ya no hay líneas MXN cruzando a MXN.
- Si agregas además un producto MXN, MN → USD se resalta.

- [ ] **Step 6: Editar el input TC del header**

Cambiar el TC de 18 a 25.

Expected:
- DOF muestra $25.0000.
- MN → USD muestra $24.0000 (badge "▼ 1.00").
- USD → MN muestra $26.0000 (badge "▲ 1.00").
- Totales del cart recalculan en vivo (el subtotal MXN sube si tienes líneas USD).

- [ ] **Step 7: Click en el refresh (↻ Banxico)**

Expected:
- El icono gira 1-2 segundos.
- Toast verde "TC actualizado" con el valor del día.
- DOF y badges se actualizan al valor de Banxico.

- [ ] **Step 8: Pisar TC manualmente (solo admin)**

Click en "Pisar TC" → modal `ModalPisarTC` se abre → escribir 20 → Aplicar.

Expected:
- DOF muestra $20.0000.
- Direccionales: $19.0000 / $21.0000.
- Toast no es necesario (el modal solo cierra al aplicar).

- [ ] **Step 9: Cargar una cotización legacy con `tc_mn_a_usd = null`**

Navegar a `/cotizador/historial`, abrir una cotización creada antes de hoy (cuando los direccionales no se persistían explícitamente).

Expected:
- Mini-tabla muestra DOF (lo que vino guardado) y los direccionales derivados (DOF ± 1).
- Badge "▼ 1.00" / "▲ 1.00" porque el delta es exactamente ±1.

- [ ] **Step 10: (Opcional) Cargar una cot con direccional overrideado**

Si tienes una cotización donde `tc_mn_a_usd` se guardó != DOF − 1 (poco común; chequear con `psql` o `/api/ventas/{id}/detalle-json`). Si no la tienes, saltar este step.

Expected: el badge muestra el delta real (ej. `▼ 0.85` si el override era DOF − 0.85).

- [ ] **Step 11: Marcar la verificación como completa**

Después de pasar Steps 1-10 (Step 10 es opcional), el plan está listo para merge a producción. El push a `origin/main` lo dispara Railway autodeploy.

```bash
git push origin main
```

Expected: `1 commit pushed`. Railway autodeploy en marcha (ver Dashboard).

---

## Notas de implementación

- **No reescribir `FXBadge` como wrapper** — eliminarlo limpio. Mantener "wrappers vacíos" es deuda técnica.
- **No agregar tests** — el repo no tiene harness configurado (ver CLAUDE.md). La verificación es manual + `tsc --noEmit` + `npm run build`.
- **No tocar el modal `ModalPisarTC`** — ya funciona con el event `cot:open-pisartc` que `TCMiniTable` dispara.
- **No tocar `CartRow`** — el badge "USD → MXN" que muestra hoy en cada línea cruz-divisa sigue siendo correcto y complementa la mini-tabla del header.
- **Single source of truth:** la mini-tabla deriva los direccionales con `resolveDirectionalTcs(tc, tcMnAUsd, tcUsdAMn)` — exactamente la misma llamada que `CartRow.tsx:27` hace para calcular el precio de cada línea. Si los valores que ve el usuario en la mini-tabla y los que producen los importes alguna vez difieren, hay un bug en `resolveDirectionalTcs` (común a ambos).
- **Persistencia:** ya viaja en `OrdenVentaCreate` (`types.ts:220-222`). Al guardar, `tc_mn_a_usd` y `tc_usd_a_mn` se mandan como `null` cuando son DOF±1 exactos (default), y como número cuando se override-aron. Eso ya está implementado en `serialize.ts:40`.

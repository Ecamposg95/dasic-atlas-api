# Cotizador UX Wave — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cerrar 5 gaps de UX del cotizador en una wave: banner cliente, tab Fantasmas en buscador, subtotal/total grandes, quitar modal Pisar TC, fix jerarquía visual de tabs.

**Architecture:** Cambios puramente SPA. Backend ya tiene `/api/fantasmas/?q=` listo. Cada sub-feature es independiente y commitea por separado para revertir fácil si algo falla. Sin migraciones, sin cambios en store/calc/persistencia.

**Tech Stack:** React 18 + TypeScript, Zustand, TanStack Query v5, Tailwind, shadcn/ui, Lucide icons.

**Spec:** `docs/superpowers/specs/2026-05-25-cotizador-ux-wave-design.md`

---

## File Structure

**Crear:**
- `web/src/features/cotizador/hooks/useFantasmasSearch.ts` — hook TanStack Query que envuelve `GET /api/fantasmas/?q=&estado=PENDIENTE`

**Modificar:**
- `web/src/features/cotizador/components/HeaderCotizacion.tsx` — banner ámbar de "elige cliente"
- `web/src/features/cotizador/components/CatalogoFiltros.tsx` — agregar tab "Fantasmas", restilizar tabs como chips
- `web/src/features/cotizador/components/ProductSearch.tsx` — branch nuevo para `tipo === 'fantasma'`
- `web/src/features/cotizador/components/TotalsBar.tsx` — tipografía
- `web/src/features/cotizador/components/TCMiniTable.tsx` — quitar link "Pisar TC"
- `web/src/features/cotizador/components/TabsCotizador.tsx` — subir contraste/peso
- `web/src/features/cotizador/pages/CotizadorPage.tsx` — quitar `<ModalPisarTC />`

**Eliminar:**
- `web/src/features/cotizador/components/ModalPisarTC.tsx`

**Sin cambios:** backend, `store.ts`, `lib/calc.ts`, `lib/serialize.ts`, `CartRow.tsx`, `RowExpanded.tsx`, `Cart.tsx`.

---

### Task 1: F4 — Quitar el modal "Pisar TC manualmente"

Empezamos por la más simple — pura deuda muerta. Limpia y commit. No cambia comportamiento; solo elimina UI redundante.

**Files:**
- Delete: `web/src/features/cotizador/components/ModalPisarTC.tsx`
- Modify: `web/src/features/cotizador/components/TCMiniTable.tsx`
- Modify: `web/src/features/cotizador/pages/CotizadorPage.tsx`

- [ ] **Step 1: Confirmar que `ModalPisarTC` no se usa más allá de Cotizador**

```bash
grep -rn "ModalPisarTC\|cot:open-pisartc" web/src/ --include="*.tsx" --include="*.ts"
```

Expected: 3 referencias en total — el `export function ModalPisarTC` (ModalPisarTC.tsx), su listener `cot:open-pisartc` (ModalPisarTC.tsx:19), el dispatch (TCMiniTable.tsx:91) y el render (CotizadorPage.tsx:392). Si aparece referencia en algún archivo fuera de cotizador, STOP y reporta.

- [ ] **Step 2: Eliminar el archivo del modal**

```bash
rm web/src/features/cotizador/components/ModalPisarTC.tsx
```

- [ ] **Step 3: Quitar imports y referencias del modal en `CotizadorPage.tsx`**

En `web/src/features/cotizador/pages/CotizadorPage.tsx`:

Borrar la línea de import:
```tsx
import { ModalPisarTC } from '../components/ModalPisarTC';
```

Borrar la línea del render (alrededor de la línea 392):
```tsx
<ModalPisarTC />
```

- [ ] **Step 4: Quitar el link "Pisar TC" y los imports muertos en `TCMiniTable.tsx`**

En `web/src/features/cotizador/components/TCMiniTable.tsx`:

a) Borrar imports muertos del header del archivo:

```tsx
// ANTES
import { RefreshCw, ArrowDown, ArrowUp, ShieldAlert } from 'lucide-react';
import { useCotizador } from '../store';
import { resolveDirectionalTcs } from '../lib/calc';
import { useFX, useFXRefresh } from '../hooks/useFX';
import { useIsAdmin } from '@/lib/permissions';
import { toast } from '@/lib/toast';
import type { ApiError } from '@/lib/api';

// DESPUÉS
import { RefreshCw, ArrowDown, ArrowUp } from 'lucide-react';
import { useCotizador } from '../store';
import { resolveDirectionalTcs } from '../lib/calc';
import { useFX, useFXRefresh } from '../hooks/useFX';
import { toast } from '@/lib/toast';
import type { ApiError } from '@/lib/api';
```

b) Borrar `const esAdmin = useIsAdmin();` dentro del componente.

c) Borrar el bloque del botón admin completo. En el JSX, dentro del primer `<div className="flex items-center justify-between gap-2">`, borrar:

```tsx
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
```

Con eso, el container de la fila superior queda con solo el botón de refresh a la izquierda. Cambiar `justify-between` por `justify-start` para que no haya un espacio raro a la derecha:

```tsx
// ANTES
<div className="flex items-center justify-between gap-2">

// DESPUÉS
<div className="flex items-center justify-start gap-2">
```

- [ ] **Step 5: Verificar que TypeScript compila**

```bash
cd web && npx tsc --noEmit 2>&1 | tail -10
```

Expected: sin errores. Si aparece "Cannot find name 'esAdmin'" o "ShieldAlert" o similar, revisa que borraste todas las referencias.

- [ ] **Step 6: Confirmar que no quedan referencias a `cot:open-pisartc` ni a `ModalPisarTC`**

```bash
grep -rn "ModalPisarTC\|cot:open-pisartc\|ShieldAlert" web/src/features/cotizador/
```

Expected: cero matches. (`ShieldAlert` debería haberse eliminado de `TCMiniTable.tsx` y no aparece en ningún otro lugar de cotizador.)

- [ ] **Step 7: Commit**

```bash
git add web/src/features/cotizador/components/TCMiniTable.tsx \
        web/src/features/cotizador/pages/CotizadorPage.tsx \
        web/src/features/cotizador/components/ModalPisarTC.tsx
git commit -m "refactor(cotizador): elimina modal Pisar TC (deuda muerta)

El input TC del header ya es directamente editable. El modal duplicaba esa
edición con un overlay innecesario. Limpia:
- ModalPisarTC.tsx eliminado
- Botón admin Pisar TC y dispatch cot:open-pisartc removidos de TCMiniTable
- Render del modal removido de CotizadorPage

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: F5 — Arreglar jerarquía visual de tabs

Sub-control style para los tabs de filtro de búsqueda (Productos/Servicios/Fantasmas), tabs primarios (Cotizador/Historial) más prominentes. Importante: la pestaña "Fantasmas" se agrega en la Task 3, así que aquí solo cambiamos visual + estructura para Productos/Servicios.

**Files:**
- Modify: `web/src/features/cotizador/components/TabsCotizador.tsx`
- Modify: `web/src/features/cotizador/components/CatalogoFiltros.tsx`

- [ ] **Step 1: Verificar que `TabsCotizador` solo se usa en cotizador**

```bash
grep -rn "TabsCotizador" web/src/ --include="*.tsx" --include="*.ts"
```

Expected: 2 referencias — export en `TabsCotizador.tsx`, import en `CotizadorPage.tsx`. Si hay más usos, STOP.

- [ ] **Step 2: Subir contraste en `TabsCotizador.tsx`**

Reemplazar el `<div>` raíz y los botones:

```tsx
// ANTES (línea 14-43 aprox)
<div className="flex items-center gap-1 border-b border-slate-800 -mt-2 mb-4">
  <button
    type="button"
    onClick={() => onChange('editor')}
    className={`flex items-center gap-2 px-4 py-2 text-sm font-medium transition border-b-2 ${
      active === 'editor'
        ? 'text-accent-glow border-accent-glow'
        : 'text-slate-400 border-transparent hover:text-slate-200'
    }`}
  >
    <Edit3 className="h-4 w-4" /> Cotizador
  </button>
  <button
    type="button"
    onClick={() => onChange('historial')}
    className={`flex items-center gap-2 px-4 py-2 text-sm font-medium transition border-b-2 ${
      active === 'historial'
        ? 'text-accent-glow border-accent-glow'
        : 'text-slate-400 border-transparent hover:text-slate-200'
    }`}
  >
    <History className="h-4 w-4" /> Historial
    {countHistorial != null && countHistorial > 0 && (
      <span className="text-[10px] bg-slate-700 text-slate-200 rounded-full px-2 py-0.5">
        {countHistorial}
      </span>
    )}
  </button>
</div>
```

```tsx
// DESPUÉS
<div className="flex items-center gap-1 border-b-2 border-slate-800 bg-slate-900/40 rounded-t-md px-1 -mt-2 mb-4">
  <button
    type="button"
    onClick={() => onChange('editor')}
    className={`flex items-center gap-2 px-4 py-2.5 text-sm font-semibold transition border-b-2 -mb-[2px] ${
      active === 'editor'
        ? 'text-accent-glow border-accent-glow'
        : 'text-slate-400 border-transparent hover:text-slate-200'
    }`}
  >
    <Edit3 className="h-4 w-4" /> Cotizador
  </button>
  <button
    type="button"
    onClick={() => onChange('historial')}
    className={`flex items-center gap-2 px-4 py-2.5 text-sm font-semibold transition border-b-2 -mb-[2px] ${
      active === 'historial'
        ? 'text-accent-glow border-accent-glow'
        : 'text-slate-400 border-transparent hover:text-slate-200'
    }`}
  >
    <History className="h-4 w-4" /> Historial
    {countHistorial != null && countHistorial > 0 && (
      <span className="text-[10px] bg-slate-700 text-slate-200 rounded-full px-2 py-0.5">
        {countHistorial}
      </span>
    )}
  </button>
</div>
```

Cambios: `border-b` → `border-b-2`, `bg-slate-900/40 rounded-t-md px-1` agregados al container, `py-2` → `py-2.5`, `font-medium` → `font-semibold`, `-mb-[2px]` agregado a los buttons para que su borde se superponga limpiamente con el del container.

- [ ] **Step 3: Convertir tabs internos de `CatalogoFiltros.tsx` en chips**

Reemplazar el container `<div className="flex gap-1 border-b border-slate-800">` y sus dos botones:

```tsx
// ANTES (línea 49-72 aprox)
<div className="flex gap-1 border-b border-slate-800">
  <button
    type="button"
    onClick={() => props.onTipoChange('producto')}
    className={`px-3 py-1 text-xs border-b-2 transition ${
      props.tipo === 'producto'
        ? 'text-accent-glow border-accent-glow'
        : 'text-slate-400 border-transparent hover:text-slate-200'
    }`}
  >
    Productos
  </button>
  <button
    type="button"
    onClick={() => props.onTipoChange('servicio')}
    className={`px-3 py-1 text-xs border-b-2 transition ${
      props.tipo === 'servicio'
        ? 'text-emerald-300 border-emerald-400'
        : 'text-slate-400 border-transparent hover:text-slate-200'
    }`}
  >
    Servicios
  </button>
</div>
```

```tsx
// DESPUÉS
<div className="inline-flex gap-1 p-1 rounded-md bg-slate-950/40 border border-slate-800/60 w-fit">
  <button
    type="button"
    onClick={() => props.onTipoChange('producto')}
    className={`px-2.5 py-1 text-[11px] rounded transition ${
      props.tipo === 'producto'
        ? 'bg-slate-800 text-accent-glow'
        : 'text-slate-400 hover:text-slate-200'
    }`}
  >
    Productos
  </button>
  <button
    type="button"
    onClick={() => props.onTipoChange('servicio')}
    className={`px-2.5 py-1 text-[11px] rounded transition ${
      props.tipo === 'servicio'
        ? 'bg-slate-800 text-emerald-300'
        : 'text-slate-400 hover:text-slate-200'
    }`}
  >
    Servicios
  </button>
</div>
```

(El 3er botón "Fantasmas" se agrega en Task 3 Step 4.)

- [ ] **Step 4: Verificar tsc**

```bash
cd web && npx tsc --noEmit 2>&1 | tail -10
```

Expected: sin errores.

- [ ] **Step 5: Commit**

```bash
git add web/src/features/cotizador/components/TabsCotizador.tsx \
        web/src/features/cotizador/components/CatalogoFiltros.tsx
git commit -m "style(cotizador): jerarquía visual de tabs

Tabs primarios (Cotizador/Historial) más prominentes con border-b-2 y
bg-slate-900/40. Tabs secundarios (Productos/Servicios) restilizados
como chips compactos dentro del buscador para clarificar que son
sub-control del filtro, no navegación de página.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: F2 — Tab "Fantasmas" en el buscador

La feature más grande. Crea un hook nuevo, agrega un 3er filtro al `CatalogoFiltros`, y agrega un branch nuevo en `ProductSearch` para renderizar fantasmas y poder agregarlos al cart.

**Files:**
- Create: `web/src/features/cotizador/hooks/useFantasmasSearch.ts`
- Modify: `web/src/features/cotizador/components/CatalogoFiltros.tsx`
- Modify: `web/src/features/cotizador/components/ProductSearch.tsx`
- Modify: `web/src/features/cotizador/hooks/useProductosSearch.ts` (extender el tipo `SearchScope` para que acepte `tipo: 'producto' | 'servicio' | 'fantasma'`)

- [ ] **Step 1: Crear `useFantasmasSearch.ts`**

Crear archivo `web/src/features/cotizador/hooks/useFantasmasSearch.ts`:

```ts
import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

// Shape devuelto por GET /api/fantasmas/ (`app/routers/fantasmas.py::_serialize_fantasma_row`).
// Listamos solo los campos que el cotizador consume al agregar al cart.
export type FantasmaPrevio = {
  id: number;
  descripcion: string;
  sku_libre: string | null;
  costo_referencia: number;
  moneda: string;             // 'MXN' | 'USD' (puede venir otro pero es raro)
  proveedor_sugerido_id: number | null;
  proveedor_sugerido_nombre: string | null;
  estado: string;             // 'PENDIENTE' | 'PROMOVIDO' | ...
  veces_solicitado: number;
  ultimo_visto_en: string | null;
};

// El endpoint devuelve un objeto con `items: [...]` cuando el query tiene
// resultados, o un array suelto en algunas versiones; nos defendemos.
type FantasmasResponse = { items: FantasmaPrevio[] } | FantasmaPrevio[];

function normalize(data: FantasmasResponse | undefined): FantasmaPrevio[] {
  if (!data) return [];
  if (Array.isArray(data)) return data;
  return data.items ?? [];
}

export function useFantasmasSearch(q: string) {
  const [debouncedQ, setDebouncedQ] = useState(q);
  useEffect(() => {
    const t = setTimeout(() => setDebouncedQ(q), 300);
    return () => clearTimeout(t);
  }, [q]);

  const trimmed = debouncedQ.trim();
  const enabled = trimmed.length === 0 || trimmed.length >= 2;

  const query = useQuery<FantasmasResponse>({
    queryKey: ['cotizador', 'fantasmas', 'search', trimmed],
    queryFn: () =>
      api.get<FantasmasResponse>(
        `/api/fantasmas/?estado=PENDIENTE&page_size=50${trimmed ? `&q=${encodeURIComponent(trimmed)}` : ''}`,
      ),
    staleTime: 30_000,
    enabled,
  });

  return {
    ...query,
    items: normalize(query.data),
  };
}
```

- [ ] **Step 2: Extender el tipo en `useProductosSearch.ts`**

En `web/src/features/cotizador/hooks/useProductosSearch.ts`, ampliar el tipo `SearchScope.tipo`:

```ts
// ANTES
export type SearchScope = {
  q: string;
  tipo: 'producto' | 'servicio';
  marca_id?: number | null;
  marca_nombre?: string | null;
  categoria_id?: number | null;
  categoria_nombre?: string | null;
};

// DESPUÉS
export type SearchScope = {
  q: string;
  tipo: 'producto' | 'servicio' | 'fantasma';
  marca_id?: number | null;
  marca_nombre?: string | null;
  categoria_id?: number | null;
  categoria_nombre?: string | null;
};
```

Luego, dentro del hook `useProductosSearch`, asegurar que cuando `tipo === 'fantasma'` el query no se ejecuta (devolver `items: []`, `servicios: []`, `cantidad: null`):

Localiza la parte donde se hace el `useQuery` principal en el archivo y guarda la consulta detrás del check de tipo. Si el archivo tiene varias ramas (producto vs servicio), añade una rama `if (scope.tipo === 'fantasma')` que devuelva resultado vacío. La búsqueda real de fantasmas la hace el hook nuevo `useFantasmasSearch`, no este.

Si tienes dudas sobre cómo hacer el branching exacto, lee el archivo entero (líneas 1-200) antes de tocarlo y replica el patrón existente.

- [ ] **Step 3: Tipo `tipo` en `CatalogoFiltros.tsx`**

Cambiar la prop:

```tsx
// ANTES (línea 24-25 aprox)
type Props = {
  tipo: 'producto' | 'servicio';
  onTipoChange: (t: 'producto' | 'servicio') => void;

// DESPUÉS
type Props = {
  tipo: 'producto' | 'servicio' | 'fantasma';
  onTipoChange: (t: 'producto' | 'servicio' | 'fantasma') => void;
```

- [ ] **Step 4: Agregar el 3er botón "Fantasmas" en `CatalogoFiltros.tsx`**

Después del botón "Servicios" (ya restilizado como chip en Task 2 Step 3), agregar un 3er botón "Fantasmas":

```tsx
<button
  type="button"
  onClick={() => props.onTipoChange('fantasma')}
  className={`px-2.5 py-1 text-[11px] rounded transition flex items-center gap-1 ${
    props.tipo === 'fantasma'
      ? 'bg-slate-800 text-amber-300'
      : 'text-slate-400 hover:text-slate-200'
  }`}
>
  <Ghost className="h-2.5 w-2.5" /> Fantasmas
</button>
```

Y agregar el import del icono al inicio del archivo:

```tsx
import { Ghost } from 'lucide-react';
```

(O si ya hay imports de lucide-react en el archivo, agregar `Ghost` a la lista.)

Tras este step, el bloque de chips tiene 3 botones: Productos, Servicios, Fantasmas. La condición `props.tipo === 'producto' && (<div>marca/categoría selects</div>)` se queda igual — los selects de marca/categoría solo se muestran en Productos.

- [ ] **Step 5: Agregar tipo `'fantasma'` en `ProductSearch.tsx`**

Cambiar el `useState` del tipo:

```tsx
// ANTES
const [tipo, setTipo] = useState<'producto' | 'servicio'>('producto');

// DESPUÉS
const [tipo, setTipo] = useState<'producto' | 'servicio' | 'fantasma'>('producto');
```

- [ ] **Step 6: Importar y usar `useFantasmasSearch` en `ProductSearch.tsx`**

Agregar el import al inicio:

```tsx
import { useFantasmasSearch, type FantasmaPrevio } from '../hooks/useFantasmasSearch';
```

Adentro del componente, después del bloque del `useProductosSearch`:

```tsx
const fantasmasQuery = useFantasmasSearch(tipo === 'fantasma' ? q : '');
const fantasmas: FantasmaPrevio[] = tipo === 'fantasma' ? fantasmasQuery.items : [];
const fantasmasLoading = tipo === 'fantasma' && fantasmasQuery.isLoading;
```

- [ ] **Step 7: Handler para click en fantasma existente**

Agregar la función helper dentro del componente, junto a `onSelect` y `onSelectServicio`:

```tsx
function onSelectFantasma(f: FantasmaPrevio) {
  const addLineaAdhoc = useCotizador.getState().addLineaAdhoc;
  addLineaAdhoc({
    descripcion: f.descripcion,
    sku_libre: f.sku_libre || undefined,
    costo: Number(f.costo_referencia) || 0,
    moneda: (f.moneda || 'MXN').toUpperCase() === 'USD' ? 'USD' : 'MXN',
    proveedor_sugerido_id: f.proveedor_sugerido_id,
    utilidad: 30,
    qty: cantidadParseada ?? 1,
  });
  setQ('');
  setOpen(false);
  setTimeout(() => inputRef.current?.focus(), 0);
}
```

- [ ] **Step 8: Render del branch `tipo === 'fantasma'` en `ProductSearch.tsx`**

El dropdown actual tiene una rama `tipo === 'servicio' ? (...) : (...)`. Convertirla en tres-vías. Localiza el JSX donde está:

```tsx
{tipo === 'servicio' ? (
  // ... servicios
) : (
  // ... productos
)}
```

Cambiarla a:

```tsx
{tipo === 'servicio' ? (
  // ... servicios (sin cambios)
) : tipo === 'fantasma' ? (
  <>
    {(fantasmas.length > 0 || fantasmasLoading) && (
      <div className="sticky top-0 z-10 bg-slate-900/95 backdrop-blur border-b border-slate-800 px-2 py-1 text-[10px] uppercase tracking-[0.15em] text-slate-500 flex items-center justify-between">
        <span>{fantasmasLoading ? 'Buscando…' : `${fantasmas.length} fantasma(s) previo(s)`}</span>
        {cantidadParseada != null && <span className="text-violet-400">Cantidad detectada: {cantidadParseada}</span>}
      </div>
    )}
    {!fantasmasLoading && fantasmas.length === 0 && (
      <div className="p-3 text-center space-y-2">
        <div className="text-[11px] text-slate-500">Sin fantasmas previos para "{q.trim() || 'tu búsqueda'}"</div>
        <button
          type="button"
          onClick={() => {
            window.dispatchEvent(
              new CustomEvent('cot:open-add-fantasma', {
                detail: { initialDescripcion: q.trim() },
              }),
            );
            setOpen(false);
            setQ('');
          }}
          className="inline-flex items-center gap-1.5 text-[11px] font-medium px-2.5 py-1.5 rounded border border-amber-700/50 bg-amber-900/20 text-amber-300 hover:bg-amber-900/40 hover:border-amber-500 transition"
        >
          <Ghost className="h-3 w-3" />
          Capturar nuevo fantasma
        </button>
      </div>
    )}
    {fantasmas.map((f) => (
      <button
        key={f.id}
        type="button"
        onClick={() => onSelectFantasma(f)}
        className="w-full text-left px-2 py-1.5 hover:bg-amber-950/30 transition border-b border-slate-800 last:border-b-0 flex items-center gap-2"
      >
        <Ghost className="h-3.5 w-3.5 text-amber-400 shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 flex-wrap">
            {f.sku_libre && (
              <span className="font-mono text-[11px] font-bold text-amber-300">{f.sku_libre}</span>
            )}
            {f.proveedor_sugerido_nombre && (
              <span className="text-[10px] text-slate-500">· {f.proveedor_sugerido_nombre}</span>
            )}
            {f.veces_solicitado > 1 && (
              <span className="text-[10px] bg-amber-900/30 text-amber-300 px-1.5 py-0.5 rounded">
                ×{f.veces_solicitado}
              </span>
            )}
          </div>
          <div className="text-[11px] text-slate-200 truncate">{f.descripcion}</div>
        </div>
        <div className="text-[11px] text-slate-400 font-mono whitespace-nowrap">
          {(f.moneda || 'MXN').toUpperCase()} ${Number(f.costo_referencia).toLocaleString('es-MX', { minimumFractionDigits: 2 })}
        </div>
      </button>
    ))}
  </>
) : (
  // ... productos (sin cambios)
)}
```

Esto reemplaza la estructura ternaria. Verifica que el cierre del bloque `tipo === 'servicio'` y la apertura de `tipo === 'fantasma'` quedan bien anidados.

- [ ] **Step 9: Cambiar el placeholder del input cuando `tipo === 'fantasma'`**

En el `<Input>` del buscador:

```tsx
// ANTES
placeholder={
  tipo === 'servicio'
    ? 'Buscar servicio (ej. "instalación" o "SRV-0001")…'
    : 'Buscar producto (ej. "5 GV2ME14" o "rodamiento")…'
}

// DESPUÉS
placeholder={
  tipo === 'servicio'
    ? 'Buscar servicio (ej. "instalación" o "SRV-0001")…'
    : tipo === 'fantasma'
      ? 'Buscar fantasma previo (descripción o SKU libre)…'
      : 'Buscar producto (ej. "5 GV2ME14" o "rodamiento")…'
}
```

- [ ] **Step 10: tsc + build**

```bash
cd web && npx tsc --noEmit 2>&1 | tail -10
cd web && npm run build 2>&1 | tail -8
```

Expected: tsc clean. Build success `✓ built in <N>s`.

- [ ] **Step 11: Commit**

```bash
git add web/src/features/cotizador/hooks/useFantasmasSearch.ts \
        web/src/features/cotizador/hooks/useProductosSearch.ts \
        web/src/features/cotizador/components/CatalogoFiltros.tsx \
        web/src/features/cotizador/components/ProductSearch.tsx
git commit -m "feat(cotizador): tab Fantasmas en buscador

3er tab junto a Productos/Servicios. Consulta /api/fantasmas/?q= y
permite seleccionar un fantasma previo para evitar capturar duplicados.
Click → addLineaAdhoc con los datos del fantasma persistido.
Estado vacío → CTA \"Capturar nuevo fantasma\" abre el modal existente.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: F3 — Subtotal y Total grandes en `TotalsBar`

**Files:**
- Modify: `web/src/features/cotizador/components/TotalsBar.tsx`

- [ ] **Step 1: Rework tipográfico**

Localizar el bloque del JSX en `TotalsBar.tsx` (alrededor de la línea 177-203, la `<div className="flex items-center justify-between gap-3 flex-wrap">`).

Reemplazar el bloque interior `<div className="flex items-center gap-4 text-xs flex-wrap">` y sus 3 grupos por:

```tsx
<div className="flex items-center gap-6 flex-wrap">
  <div className="flex flex-col">
    <span className="text-[10px] uppercase tracking-wider text-slate-500 flex items-center gap-1">
      <Sigma className="h-3 w-3" /> Subtotal
    </span>
    <span className="font-mono text-2xl font-semibold text-slate-100">{fmtMoney(subtotal, moneda)}</span>
  </div>
  <div className="flex flex-col">
    <span className="text-[10px] uppercase tracking-wider text-slate-500 flex items-center gap-1">
      <Percent className="h-3 w-3" /> IVA ({config.iva_pct_label})
    </span>
    <span className="font-mono text-xs text-slate-400">{fmtMoney(iva, moneda)}</span>
  </div>
  <div className="flex flex-col">
    <span className="text-[10px] uppercase tracking-wider text-slate-500 flex items-center gap-1">
      <Coins className="h-3 w-3 text-accent-glow" /> Total
    </span>
    <span className="font-mono text-2xl font-bold text-accent-glow">{fmtMoney(total, moneda)}</span>
  </div>
  {cart.length > 0 && (
    <span
      className={`self-center text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border flex items-center gap-1 ${avgClass}`}
      title="Utilidad promedio del carrito"
    >
      <TrendingUp className="h-2.5 w-2.5" />
      Util prom. {margenStats.avg.toFixed(1)}%
    </span>
  )}
</div>
```

Cambios clave:
- `text-xs` → `text-2xl` para Subtotal y Total
- IVA queda chico (`text-xs`) y atenuado (`text-slate-400`)
- Labels arriba de los importes (`flex flex-col`) en vez de inline
- Container con `gap-6` para más respiro entre los 3 grupos
- El chip "Util prom." se mantiene con `self-center` para no estirarse al alto del grupo

- [ ] **Step 2: Aumentar el padding del container del TotalsBar**

El `<div className="sticky bottom-0 bg-slate-900 border-t border-slate-800 px-4 py-2">` cámbialo a:

```tsx
<div className="sticky bottom-0 bg-slate-900 border-t border-slate-800 px-4 py-3">
```

(`py-2` → `py-3` para acomodar el alto extra.)

- [ ] **Step 3: tsc + build**

```bash
cd web && npx tsc --noEmit 2>&1 | tail -10
cd web && npm run build 2>&1 | tail -8
```

Expected: tsc clean, build success.

- [ ] **Step 4: Commit**

```bash
git add web/src/features/cotizador/components/TotalsBar.tsx
git commit -m "style(cotizador): subtotal y total grandes en TotalsBar

Subtotal y Total ahora text-2xl con labels arriba. IVA queda discreto
(text-xs slate-400) porque se deriva del subtotal. Padding vertical
sube de py-2 a py-3 para acomodar la altura nueva.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: F1 — Banner "Selecciona cliente primero"

**Files:**
- Modify: `web/src/features/cotizador/components/HeaderCotizacion.tsx`

- [ ] **Step 1: Agregar el banner en `HeaderCotizacion.tsx`**

Justo antes del `return (` del componente, agregar la lógica:

```tsx
const cart = useCotizador((s) => s.cart);  // ya existe — no duplicar si está
const clienteId = useCotizador((s) => s.cliente_id);  // ya existe en este archivo

// Banner: solo cuando hay actividad (cart o moneda/TC tocados) sin cliente.
// "Tocado" se aproxima con: hay líneas en cart, o la moneda es USD (default es MXN),
// o el TC se editó manualmente (tc != 1 y != banxico). Simplificamos: si cart.length > 0
// sin cliente, mostramos el banner.
const showClienteBanner = clienteId == null && cart.length > 0;
```

Verifica si `cart` y `clienteId` ya se leen en el componente (mirar la sección de selectores arriba del `useEffect`). Si ya existen, no los redefines.

Luego, en el JSX, ANTES del `<div className="bg-slate-900 border border-slate-800 rounded-xl p-3 grid …">` agregar:

```tsx
{showClienteBanner && (
  <div className="mb-2 px-3 py-2 rounded-md bg-amber-900/20 border border-amber-700/50 text-amber-200 text-xs flex items-center gap-2">
    <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
    <span>
      Selecciona un cliente para que esta cotización pueda guardarse.
    </span>
  </div>
)}
```

Y agregar `AlertTriangle` al import de lucide-react al inicio del archivo:

```tsx
// ANTES
import { User, Coins, ArrowRightLeft, CalendarPlus, CalendarClock } from 'lucide-react';

// DESPUÉS
import { User, Coins, ArrowRightLeft, CalendarPlus, CalendarClock, AlertTriangle } from 'lucide-react';
```

Como el wrapper del JSX hoy es un `<div>` único, hay que envolver el banner + el grid en un fragment:

```tsx
// ANTES
return (
  <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 grid …">
    {/* ... */}
  </div>
);

// DESPUÉS
return (
  <>
    {showClienteBanner && (
      <div className="mb-2 px-3 py-2 rounded-md bg-amber-900/20 border border-amber-700/50 text-amber-200 text-xs flex items-center gap-2">
        <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
        <span>Selecciona un cliente para que esta cotización pueda guardarse.</span>
      </div>
    )}
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 grid …">
      {/* ... */}
    </div>
  </>
);
```

- [ ] **Step 2: tsc + build**

```bash
cd web && npx tsc --noEmit 2>&1 | tail -10
cd web && npm run build 2>&1 | tail -8
```

Expected: tsc clean, build success.

- [ ] **Step 3: Commit**

```bash
git add web/src/features/cotizador/components/HeaderCotizacion.tsx \
        app/static/dist
git commit -m "feat(cotizador): banner Selecciona cliente con productos sin cliente

Banner ámbar al inicio del header cuando hay líneas en el cart pero
no se seleccionó cliente. No bloquea — solo advierte. Se oculta
automáticamente al elegir cliente.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

Nota: este commit incluye `app/static/dist/` con los bundles regenerados de TODAS las tasks anteriores (Tasks 1-5). Si prefieres, cada task puede commitear su propio bundle, pero como las anteriores no lo hicieron (excepto si su archivo lo requería), aquí cerramos. Si Vite no detectó cambios entre commits intermedios, está bien.

Importante: si el repo tiene policy de bundle por commit, regenera y stagea `app/static/dist` al final de **cada** task antes de commitear. Verifica con `git status` después del build de cada task.

---

### Task 6: Verificación manual

**Files:** ninguno. Verificación visual.

- [ ] **Step 1: Levantar backend + frontend**

```bash
uvicorn app.main:app --reload  # terminal 1
cd web && npm run dev          # terminal 2
```

- [ ] **Step 2: F4 — modal Pisar TC eliminado**

En `/cotizador/nueva` como usuario admin: en `TCMiniTable` (bajo el input TC) NO debe aparecer el link "Pisar TC". Solo el botón "↻ Banxico · fecha" a la izquierda.

Editar directamente el input "TC" del header debe funcionar como antes — modificar valor → mini-tabla recalcula direccionales.

- [ ] **Step 3: F5 — tabs**

Tabs primarios (Cotizador/Historial) deben verse:
- Más altos (py-2.5)
- Más bold (font-semibold)
- Con fondo `slate-900/40` y borde inferior 2px

Tabs internos (Productos/Servicios/Fantasmas) deben verse:
- Como chips compactos con bordes redondeados
- Más chicos (text-[11px])
- Sin border-b — fondo `slate-950/40` con `slate-800/60` border en el container
- Visualmente subordinados al input de búsqueda, no se confunden con los primarios

- [ ] **Step 4: F2 — tab Fantasmas**

a) Click en el chip "Fantasmas". El dropdown muestra hasta 50 fantasmas pendientes (los más recientes primero).
b) Escribir parte de una descripción → debe filtrar resultados.
c) Click en un fantasma existente → entra al cart como línea fantasma con su descripción, sku_libre, costo y proveedor.
d) Si no hay resultados → mostrar CTA "Capturar nuevo fantasma" que abre el modal `AgregarFantasmaModal` con la descripción precargada.

- [ ] **Step 5: F3 — subtotal y total grandes**

Agregar 3 productos al cart. En `TotalsBar`:
- Subtotal y Total se ven claramente más grandes que IVA
- Total mantiene `text-accent-glow` (verde glow)
- Labels arriba de los importes
- En pantalla angosta (resize), el flex-wrap los acomoda en columnas

- [ ] **Step 6: F1 — banner cliente**

Empezar cotización sin elegir cliente. Agregar un producto del cart. El banner ámbar "Selecciona un cliente…" debe aparecer arriba del header. Elegir cliente → banner desaparece.

- [ ] **Step 7: Push a `origin/main`**

```bash
git push origin main
```

Railway autodeploy se encarga del resto.

---

## Notas de implementación

- **Orden de tasks:** F4 primero (más simple, sirve de warmup), F5 segundo (visual), F2 tercero (más complejo, mejor con la jerarquía visual ya fix), F3 cuarto (independiente), F1 quinto (también independiente). Esta secuencia minimiza conflictos de merge si se hacen en paralelo.
- **Bundle regenerado:** cada task que toca archivos `.tsx` cambia el bundle. Para mantener consistencia, regenerar y stagear `app/static/dist` en la última task (5) y no en intermedias. Si el bundle se incluye en cada commit el historial se llena de churn — preferible un solo commit de bundle al final, o uno por cada task que toca UI. Decisión del implementer.
- **Fantasmas backend:** no necesita tocarse. El endpoint `GET /api/fantasmas/?q=&estado=PENDIENTE&page_size=50` ya existe. Si el shape cambia, ajustar `useFantasmasSearch.ts` el tipo `FantasmaPrevio`.
- **No hay tests:** este repo no tiene harness (CLAUDE.md lo dice). Verificación es manual + tsc + build. No agregar tests sin antes configurar el harness en una task separada.

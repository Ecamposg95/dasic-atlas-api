# TC explícito en el cotizador (modelo Excel V_03)

**Fecha:** 2026-05-25
**Estado:** Diseño aprobado, pendiente de plan de implementación
**Alcance:** Solo UI del header del cotizador. Backend, persistencia y cálculos ya están implementados.

## Problema

Dasic no aprueba la versión actual del cotizador porque **no ve** los TCs direccionales. El header expone solo el TC DOF (oficial Banxico) y los spreads de ±1 peso que el sistema aplica para protegerse de la variación cambiaria entre cotización y cobro se aplican silenciosamente. El equipo comercial quiere ver explícitamente:

- DOF · Banxico (TC oficial del día, ej. `$17.5461`)
- MN → USD: DOF − 1 con badge verde "−1.00"
- USD → MN: DOF + 1 con badge verde "+1.00"

La transparencia es el objetivo: el spread ya se aplica a las líneas del cart cuando una línea está en divisa distinta a la cotización, pero el usuario no lo ve y no entiende cómo se llega al precio final al cliente.

Referencia: `context/TC V_03 260100.xlsx`, hoja `CotProveedor`, celdas E2/E3/E4 — el Excel original que Dasic usaba antes del sistema expone las 3 celdas editables.

## Estado actual del código (verificado)

Toda la maquinaria está en su lugar excepto la visibilidad.

**Backend (`app/`)**
- `OrdenVenta` tiene `tipo_cambio` (DOF) + `tc_mn_a_usd` + `tc_usd_a_mn` (`app/models/sales.py`).
- `_resolve_directional_tcs` deriva DOF±1 cuando los direccionales vienen `null`.
- `/api/fx/usd-mxn`, `/api/fx/refresh`, `/api/fx/override` (admin) — `app/routers/fx.py`.
- Cache diaria en `tipos_cambio_dia` (`app/models/fx.py`).

**Frontend (`web/src/features/cotizador/`)**
- Store con `tc`, `tc_mn_a_usd`, `tc_usd_a_mn` (`store.ts:34-38`).
- `calc.ts::convertCost` aplica TCs direccionales a cada línea según `productCurrency` vs `moneda` de la cot.
- `calc.ts::convertCostDOF` aplica DOF puro para "Costo OC" en `RowExpanded` (lo que se paga al proveedor).
- `calc.ts::resolveDirectionalTcs` deriva DOF±1 cuando los direccionales son `null`.
- `CartRow` y `TotalsBar` ya consumen los TCs direccionales.

**Lo único que falta:** mostrar los 3 valores en el header.

## Diseño

### Cambio de UI

Bajo el campo `TC` del header (`HeaderCotizacion.tsx`), donde hoy aparece el `FXBadge` con una sola línea "TC oficial: $X (fuente, fecha)", se introduce una mini-tabla de 3 columnas read-only:

```
┌────────────────────────┬───────────────────────────┬───────────────────────────┐
│ DOF · Banxico          │ MN → USD                  │ USD → MN                  │
│ $17.5461               │ $16.5461   ▼ −1.00        │ $18.5461   ▲ +1.00        │
└────────────────────────┴───────────────────────────┴───────────────────────────┘
   ↑                       ↑ badge emerald             ↑ badge emerald
   refresh + fuente arriba
```

- Las 3 columnas tienen el mismo ancho y vienen pegadas al input TC para que se lean como una unidad.
- DOF muestra `store.tc` formateado a 4 decimales.
- MN → USD y USD → MN se computan llamando `resolveDirectionalTcs(tc, tcMnAUsd, tcUsdAMn)` — la **misma función que `CartRow` y `lineImporte` usan para el cálculo real**, garantizando que lo mostrado es lo aplicado.
- Badge: clase `text-emerald-400 bg-emerald-950/40 border-emerald-700/40` (consistente con totales positivos en el theme Atlas ONE), con flecha (`▼` para −, `▲` para +) y el delta formateado a 2 decimales con signo.
- El refresh/fuente actual del `FXBadge` se compacta a una sola línea pequeña sobre la mini-tabla: `↻ Banxico · 2026-05-25`. El click hace lo mismo de hoy (`refreshFX` → `setTc`).

### Resaltado de columna "activa"

Solo informativo, no cambia el cálculo. Se calcula del estado actual del cart:

- Cot en `MXN` con al menos una línea `productCurrency === 'USD'` → la columna **USD → MN** se resalta (borde `border-accent-glow/50` + texto `text-slate-100`).
- Cot en `USD` con al menos una línea `productCurrency === 'MXN'` → la columna **MN → USD** se resalta.
- Sin cruce de monedas → las 3 columnas con `opacity-60` (igual que el input TC en estado "no requerido" hoy).
- DOF nunca se resalta porque siempre se aplica a la OC al proveedor (no al precio del cliente).

### Tooltip explicativo

Al hover de la mini-tabla (no de columnas individuales):

> Spread de ±1 peso. Aplica solo cuando una línea está en divisa distinta a la cotización. Protege a Dasic de la variación cambiaria entre cotización y cobro. La OC al proveedor usa el DOF puro (sin spread).

### Edge cases cubiertos por diseño

1. **Usuario cambia el DOF en vivo** → mini-tabla recalcula (porque deriva del mismo store).
2. **Cot legacy con direccionales overrideados ≠ DOF±1** → muestra los valores reales y el badge calcula el delta real respecto al DOF (ej. `▼ −0.85` o `▲ +1.20`).
3. **Cot MXN sin líneas USD** → toda la mini-tabla atenuada (`opacity-60`), igual que el input TC, para indicar "no aplica ahora".
4. **Pisar TC manualmente** (modal admin) → afecta `store.tc`; los direccionales se rederivan visualmente porque la mini-tabla siempre lee de la misma fuente.
5. **`tc === 0` o estado inicial** → la mini-tabla muestra `—` en las 3 columnas y oculta los badges (`tc <= 0` significa "aún no se conoce TC").

## Archivos a tocar

- **Nuevo:** `web/src/features/cotizador/components/TCMiniTable.tsx` (≤80 líneas, presentation only)
- **Editar:** `web/src/features/cotizador/components/HeaderCotizacion.tsx` — sustituye el bloque del `FXBadge` por `<TCMiniTable />`; el `FXBadge` queda como prop-less child de `TCMiniTable` (botón de refresh).
- **Editar:** `web/src/features/cotizador/components/FXBadge.tsx` — adelgazarlo a una línea (solo `↻ Banxico · YYYY-MM-DD`), conserva el efecto de `refresh.mutateAsync()` + `setTc`.

Sin cambios en `store.ts`, `calc.ts`, `serialize.ts`, backend, ni migraciones.

## Verificación manual (browser)

Después del build (`cd web && npm run build`):

1. **Sin cart, cot MXN** → mini-tabla atenuada, badges visibles pero pálidos.
2. **Cot MXN, agregar producto USD del catálogo** → columna USD→MN se resalta; el `CartRow` muestra el precio convertido con TC+1 (verificar contra la mini-tabla).
3. **Cot USD, agregar producto MXN** → columna MN→USD se resalta; `CartRow` muestra precio convertido con TC−1.
4. **Editar el input TC** (ej. de 17.5461 a 19.0000) → los 3 valores de la mini-tabla cambian en vivo; los totales del cart también.
5. **Cargar una cot legacy** (creada antes de este cambio) con `tc_mn_a_usd = null` → la mini-tabla deriva DOF±1 (mismo comportamiento que hoy en cálculo).
6. **Cargar una cot con directional override** (ej. `tc_mn_a_usd = 17.20` cuando DOF = 17.5461) → mini-tabla muestra `$17.2000 ▼ −0.35`.
7. **Click en refresh (Banxico)** → store.tc se actualiza, mini-tabla recalcula, toast confirma.
8. **Cambiar moneda de la cot MXN→USD con cart mixto** → highlight de columna se invierte.

## No goals

- Editar los direccionales desde la UI. Hoy se pueden persistir (los campos viajan en el payload) pero no se exponen para editar; si Dasic pide flexibilidad en el futuro, abrimos un input adicional. La prioridad de este sub-proyecto es **transparencia**, no flexibilidad.
- Cambiar la fórmula del spread (sigue siendo ±1.00 peso).
- Tocar el render del PDF de cotización u OC. El PDF ya consume los TCs correctos.
- Tocar el `RowExpanded` o `CartRow` (ya muestran "Costo OC" con DOF puro y el badge "USD → MN"/"MN → USD" cuando hay conversión).

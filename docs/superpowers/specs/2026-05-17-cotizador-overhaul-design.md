# Spec: Cotizador UX/UI Overhaul + DB Pool Fix + Sidebar Polish

**Fecha:** 2026-05-17
**Estado:** Aprobado (pendiente plan de implementación)
**Spec previo relacionado:** `2026-05-17-ux-overhaul-design.md` (ya implementado)

## Contexto

Tras el primer UX overhaul el usuario reporta:

1. **Inconsistencias visuales en el cotizador** — 7+ variantes de botones sin sistema, tipografía con 5+ tamaños mezclados sin criterio (text-[9px], [10px], [11px], xs, sm), branding inconsistente (4 azules + 3 emerald + 3 amber), cards con padding aleatorio (p-3/p-4/p-5).
2. **Header del cotizador desperdicia espacio** — 140px verticales solo para cliente/moneda/TC/obs/términos cuando podría ser ~48px en toolbar horizontal.
3. **Botones triplicados** Producto/Ad-hoc/Fantasma aparecen en 3 lugares (catálogo, cart header, modal interno) causando confusión.
4. **Panel resumen sticky voluminoso** — 320px ancho × ~600px alto con 7 cards apiladas que podrían consolidarse.
5. **Sidebar con inconsistencias** — texto `text-[8.5px]` microscópico en "Industrial · OPS", 11 items al mismo nivel sin agrupación visual.
6. **QueuePool exhausted en producción** — `sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached`. Bug crítico en Railway: el endpoint `/api/auth/me` falla porque el pool de conexiones DB se agota.

Outcome esperado: cotizador con sistema visual coherente y compacto (header 48px en lugar de 140px, resumen 280px en lugar de 320px), sidebar agrupado y legible, error de pool resuelto para que la app deje de crashearse bajo carga concurrente.

## Decisiones tomadas (confirmadas con usuario)

| Tema | Elección |
|------|----------|
| Alcance | **Refactor visual completo** (todas las áreas del audit) |
| Header del cotizador | **Toolbar 1 fila ~48px** — cliente flex-1, moneda+TC compactos, obs/términos como botones-icono |
| Botones Producto/Servicio/Fantasma | **Solo en cart header** — el catálogo queda puro para búsqueda |
| Panel resumen sticky | **Compactar a 280px** — fusionar cards Total+Desglose+Métricas |
| QueuePool fix | **CRÍTICO** — aumentar pool + sacar I/O (SMTP/Anthropic) fuera de sesión DB |
| Sidebar | **Tipografía corregida + 4 secciones con dividers** |

## Decisiones de diseño visual

### Design tokens (base CSS)

**Tipografía — 4 escalas canónicas:**
| Token | Píxeles | Uso |
|---|---|---|
| `text-xs` | 12px | Labels, badges, metadata |
| `text-sm` | 14px | Body, inputs, botones |
| `text-base` | 16px | Títulos de sección |
| `text-2xl` | 24px | TOTAL grande hero |

Todos los `text-[9px]`, `text-[10px]`, `text-[11px]` se reemplazan por `text-xs`.

**Paleta — 5 colores brand + neutral:**
- Primary: `cyan-500` (acciones primarias)
- Accent gradient: `from-cyan-500 to-blue-500` (TOTAL hero)
- Success: `emerald-500`
- Warning: `amber-500`
- Danger: `rose-500`
- Neutral: `slate-50` → `slate-900`

Reemplazos: `text-blue-900` aislados → `text-cyan-700`. Niveles tipo `emerald-400/500/700/300` se normalizan a un solo nivel por contexto (700 para texto, 500 para fills, 100/15 para fondos).

**Botones — 3 clases canónicas:**
- `.dax-btn-primary` (cyan-500 fill) — acción principal
- `.dax-btn-ghost` (transparent → slate-100 hover) — secundario
- `.dax-btn-pill` con modifiers: `.pill-success`, `.pill-warning`, `.pill-danger` — para toggles coloreados (Servicio/Fantasma/etc)

**Cards — 2 paddings:**
- `.dax-card` (p-4) — default
- `.dax-card-sm` (p-3) — compactas (sub-cards dentro de panel resumen)

**Spacing rhythm:**
- gap-2 (8px) default entre elementos
- gap-3 (12px) entre secciones de un panel

## Componentes detallados

### Fase 0: DB Pool Fix (CRÍTICO, backend)

**Archivos:**
- `app/db/session.py` (o `app/db/__init__.py` según ubicación real del `create_engine`)
- `app/routers/ventas.py` líneas ~1274-1338 (`enviar_correo`) y ~1372-1408 (`ia_resumen`)

**Cambio 1 — Engine config:**
```python
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=20,
    max_overflow=20,
    pool_recycle=3600,
    pool_pre_ping=True,
)
```
(Si `pool_pre_ping=True` ya existe, solo agregar los tres parámetros nuevos.)

**Cambio 2 — `enviar_correo` (ventas.py:1274):**
- Antes de llamar `send_quote_email(...)` (SMTP, hasta 20s), **cerrar la sesión DB**.
- Crear evento con `db.add()` + `db.commit()` + capturar `evento_id` con `db.refresh()`.
- Cerrar `db.close()` (o salir del scope del Depends antes de la llamada).
- Llamar `send_quote_email(...)` sin sesión activa.
- Si necesita actualizar estatus del evento, abrir nueva sesión con `SessionLocal()` y commit.

**Cambio 3 — `ia_resumen` (ventas.py:1372):**
- Mismo patrón. Antes de `sugerir_proximo_paso(...)` (Anthropic API, ~2-5s), cerrar sesión.

**Riesgo:** Medio. Cambiar el flujo de 2 endpoints requiere cuidado para no romper el feedback al frontend. Verificar que la respuesta JSON sigue idéntica.

### Fase 1: Design tokens (CSS)

**Archivos:**
- `app/static/css/cotizador.css` (existe) o nuevo si la deuda lo amerita
- `app/templates/base.html` si se agregan clases globales

**Cambios:**

Agregar al CSS:
```css
/* Botones pill (toggles coloreados) */
.dax-btn-pill {
  @apply inline-flex items-center gap-1.5 px-3 py-2 text-xs font-bold rounded-lg border border-dashed transition;
}
.dax-btn-pill.pill-success {
  @apply border-emerald-300 dark:border-emerald-700
         text-emerald-700 dark:text-emerald-300
         bg-emerald-50 hover:bg-emerald-100 dark:bg-emerald-900/20 dark:hover:bg-emerald-900/40;
}
.dax-btn-pill.pill-warning {
  @apply border-amber-300 dark:border-amber-700
         text-amber-700 dark:text-amber-300
         bg-amber-50 hover:bg-amber-100 dark:bg-amber-900/20 dark:hover:bg-amber-900/40;
}
.dax-btn-pill.pill-danger {
  @apply border-rose-300 dark:border-rose-700
         text-rose-700 dark:text-rose-300
         bg-rose-50 hover:bg-rose-100 dark:bg-rose-900/20 dark:hover:bg-rose-900/40;
}

/* Card small */
.dax-card-sm {
  @apply dax-card p-3;
}
```

Reemplazos de tipografía (búsqueda global en `cotizador.html`):
- `text-[9px]` → `text-xs`
- `text-[10px]` → `text-xs`
- `text-[11px]` → `text-xs`

Reemplazos de color (cotizador.html):
- `text-blue-900 dark:text-cyan-400` (línea 198 del cart-title) → `text-cyan-700 dark:text-cyan-300`
- Cualquier `dax-btn-primary` que tenga override inline (gradiente extra) — confirmar y limpiar
- Eliminar gradientes inline excepto el del Total hero

### Fase 2: Header cotizador — Toolbar 1 fila

**Archivo:** `app/templates/cotizador.html` líneas ~31-79

**Layout actual** (140px alto):
```
grid md:grid-cols-4 gap-4
[Cliente col-span-2] [Moneda] [TC]
[Botones Obs + Términos en fila separada]
```

**Layout nuevo** (~48px alto):
```html
<div class="border-l-4 border-cyan-500 bg-white dark:bg-slate-800 rounded-r-lg shadow-sm p-3
            flex flex-wrap items-center gap-3 mb-3">
  <!-- Cliente: ocupa el espacio principal -->
  <div class="flex-1 min-w-[200px] flex items-center gap-2">
    <label class="text-xs font-bold text-slate-500 uppercase shrink-0">Cliente</label>
    <select id="select-cliente" class="dax-input flex-1 max-w-md" required>
      ...
    </select>
  </div>

  <!-- Moneda compacta -->
  <select id="select-moneda" onchange="cambiarMoneda()"
          class="dax-input w-20 text-sm font-bold">
    <option value="MXN">MXN</option>
    <option value="USD">USD</option>
  </select>

  <!-- TC compacto con badge fuente al hover -->
  <div class="flex items-center gap-1">
    <label class="text-xs text-slate-500">TC</label>
    <input id="input-tc" type="number" min="0" step="0.01" value="20.00"
           class="dax-input w-24 text-right font-mono text-sm">
    <span id="fx-source-chip" class="text-[10px] text-slate-400 hidden sm:inline">SIE</span>
  </div>

  <!-- Acciones: obs + términos -->
  <div class="flex items-center gap-2">
    <button type="button" onclick="abrirModalObs()"
            class="dax-btn-ghost text-xs flex items-center gap-1.5">
      <i class="fas fa-pen-to-square text-[10px]"></i>
      <span class="hidden sm:inline">Obs</span>
      <span id="obs-dot" class="hidden w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
    </button>
    <button type="button" onclick="abrirModalTerminos()"
            class="dax-btn-ghost text-xs flex items-center gap-1.5">
      <i class="fas fa-file-lines text-[10px]"></i>
      <span class="hidden sm:inline">T&C</span>
      <span id="terminos-dot" class="hidden w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
    </button>
  </div>

  <!-- Hidden: storage para values originales (preservados) -->
  <input id="observaciones" type="hidden">
  <textarea id="terminos" class="hidden"></textarea>
</div>

<!-- Banner edición separado (solo si ?edit=) -->
<div id="banner-edicion" class="hidden mb-3 ..."></div>
```

**Comportamiento mobile (<sm):**
- Labels "Obs" y "T&C" se ocultan (queda solo el icono).
- Selects se mantienen, pueden hacer wrap en 2 filas si no caben.
- Altura estimada en móvil: ~80-100px (vs ~240px actual).

### Fase 3: Catálogo izquierdo limpio

**Archivo:** `app/templates/cotizador.html` líneas ~74-128 (después del último commit)

**Cambios:**
1. Eliminar `<div class="grid grid-cols-3 gap-1 mt-2">` con los 3 botones [Producto][Ad-hoc][Fantasma] (líneas ~114-128).
2. Reducir el width de la columna catálogo: `260px` → `240px` en el grid principal:
   ```
   lg:grid-cols-[260px_minmax(0,1fr)_320px]
   →
   lg:grid-cols-[240px_minmax(0,1fr)_280px]
   ```
   (también reduce panel resumen de 320 a 280 — ver Fase 5)
3. Mejorar el "empty state" del catálogo cuando no hay búsqueda: en lugar del icono barcode huérfano, mostrar mensaje "Busca un producto por SKU o nombre" + tip de atajo "Atajo: /".

### Fase 4: Cart header con botones crear

**Archivo:** `app/templates/cotizador.html` líneas ~193-215 (el header del cart)

**Layout nuevo:**
```html
<div class="p-3 bg-slate-50 dark:bg-slate-700 border-b border-slate-200 dark:border-slate-600
            flex flex-wrap justify-between items-center gap-2 flex-none">
  <div class="flex items-center gap-2">
    <span id="cart-title" class="font-bold text-sm text-cyan-700 dark:text-cyan-300">
      Detalle de Partidas
    </span>
    <span class="text-xs bg-cyan-100 dark:bg-slate-600 text-cyan-800 dark:text-cyan-200
                 px-2 py-1 rounded-full font-bold" id="items-count">0 Ítems</span>
  </div>
  <div class="flex items-center gap-2">
    <button type="button" onclick="abrirModalLineaCustom('servicio')"
            title="Servicio ad-hoc (atajo: n)"
            class="dax-btn-pill pill-success">
      <i class="fas fa-wrench text-[10px]"></i>
      <span class="hidden sm:inline">Servicio</span>
    </button>
    <button type="button" onclick="abrirModalLineaCustom('fantasma')"
            title="Producto fantasma (atajo: f)"
            class="dax-btn-pill pill-warning">
      <i class="fas fa-ghost text-[10px]"></i>
      <span class="hidden sm:inline">Fantasma</span>
    </button>
  </div>
</div>
```

(Reemplaza el header actual del cart con clases pill consistentes. La estructura es muy similar a la que ya tiene; solo migran las clases inline a `.dax-btn-pill`).

### Fase 5: Resumen panel compactado (280px)

**Archivo:** `app/templates/cotizador.html` líneas ~284-371 (panel resumen sticky)

**Cambios:**

1. Width: `lg:grid-cols-[...320px]` → `lg:grid-cols-[...280px]` (en el grid principal de la Fase 3).

2. Fusionar cards Total + Desglose + Métricas en una sola card:
```html
<aside id="resumen-panel"
       class="lg:sticky lg:top-4 lg:self-start space-y-3">
  <!-- Header con autosave -->
  <div class="flex items-center justify-between">
    <span class="text-xs font-bold uppercase text-slate-500">Resumen</span>
    <span id="sum-autosave" class="text-[10px] text-emerald-500 hidden">●</span>
  </div>

  <!-- Card unificada: Total + Desglose + Métricas inline -->
  <div class="dax-card overflow-hidden">
    <!-- Total hero -->
    <div class="p-4 bg-gradient-to-br from-cyan-500 to-blue-500 text-white">
      <p class="text-xs uppercase font-bold opacity-80">Total con IVA</p>
      <p class="text-2xl font-black tabular-nums" id="sum-total">$0.00</p>
      <p class="text-xs opacity-80" id="sum-moneda">MXN</p>
    </div>
    <!-- Desglose -->
    <div class="p-3 text-xs space-y-1 border-b border-slate-200 dark:border-slate-700">
      <div class="flex justify-between">
        <span class="text-slate-500">Subtotal</span>
        <span class="tabular-nums font-mono" id="sum-subtotal">$0.00</span>
      </div>
      <div class="flex justify-between">
        <span class="text-slate-500">IVA <span id="lbl-iva-pct">16%</span></span>
        <span class="tabular-nums font-mono" id="sum-iva">$0.00</span>
      </div>
      <div class="flex justify-between" id="sum-desc-row" style="display:none">
        <span class="text-slate-500">Descuentos</span>
        <span class="tabular-nums font-mono text-rose-500" id="sum-desc">-$0.00</span>
      </div>
    </div>
    <!-- Métricas inline (margen + TC) -->
    <div class="p-3 text-xs space-y-1">
      <div class="flex justify-between">
        <span class="text-slate-500">Margen prom</span>
        <span class="font-bold" id="sum-margen">0%</span>
      </div>
      <div class="flex justify-between" id="sum-tc-row" style="display:none">
        <span class="text-slate-500">TC USD/MXN</span>
        <span class="tabular-nums font-mono" id="sum-tc-display">$0.00</span>
      </div>
    </div>
  </div>

  <!-- Botones -->
  <div class="space-y-2">
    <button onclick="guardar('cotizacion')" class="dax-btn-primary w-full">
      <i class="fas fa-save mr-2"></i>Guardar cotización
    </button>
    <button onclick="guardar('pendiente')"
            class="dax-btn-pill pill-success w-full justify-center"
            x-show="$store.user.can('convertir_a_venta')" x-cloak>
      <i class="fas fa-check-circle mr-2"></i>Guardar como venta
    </button>
    <button onclick="window.open('/api/ventas/' + state.lastSavedId + '/pdf')"
            class="dax-btn-ghost w-full justify-center"
            id="sum-btn-pdf" disabled>
      <i class="fas fa-file-pdf mr-2"></i>Ver PDF
    </button>
  </div>

  <!-- Atajos (popover, no inline) -->
  <button onclick="abrirPopoverAtajos()" class="text-xs text-slate-400 hover:text-cyan-500 flex items-center gap-1">
    <i class="fas fa-keyboard text-[10px]"></i>
    Atajos
  </button>
</aside>
```

3. Crear popover de atajos (mini modal):
```html
<div id="popover-atajos" class="hidden fixed inset-0 z-40 ...">
  <ul class="text-xs space-y-2">
    <li><kbd>/</kbd> Buscar producto</li>
    <li><kbd>n</kbd> Nuevo servicio</li>
    <li><kbd>f</kbd> Nuevo fantasma</li>
    <li><kbd>Ctrl+S</kbd> Guardar</li>
    <li><kbd>Ctrl+Z</kbd> Undo</li>
  </ul>
</div>
```

### Fase 6: Sidebar polish

**Archivo:** `app/templates/base.html` líneas ~268-376

**Cambios:**

1. Tipografía: `text-[8.5px]` (línea 299, "Industrial · OPS") → `text-[10px]`.

2. Agrupar items con headers de sección + dividers. Patrón con `x-show` para ocultar el header cuando todos los items del grupo están filtrados por RBAC:
```html
<!-- Section header: visible solo si al menos un item del grupo es visible -->
<p class="sidebar-section-header text-[9px] uppercase font-bold tracking-wider
          text-slate-500 dark:text-slate-600 px-3 mt-3 mb-1"
   x-show="$store.user.canVer('dashboard') || $store.user.canVer('clientes')"
   x-cloak>
  Operación
</p>
<a href="/dashboard" class="sidebar-item ...">Dashboard</a>
<a href="/cuentas-por-cobrar" class="sidebar-item ...">Cuentas por cobrar</a>

<p class="sidebar-section-header ...">Ventas</p>
<a href="/ventas/cotizador" ...>Cotizador</a>
<a href="/seguimiento" ...>Seguimiento</a>
<a href="/clientes" ...>Clientes</a>

<p class="sidebar-section-header ...">Catálogos</p>
<a href="/inventario" ...>Catálogo de productos</a>
<a href="/servicios" ...>Servicios</a>
<a href="/catalogos" ...>Diccionarios</a>

<p class="sidebar-section-header ...">Backoffice</p>
<a href="/compras" ...>Compras</a>
<a href="/reportes" ...>Reportes</a>
<a href="/gastos" ...>Gastos</a>
<a href="/usuarios" ...>Usuarios</a>
```

3. CSS para ocultar headers de sección en modo rail:
```css
body[data-sidebar="rail"] .sidebar-section-header {
  display: none;
}
/* En rail, separar bloques con un border-t sutil */
body[data-sidebar="rail"] .sidebar-section-header + a.sidebar-item {
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid rgba(255,255,255,0.06);
}
```

(Permite que el border-t funcione como separador silencioso en rail.)

## Archivos críticos

### Backend (Fase 0)
- `app/db/session.py` o equivalente — pool config
- `app/routers/ventas.py` — endpoints `enviar_correo` y `ia_resumen`

### Frontend
- `app/static/css/cotizador.css` o `app/static/css/tablas.css` — design tokens
- `app/templates/cotizador.html` — header + catálogo + cart header + resumen panel
- `app/templates/base.html` — sidebar

## Patrones existentes a reutilizar

- `.dax-btn-primary`, `.dax-btn-ghost`: ya existen, se conservan sin cambio.
- `.dax-card`: ya existe, se respeta como base; se agrega `.dax-card-sm`.
- `.dax-badge-green/amber/red/slate`: ya existen; se respetan en chips de líneas del carrito.
- `Alpine.store('toasts')` + `window.toast()`: ya existen; se usan para feedback de cambios.
- `SessionLocal()` patrón: ya existe; el cambio en Fase 0 lo reusa para abrir nuevas sesiones después del SMTP/Anthropic.
- `--sidebar-width`, `--sidebar-rail-width`: ya existen.

## Lo que NO se hace (fuera de alcance)

- Refactor de la lógica de `state.cart` o `renderCart()` del cotizador (cambios solo visuales).
- Cambio de schema DB o endpoints nuevos.
- Reescribir el flujo de plantillas (`abrirPlantillas`, `aplicarPlantilla`).
- Animaciones/transiciones complejas más allá de los hovers ya existentes.
- Compactar otras pantallas (inventario/servicios/clientes/etc) — ya tuvieron su Fase 1 UX previa.
- Conversión async/background tasks para SMTP/Anthropic (el fix de Fase 0 solo libera la sesión DB, no convierte la operación en async).

## Verificación

End-to-end manual después de cada fase:

**Fase 0 (DB pool):**
- `uvicorn --reload` y abrir varias pestañas con sesiones distintas.
- Hacer `GET /api/auth/me` repetidamente (10+ veces simultáneas).
- Verificar que no aparece `QueuePool limit ... reached` en logs.
- Enviar correo desde `/seguimiento` (acción `enviar_correo`): debe responder OK y el evento queda registrado.
- Pedir resumen IA (acción `ia_resumen`): debe responder en ~2-5s sin bloquear otras requests.

**Fase 1 (CSS tokens):**
- Inspeccionar elementos con DevTools: cualquier botón `pill-success` o `pill-warning` debe tener los estilos correctos.
- `grep -rn "text-\[9px\]\|text-\[10px\]\|text-\[11px\]"` en `app/templates/cotizador.html` debe devolver 0 resultados (todos migrados a `text-xs`).

**Fase 2 (header):**
- Visitar `/ventas/cotizador` en viewport 1280px: header en una sola fila, altura ~48px medida con DevTools.
- Resize a móvil 390px: header se acomoda con flex-wrap, sigue compacto (<100px).
- Click "Obs" → modal abre. Click "T&C" → modal abre. Indicadores dot cyan se prenden cuando hay valor.
- Iniciar edición de cotización con `?edit=`: banner aparece debajo del toolbar.

**Fase 3 (catálogo):**
- `grep -A2 "Producto.*Ad-hoc.*Fantasma" app/templates/cotizador.html` debe devolver 0 resultados (botones eliminados).
- Catálogo izquierdo solo tiene tabs + filtros + buscador + lista. Sin botones de crear abajo.

**Fase 4 (cart header):**
- Botones [+ Servicio] y [+ Fantasma] usan clases `.dax-btn-pill.pill-success` y `.pill-warning` (inspeccionar DOM).
- Click → abre modal-linea-custom en el modo correspondiente.

**Fase 5 (resumen):**
- Panel a la derecha mide 280px de ancho (no 320).
- Altura total ~360px (no 600). Card unificada con Total + Desglose + Métricas dentro.
- Click "Atajos" → popover aparece con la lista. Esc cierra.

**Fase 6 (sidebar):**
- Sidebar muestra 4 grupos: Operación, Ventas, Catálogos, Backoffice. Headers con `text-[9px] uppercase`.
- En modo rail: headers desaparecen, separadores horizontales sutiles permanecen.
- "Industrial · OPS" se ve legible (text-[10px]).

## Plan de commits

```
fix(db): aumentar pool size + liberar sesión durante SMTP/Anthropic (Fase 0)
feat(ui): design tokens cotizador — pill buttons + card-sm + typography (Fase 1)
feat(ui): cotizador header toolbar 1 fila ~48px (Fase 2)
feat(ui): catálogo izquierdo limpio sin botones duplicados (Fase 3)
feat(ui): cart header con pill buttons consistentes (Fase 4)
feat(ui): resumen panel compactado 280px + popover atajos (Fase 5)
feat(ui): sidebar agrupado en secciones + tipografía corregida (Fase 6)
```

7 commits aislados.

## Riesgos

- **Fase 0 SMTP/Anthropic**: cerrar y reabrir sesión cambia el flujo. Si hay bugs sutiles donde el endpoint accedía a relaciones lazy-loaded del evento DESPUÉS de la llamada I/O, esos accesos van a fallar porque la sesión está cerrada. Mitigación: serializar todo a dict antes de cerrar.
- **Fase 2 header inline**: cliente puede tener nombre muy largo. `select-cliente.flex-1 max-w-md` se asegura que no rompa el flex. Probar con cliente "Constructora Industrial del Norte S.A. de C.V."
- **Fase 5 fusión Total+Desglose**: hay otras pantallas (PDF render) que pueden depender de IDs específicos como `sum-total`, `sum-iva`, etc. Los IDs se preservan dentro del card unificada.
- **Fase 6 sidebar agrupado**: si el usuario tiene RBAC restrictivo y solo ve algunos items, las secciones pueden quedar vacías. Cada `<p class="sidebar-section-header">` debe tener `x-show` que sume los items visibles del grupo, o tener un `:class="{'hidden': !visibleEnGrupo}"`.

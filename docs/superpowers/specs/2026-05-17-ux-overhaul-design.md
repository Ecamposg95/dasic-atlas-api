# Spec: UX Overhaul — Sidebar rail + Header limpio + Inventario compacto + Cotizador 2-col

**Fecha:** 2026-05-17
**Estado:** Aprobado (pendiente plan de implementación)

## Contexto

El usuario reporta tres dolores concretos:

1. La tabla de `/inventario` requiere scroll horizontal y repite información (13 columnas con datos derivados unos de otros).
2. `/ventas/cotizador` requiere scroll horizontal en el carrito y el espacio no se aprovecha bien.
3. Al ocultar el sidebar desaparece completo; se quiere un modo intermedio "solo iconos" para tener navegación sin perder espacio.
4. El header global tiene botones decorativos (Inbox, Notificaciones) sin handler, ruido visual.

Outcome esperado: ninguna pantalla principal con scroll horizontal en viewports >=1280px, sidebar con 3 modos persistentes, header sin botones muertos, tabla de inventario semántica sin redundancias, cotizador con re-layout 2-col + drawer para catálogo.

## Decisiones tomadas

| Tema | Elección |
|------|----------|
| Sidebar collapsed | **Rail 56px solo iconos + tooltip** (`title`), 3er modo en localStorage. Ciclo `expanded → rail → hidden` con Ctrl+\ |
| Header global | **Eliminar Inbox + Notificaciones** (sin handler). Mantener reloj y toggle de tema |
| Inventario tabla | **8 columnas compactas**, lo eliminado va al cardex (side-panel ya existe) |
| Cotizador layout | **2-col**: carrito (flex) + resumen sticky 320px. Catálogo como **drawer lateral** |
| Header del cotizador | **Compactar** observaciones y términos a botones `✎` / `📋` que abren modal |
| Modales servicio + fantasma | **Fusionar** en uno con toggle `[• Servicio ○ Producto fantasma]` |
| Drawer catálogo cotizador | Búsqueda + tabs Productos/Servicios + filtros marca + categoría |

No se cambia el cardex actual (4 tabs Resumen / Fiscales / Movimientos / Histórico).

## Diseño detallado

### Componente 1: Sidebar rail (56px)

**Archivos:** `app/templates/base.html` (CSS + Alpine state + estructura del aside)

**Cambios:**
- Variable CSS nueva: `--sidebar-rail-width: 56px`
- Alpine `mode` ya existe con valores `expanded` / `hidden`; agregar tercer valor `rail`
- `body[data-sidebar="rail"]` aplica `width: var(--sidebar-rail-width)` al aside y `margin-left: var(--sidebar-rail-width)` al `.main-shell`
- En modo `rail`: `body[data-sidebar="rail"] .sidebar-item > span:not(.sidebar-item-icon) { display: none }` oculta labels
- Header del sidebar (logo + título "DASIC · OPS · Industrial") se reemplaza por solo el isotipo cuadrado cyan con la letra "D"
- Botón colapsar dentro del sidebar (icono `fa-angles-left` agregado en commit f16873d): cicla `expanded → rail` (no `hidden`)
- Atajo Ctrl+\: cicla los 3 estados `expanded → rail → hidden → expanded`
- Botón flotante "Mostrar sidebar" (cuando `hidden`) lleva de regreso a `expanded`
- Tooltip: el `title=` ya existe en cada `.sidebar-item` desde el HTML — no requiere JS adicional, el navegador lo muestra al hover
- Persistencia: `localStorage.dasic_sidebar_mode` ya está cableada; aceptar valor `"rail"` además de los existentes

**Migración suave:** valores antiguos `"collapsed"` en localStorage que ya se normalizan a `"expanded"` (línea 189) se siguen normalizando; valores `"rail"` válidos.

### Componente 2: Header global — quitar Inbox + Notifications

**Archivo:** `app/templates/base.html` (líneas 445-459 aprox)

**Cambio:** eliminar los dos `<button>` que solo tienen `title=` sin `@click`:
- Inbox (icono `fa-inbox`)
- Notifications (icono `fa-bell`)

Mantener todo lo demás del header: hamburguesa móvil, toggle sidebar lg+, búsqueda global, toggle de tema, reloj, `{% block header_actions %}`.

### Componente 3: Inventario tabla compacta

**Archivo:** `app/templates/inventario.html`

**Tabla nueva con 8 columnas y `table-layout: fixed`:**

| # | Columna | Contenido | Ancho |
|---|---------|-----------|-------|
| 1 | Producto | `<p>nombre (bold)</p><p>sku_comercial (mono mute)</p>` | `flex` (auto) |
| 2 | Marca | `marca` truncado | 110px |
| 3 | Categoría | `categoria` truncado | 110px |
| 4 | Stock | pill `12 / 8` (físico/disponible), color por estatus | 90px |
| 5 | Costo | `$X.XX MXN` (admin only con `x-show="$store.user.can('ver_costos')"`) | 100px |
| 6 | Estatus | badge OK/Crítico/Sin stock | 100px |
| 7 | Unid. | `PZA`/`CAJA`/etc | 60px |
| 8 | Acciones | 4 botones (−, +, ✎, 🗑) | 130px |

**Cambios en JS:**
- Eliminar `displaySku()` (ya no se usa porque la celda Producto compone su propio sub-texto)
- Eliminar columnas: SKU interno, Reservado, Disponible (independiente), Mínimo, Descripción

**Campos que migran al cardex (ya existe el side-panel):**
- SKU interno (`sku`): en tab "Resumen", debajo del header con label `Interno: ABCS-0001`
- Reservado, Disponible (independientes): ya estaban en el tab Resumen
- Stock mínimo: ya estaba en tab Resumen
- Descripción del producto: tab Resumen, sección descripción
- Proveedor principal: ya estaba

El cardex queda como está (4 tabs); solo verifico que muestre todo lo migrado.

### Componente 4: Cotizador layout 2-col

**Archivo:** `app/templates/cotizador.html`

**Grid principal:**
```
lg:grid-cols-[minmax(0,1fr)_320px]
```
- Columna izquierda: header compacto + carrito (flex)
- Columna derecha: panel resumen sticky (320px en lg+)
- En `<lg` (tablet+móvil): stack vertical actual; bottom bar móvil se mantiene

**Catálogo como drawer:**
- El bloque `<section aria-labelledby="catalogo-title">` actual (línea 83-138 aprox) se mueve a un drawer lateral `fixed inset-y-0 left-0 w-80`
- Se abre con:
  - Botón en el header del cotizador: `[🔍 Buscar producto/servicio]`
  - Atajo `/` (ya existe; ahora abre el drawer en lugar de hacer focus)
- Backdrop: `bg-black/40` con click-outside para cerrar
- Animación slide-in-from-left con transition
- Estado Alpine: `catalogoDrawerOpen: false`
- Tabs Productos/Servicios dentro del drawer (ya existen como `setPanelTab`)
- Filtros: agregar `select` de marca + `select` de categoría arriba del listado (se cargan en init() vía `/api/productos/utils/categorias` que ya existe)

**Carrito sin scroll horizontal:**
- Tabla del carrito: `table-layout: fixed`
- Anchos por columna:
  - `Producto` flex
  - `Cant.` 80px
  - `Costo` 110px
  - `Util %` 80px
  - `Subtotal` 110px
  - `Acciones` 60px
- Inputs `<input>` dentro de td agregan `min-w-0` y `w-full`
- Descripción del producto en la celda usa `truncate` con `max-w-full`

### Componente 5: Header del cotizador compacto

**Antes** (línea ~31-79):
```
[Cliente▼  cs2] [Moneda▼] [TC] [Observaciones (input largo)]
[▶ Términos y condiciones (collapsible 9 líneas)]
```

**Después:**
```
[Cliente▼  cs2] [Moneda▼] [TC] [+ Agregar línea] [✎ Obs] [📋 Términos]
```

- `Observaciones` pasa a botón `✎` que abre un mini-modal o popover con el textarea
- `Términos y condiciones` (el `<details>` actual) pasa a botón `📋` que abre modal con el textarea + botones "Restaurar default" / "Vaciar"
- El badge de cambios pendientes/autosave puede ir al lado de los botones (un puntito pequeño cuando hay cambios sin guardar)

### Componente 6: Modal fusionado Servicio + Fantasma

**Archivo:** `app/templates/cotizador.html`

**Antes:**
- `<div id="modal-servicio">` líneas 130-169 — 4 inputs: descripción, tarifa, moneda, cantidad
- `<div id="modal-fantasma">` líneas 171-218 — 5 inputs: SKU, descripción, costo, moneda, cantidad + utilidad%

**Después:** un solo `<div id="modal-linea-custom">` con:
- Toggle radio `[• Servicio ○ Producto fantasma]` arriba
- Campos compartidos: descripción, costo, moneda, cantidad
- Campos opcionales:
  - SKU libre (visible solo si tipo = fantasma)
  - Utilidad % (visible solo si tipo = fantasma; servicios fuerzan utilidad = 0)
- Botón "Agregar": llama a `agregarServicio()` o `agregarFantasma()` según el tipo elegido
- Atajos: `n` abre el modal (ya funciona), por default tipo = servicio; `f` abre el modal con tipo = fantasma pre-seleccionado

## Archivos críticos

### Base
- `app/templates/base.html` — sidebar `rail` mode, header sin Inbox/Notif (3 cambios discretos)

### Inventario
- `app/templates/inventario.html` — tabla 8 cols + table-layout fixed + cardex tab Resumen enriquecido

### Cotizador
- `app/templates/cotizador.html` — grid 2-col + drawer catálogo + header compacto + modal fusionado + table-layout fixed en carrito

### CSS
- `app/static/css/tablas.css` — agregar reglas `.dax-table.compact` o usar `table-layout: fixed` en `.dax-table` directamente (decisión: directo en `.dax-table` porque toda la app gana de esto)

## Patrones existentes a reutilizar

- **Tabs Productos/Servicios** en cotizador: ya implementadas como `setPanelTab` en commit anterior (Fase 4 del bloque grande).
- **Filtros marca/categoría**: endpoints `/api/catalogos/marcas` y `/api/productos/utils/categorias` ya existen.
- **Card side-panel cardex**: estructura completa ya en `inventario.html` con `sidePanel()` Alpine state.
- **Toast global**: `window.toast()` para feedback al cerrar modales o aplicar cambios.
- **Persistencia localStorage**: patrón `dasic_sidebar_mode` ya está, solo aceptar valor nuevo `rail`.
- **`$store.user.can(...)`**: para `ver_costos` en columna Costo del inventario.

## Lo que NO se hace (fuera de alcance)

- Cambios a la lógica de backend (queries, endpoints, modelos).
- Rediseño del cardex (queda con sus 4 tabs).
- Cambios al dashboard, clientes, compras, CRM, reportes — solo inventario y cotizador.
- Implementar Inbox/Notifications de verdad (decisión: eliminar, no implementar).
- Cambios al footer / sticky bottom-bar móvil del cotizador (funciona bien hoy).
- Cambios al tab Servicios del módulo Diccionarios (recién armado).

## Verificación

End-to-end manual después de cada commit:

1. **Sidebar:**
   - Cargar `/dashboard`. Sidebar inicial = `expanded`.
   - Click botón colapsar dentro del sidebar → pasa a `rail` (56px, solo iconos).
   - Hover sobre un icono → tooltip muestra el label.
   - Recargar página → mantiene `rail` (localStorage).
   - Ctrl+\ → cicla a `hidden`. Ctrl+\ otra vez → vuelve a `expanded`.
   - Botón flotante "mostrar" aparece solo cuando `hidden`.

2. **Header:**
   - Visitar cualquier página. No deben aparecer iconos de Inbox ni Notifications.
   - Toggle de tema y reloj siguen funcionando.

3. **Inventario:**
   - Cargar `/inventario` en viewport 1280px con sidebar en `expanded`. Tabla cabe sin scroll horizontal.
   - Mismo viewport pero sidebar en `rail`. Tabla con más respiro.
   - Click en una fila → cardex abre con tabs Resumen/Fiscales/Movs/Histórico.
   - El cardex tab Resumen muestra SKU interno, Reservado, Disponible, Mínimo, Descripción, Proveedor.
   - Mobile (390px): tabla scrollea horizontalmente solo en móvil (ahí sí, no es problema).

4. **Cotizador:**
   - `/ventas/cotizador` en lg+: layout 2-col (carrito flex + resumen 320px).
   - El catálogo izquierdo está oculto por defecto.
   - Click en "🔍 Buscar producto/servicio" → drawer se abre desde la izquierda con backdrop.
   - Drawer tiene tabs Productos/Servicios + filtros Marca + Categoría + búsqueda.
   - Tabla del carrito no scrollea horizontalmente en lg+.
   - Botón "✎ Obs" abre modal con el textarea de observaciones.
   - Botón "📋 Términos" abre modal con términos editables.
   - Botón "+ Línea" (o atajo `n`) abre modal fusionado con toggle Servicio/Fantasma.

5. **Regresión cero esperada:**
   - Crear nueva cotización: misma cantidad de clicks que antes.
   - Editar producto existente: modal no cambia internamente (sigue con sus fieldsets).
   - Convertir cotización a venta: flujo intacto.

## Riesgos

- **Sidebar rail en móvil**: el sidebar móvil se comporta diferente (overlay). El modo `rail` debe ser solo lg+; en `<lg` se ignora y se usa el sidebar móvil actual.
- **Tabla con table-layout: fixed**: las columnas con ancho fijo no se autoexpanden si el contenido es largo. Los `truncate` deben estar bien puestos.
- **Drawer + Alpine focus management**: al abrir el drawer, el input de búsqueda debe recibir focus con `$nextTick`.
- **Atajo `/`**: hoy hace focus en el input del catálogo. Ahora debe abrir el drawer + hacer focus. Verificar que no rompa al usuario que ya tiene memoria muscular.
- **Modal fusionado Servicio/Fantasma**: las funciones `agregarServicio()` y `agregarFantasma()` se mantienen separadas; el modal nuevo solo decide cuál llamar. Riesgo: olvidar pasar utilidad=0 cuando tipo=servicio.

## Plan de commits sugerido

```
feat(ui): sidebar rail mode 56px solo iconos
feat(ui): eliminar botones header sin handler (inbox + notifications)
feat(ui): inventario tabla 8 cols + table-layout fixed
feat(ui): cotizador 2-col layout + drawer catálogo
feat(ui): cotizador header compacto + modal servicio/fantasma fusionado
```

Cada uno aislado para que regresión sea localizable.

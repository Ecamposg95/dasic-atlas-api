# Sidebar Redesign — Design Spec

**Date:** 2026-04-28
**Owner:** Atlas_Tech
**Scope:** Arreglar la regresión donde clicar "Cotizador" siempre redirige a `/dashboard` y reestructurar el sidebar a single-column estilo Linear/Notion con grupos colapsables y agrupación más semántica.

---

## 1. Decisiones marco

| # | Decisión | Justificación |
|---|---|---|
| 1 | **Migrar `cotizador.html` a extender `base.html`** | Elimina la regresión raíz: la plantilla legacy hace `localStorage.getItem('token')` y rebota a `/` → `/dashboard`. |
| 2 | **Eliminar `app/static/js/navbar.js`** | Cero consumidores tras la migración. Es el sidebar viejo basado en JS-injection. |
| 3 | **Sidebar single-column (sin rail)** | Linear/Notion style: todos los grupos visibles, sin clicks ocultos. La estructura rail+panel actual es la causa del UX "no funcionan las rutas" — los items quedaban escondidos detrás de un click previo en el rail. |
| 4 | **Grupos colapsables con persistencia** | El usuario puede ocultar grupos que no usa; el estado vive en `localStorage`. |
| 5 | **Reagrupación semántica (opción C)** | Separa CRM (flujo comercial) de Reportes (lectura/finanzas) y Sistema (admin). |
| 6 | **Auth solo por cookie** | Quitar TODA referencia a `localStorage.getItem('token')` en plantillas; el cookie HttpOnly + `_protected_view` ya cubren auth SSR. |

---

## 2. Forma de la entrega — 2 fases

```
Fase 1: Bug fix      → cotizador.html migrada, navbar.js borrado
Fase 2: Restructure  → sidebar single-column en base.html
```

Cada fase es un commit aparte y mergeable. Se pueden ejecutar en una sola rama secuencialmente.

---

## 3. Fase 1 — Bug fix (cotizador.html)

### Estado actual de `app/templates/cotizador.html`

Es una plantilla **standalone** (no extiende `base.html`). Contiene su propio `<!DOCTYPE html>`, `<head>`, `<body>` y:

```html
<script>if (!localStorage.getItem('token')) { window.location.href = "/"; }</script>
<div id="sidebar-container"></div>
...
<script src="/static/js/navbar.js"></script>
```

### Estado objetivo

Estructura idéntica a `dashboard.html`, `clientes.html`, etc.:

```jinja
{% extends "base.html" %}

{% block title %}Cotizador{% endblock %}
{% block page_title %}Cotizador{% endblock %}

{% block extra_head %}
  <link rel="stylesheet" href="{{ url_for('static', path='css/cotizador.css') }}">
  <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
{% endblock %}

{% block content %}
  <!-- contenido específico del cotizador (tabs, formularios, modales) -->
{% endblock %}

{% block extra_scripts %}
  <!-- scripts inline + <script src="/static/js/cotizador.js"> si aplica -->
{% endblock %}
```

### Cambios específicos

1. Eliminar `<!DOCTYPE html>`, `<html>`, `<head>` propios y todo el `<body class="...">` envolvente.
2. Eliminar la línea `<script>if (!localStorage.getItem('token')) { window.location.href = "/"; }</script>` (auth la maneja `_protected_view` server-side).
3. Eliminar `<div id="sidebar-container"></div>`.
4. Eliminar `<script src="/static/js/navbar.js"></script>`.
5. Eliminar el script que lee `const token = localStorage.getItem('token');` (línea ~204) — si el cotizador necesita el id de usuario, lo recibe de `current_user` en Jinja.
6. Mover CSS específico (`<link rel="stylesheet" href="...cotizador.css">`) a `{% block extra_head %}`.
7. Mover el contenido del `<main>` actual al `{% block content %}`.
8. Mover scripts del cotizador a `{% block extra_scripts %}`.
9. **Stripear `dark:` modifiers del cotizador.** El template hoy usa pares `text-slate-800 dark:text-slate-200`, `bg-slate-100 dark:bg-slate-950`, etc. La app entera es dark-only (sin `dark:` modifiers, sin `darkMode: 'class'` en `base.html`). Reemplazar cada par con la variante dark sola:
   - `text-slate-800 dark:text-slate-200` → `text-slate-200`
   - `bg-slate-100 dark:bg-slate-950` → `bg-slate-950` (o el color contextual del fondo de `base.html`)
   - `border-slate-300 dark:border-slate-700` → `border-slate-700`
   - etc.

   Esto evita tener que portar `darkMode: 'class'` y mantiene consistencia con el resto de la app.

### Cleanup adicional

10. `git rm app/static/js/navbar.js`. Cero referencias salvo desde `cotizador.html` (que ya no lo usa).

### Criterio de done

- Login → click "Cotizador" en el sidebar → URL queda en `/ventas/cotizador` → se ve la UI del cotizador con sidebar de `base.html` (no el del navbar.js viejo).
- `git grep -nE "localStorage.getItem\('token'\)|navbar\.js|sidebar-container" app/` devuelve cero hits.
- Las features del cotizador siguen funcionando: tabs, búsqueda de productos, agregar líneas, generar PDF, pipeline de cotizaciones.

---

## 4. Fase 2 — Sidebar single-column (`base.html`)

### Estado actual

Doble columna: rail 56px (4 botones de sección) + panel 240px (items de UNA sección activa). Modos: `expanded`, `collapsed` (solo rail), `hidden`. Toggle `Ctrl+[`.

### Estado objetivo

Una sola columna 256px. Modos: `expanded`, `hidden`. Toggle `Ctrl+\` (y `Cmd+\` en macOS). Todos los grupos siempre presentes; cada grupo tiene un toggle expand/collapse propio.

### Estructura del menú

```
┌──────────────────────────┐
│ [Logo] DASIC             │
│        Industrial ERP    │
├──────────────────────────┤
│ 🔍 Quick search    ⌘K    │
│ 📥 Inbox            0    │
│ 🔔 Notifications    0    │
├──────────────────────────┤
│ RESUMEN          ▾       │
│   📈 Dashboard           │
│                          │
│ CRM              ▾       │
│   👥 Clientes            │
│   🛒 Cotizador           │
│   🛣️ Seguimiento         │
│                          │
│ OPERACIÓN        ▾       │
│   📦 Inventario          │
│   🚚 Compras             │
│                          │
│ REPORTES         ▾       │
│   📊 Reportes            │
│   💰 Gastos              │
│                          │
│ SISTEMA          ▾       │
│   👤 Usuarios            │
├──────────────────────────┤
│ [👤] Emmanuel       [↗]  │
│      En línea            │
└──────────────────────────┘
```

### Mapping ruta → grupo (Jinja, para auto-expand del grupo activo en primera visita)

```jinja
{% set _path = request.url.path %}
{% set _group_active = 'resumen' %}
{% if _path in ['/clientes', '/seguimiento'] or '/cotizador' in _path %}
  {% set _group_active = 'crm' %}
{% elif _path in ['/inventario', '/compras'] %}
  {% set _group_active = 'operacion' %}
{% elif _path in ['/reportes', '/gastos'] %}
  {% set _group_active = 'reportes' %}
{% elif _path in ['/usuarios'] %}
  {% set _group_active = 'sistema' %}
{% endif %}
```

### Tokens CSS resultantes

```css
:root {
  --sidebar-width: 256px;       /* única — antes había rail+total */
  --sidebar-bg: #0d1b3e;
  --sidebar-bg-bottom: #050d22;
  --sidebar-text: #ffffff;
  --sidebar-active-bg: rgba(255,255,255,0.10);
  --sidebar-hover-bg: rgba(255,255,255,0.06);
  --sidebar-accent: #2563eb;
  --sidebar-accent-glow: #00d4e0;
  --header-h: 64px;
  --footer-h: 36px;
}
```

Eliminadas: `--sidebar-rail-width`, `--sidebar-panel-width`, `--sidebar-total-width`.

### Layout principal (margen del `main-shell`)

```css
.main-shell { margin-left: 0; transition: margin-left 0.22s ease; }
@media (min-width: 1024px) {
  body[data-sidebar="expanded"] .main-shell { margin-left: var(--sidebar-width); }
  body[data-sidebar="hidden"]   .main-shell { margin-left: 0; }
}
```

### Componentes Alpine resultantes (`<body x-data>`)

```js
{
  sidebarMobile: false,
  mode: localStorage.getItem('dasic_sidebar_mode') || 'expanded',
  groups: JSON.parse(localStorage.getItem('dasic_sidebar_groups') || 'null') || null,
  searchOpen: false,

  setMode(m) {
    this.mode = m;
    localStorage.setItem('dasic_sidebar_mode', m);
    document.body.dataset.sidebar = m;
  },
  hide() { this.setMode('hidden'); },
  show() { this.setMode('expanded'); },

  isGroupOpen(key) {
    if (this.groups && key in this.groups) return this.groups[key];
    // Default: el grupo activo abierto, los demás abiertos también (todos abiertos por default).
    return true;
  },
  toggleGroup(key) {
    const next = { ...(this.groups || {}), [key]: !this.isGroupOpen(key) };
    this.groups = next;
    localStorage.setItem('dasic_sidebar_groups', JSON.stringify(next));
  }
}
```

Default: todos los grupos abiertos en primera visita. El usuario los colapsa/expande explícitamente y se persiste.

### Markup de cada grupo (patrón repetido)

```html
<div class="sidebar-group">
  <button class="sidebar-group-header" @click="toggleGroup('crm')">
    <span class="sidebar-group-title">CRM</span>
    <i class="fas fa-chevron-down sidebar-group-chevron"
       :class="isGroupOpen('crm') ? 'rotate-0' : '-rotate-90'"></i>
  </button>
  <div x-show="isGroupOpen('crm')" x-collapse class="sidebar-group-items">
    <a href="/clientes" class="sidebar-item {% if _path == '/clientes' %}is-active{% endif %}">
      <i class="fas fa-users sidebar-item-icon"></i>
      <span>Clientes</span>
    </a>
    <a href="/ventas/cotizador" class="sidebar-item {% if '/cotizador' in _path %}is-active{% endif %}">
      <i class="fas fa-cash-register sidebar-item-icon"></i>
      <span>Cotizador</span>
    </a>
    <a href="/seguimiento" class="sidebar-item {% if _path == '/seguimiento' %}is-active{% endif %}">
      <i class="fas fa-route sidebar-item-icon"></i>
      <span>Seguimiento</span>
    </a>
  </div>
</div>
```

`x-collapse` viene de Alpine.js plugin "collapse" — agregar carga vía CDN si no está ya:
```html
<script defer src="https://cdn.jsdelivr.net/npm/@alpinejs/collapse@3.x.x/dist/cdn.min.js"></script>
```

(Cargar ANTES de Alpine core para que el plugin se registre.)

### Atajos de teclado

- `Cmd+K` / `Ctrl+K` → quick search (sin cambios).
- `Cmd+\` / `Ctrl+\` → toggle hide/show del sidebar.
- Eliminado: `Cmd+[` / `Ctrl+[` (era para colapsar al rail; ya no aplica).

### Cleanup colateral

- Eliminar todas las clases CSS del rail: `.rail-btn`, `.rail-btn:hover`, `.rail-btn.is-active`, `.rail-btn.is-active::before`.
- Eliminar `.panel-item`, `.panel-icon`, `.panel-section-title` (reemplazadas por `.sidebar-item`, `.sidebar-item-icon`, `.sidebar-group-title`).
- Eliminar el `<div class="rail">` entero del `<aside>`.
- Eliminar el botón flotante `x-show="mode === 'hidden'"` superior izquierdo si lo movemos al header (queda igual — sigue siendo útil).
- Eliminar variables CSS no usadas (`--sidebar-rail-width`, etc.).

### Footer del sidebar

Sin cambios. Mantiene avatar + nombre + indicador "En línea" + botón logout (form POST a `/api/auth/logout`).

### Header de marca

Sin cambios significativos. "DASIC" + "Industrial ERP" pequeño debajo.

### Quick rows (Quick search / Inbox / Notifications)

Sin cambios. Siguen siendo placeholders. Quick search abre el modal con `Cmd+K`.

### Criterio de done

- Login → todas las 9 rutas SSR (`/dashboard`, `/clientes`, `/ventas/cotizador`, `/seguimiento`, `/inventario`, `/compras`, `/gastos`, `/reportes`, `/usuarios`) son visibles en el sidebar sin necesidad de clicar nada previo.
- Click en cualquier item navega correctamente y la URL refleja la ruta.
- El item de la página actual aparece resaltado (`is-active`).
- Toggle de grupo individual: click en el header de "CRM" colapsa solo ese grupo; reload conserva el estado.
- Toggle global: `Ctrl+\` oculta el sidebar; el botón flotante permite reabrirlo.
- Mobile (<1024px): el sidebar es offcanvas, se abre con el botón hamburger del header.
- Cero referencias en grep a: `rail-btn`, `panel-item`, `panel-section-title`, `--sidebar-rail-width`, `--sidebar-panel-width`, `--sidebar-total-width`, `mode === 'collapsed'`.

---

## 5. Migración del estado en localStorage

Usuarios actuales tienen `localStorage.dasic_sidebar_mode` con valor `'expanded'`, `'collapsed'`, o `'hidden'`. Tras este cambio:

- `'expanded'` y `'hidden'` siguen siendo válidos.
- `'collapsed'` se trata como `'expanded'` (el nuevo `setMode` lo normaliza al cargar):

```js
// En x-init o al construir mode:
let saved = localStorage.getItem('dasic_sidebar_mode');
if (saved === 'collapsed') saved = 'expanded';
this.mode = saved || 'expanded';
```

`dasic_sidebar_groups` es nuevo — null en usuarios existentes, se llena al primer toggle.

---

## 6. Out of scope

- Búsqueda funcional (`Cmd+K` sigue siendo placeholder).
- Inbox / Notifications con datos reales.
- Subitems anidados (3 niveles).
- Customización por usuario del orden de grupos o ítems.
- Cambio de íconos / paleta — se respetan los actuales.

---

## 7. Riesgos

| # | Riesgo | Mitigación |
|---|---|---|
| R1 | El cotizador pierde funcionalidad al migrarlo (CSS roto, scripts mal ubicados) | Smoke test manual: crear cotización, agregar línea, generar PDF, ver historial. Si algo se rompe, identificar el bloque mal movido y corregir. |
| R2 | Plugin `@alpinejs/collapse` no carga (CSP, CDN caído) | Fallback: usar `x-show` con `x-transition.duration.150ms` en lugar de `x-collapse` — animación menos suave pero funcional. |
| R3 | Usuarios con sidebar en modo `collapsed` viejo se desconciertan al ver todo abierto | Migración silenciosa: `'collapsed'` → `'expanded'`. Sin warning, sin notificación. |
| R4 | Grupos vacíos por permisos futuros (RBAC oculta items) | No aplica todavía — todos los items son visibles para todos los roles autenticados. Cuando entre RBAC granular, ocultar el grupo si no tiene items. |

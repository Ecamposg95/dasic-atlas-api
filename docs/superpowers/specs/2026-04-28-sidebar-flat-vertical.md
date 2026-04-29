# Sidebar Flat Vertical — Design Spec

**Date:** 2026-04-28
**Owner:** Atlas_Tech
**Scope:** Eliminar la agrupación colapsable del sidebar y dejar los 9 módulos como una lista plana vertical, en un solo bloque, sin headers de grupo ni interacción de expand/collapse.

---

## 1. Decisiones marco

| # | Decisión | Justificación |
|---|---|---|
| 1 | **Lista plana sin grupos** | El usuario seleccionó la opción A. Los headers colapsables y los grupos eran fricción innecesaria — los 9 módulos caben con holgura en una sola columna. |
| 2 | **Eliminar plugin `@alpinejs/collapse`** | Sin grupos colapsables, el plugin ya no aporta valor. Un `<script>` menos. |
| 3 | **Limpieza pasiva del localStorage `dasic_sidebar_groups`** | Las claves huérfanas no afectan nada. Sin migración activa. |
| 4 | **Preservar `.sidebar-item` y `.sidebar-item-icon`** | Estilos de item siguen siendo el activo. Solo se borran las clases de grupo. |
| 5 | **Orden actual mantenido** | `Dashboard / Clientes / Cotizador / Seguimiento / Inventario / Compras / Reportes / Gastos / Usuarios` — preserva la lógica de flujo (resumen → CRM → ops → reportes → admin) sin etiquetas. |

---

## 2. Forma — un solo commit

Edición localizada a `app/templates/base.html`. 5 sub-cambios que se aplican atómicamente:

1. Eliminar `<script>` del plugin `@alpinejs/collapse`.
2. Limpiar el `x-data` del `<body>`: quitar `groups`, `isGroupOpen`, `toggleGroup`.
3. Eliminar reglas CSS `.sidebar-group*` del bloque `<style>`.
4. Reemplazar el `<nav>` con 9 `<a class="sidebar-item">` planos.
5. (No-op): la clave `dasic_sidebar_groups` queda huérfana en navegadores; no se purga.

---

## 3. Estado objetivo del `<nav>`

```html
<nav class="flex-1 min-h-0 overflow-y-auto px-3 py-3 space-y-1">
  <a href="/dashboard" class="sidebar-item {% if _path == '/dashboard' %}is-active{% endif %}">
    <span class="sidebar-item-icon"><i class="fas fa-chart-line text-[12px]"></i></span>
    <span>Dashboard</span>
  </a>
  <a href="/clientes" class="sidebar-item {% if _path == '/clientes' %}is-active{% endif %}">
    <span class="sidebar-item-icon"><i class="fas fa-users text-[12px]"></i></span>
    <span>Clientes</span>
  </a>
  <a href="/ventas/cotizador" class="sidebar-item {% if '/cotizador' in _path %}is-active{% endif %}">
    <span class="sidebar-item-icon"><i class="fas fa-cash-register text-[12px]"></i></span>
    <span>Cotizador</span>
  </a>
  <a href="/seguimiento" class="sidebar-item {% if _path == '/seguimiento' %}is-active{% endif %}">
    <span class="sidebar-item-icon"><i class="fas fa-route text-[12px]"></i></span>
    <span>Seguimiento</span>
  </a>
  <a href="/inventario" class="sidebar-item {% if _path == '/inventario' %}is-active{% endif %}">
    <span class="sidebar-item-icon"><i class="fas fa-boxes-stacked text-[12px]"></i></span>
    <span>Inventario</span>
  </a>
  <a href="/compras" class="sidebar-item {% if _path == '/compras' %}is-active{% endif %}">
    <span class="sidebar-item-icon"><i class="fas fa-truck text-[12px]"></i></span>
    <span>Compras</span>
  </a>
  <a href="/reportes" class="sidebar-item {% if _path == '/reportes' %}is-active{% endif %}">
    <span class="sidebar-item-icon"><i class="fas fa-chart-pie text-[12px]"></i></span>
    <span>Reportes</span>
  </a>
  <a href="/gastos" class="sidebar-item {% if _path == '/gastos' %}is-active{% endif %}">
    <span class="sidebar-item-icon"><i class="fas fa-file-invoice-dollar text-[12px]"></i></span>
    <span>Gastos</span>
  </a>
  <a href="/usuarios" class="sidebar-item {% if _path == '/usuarios' %}is-active{% endif %}">
    <span class="sidebar-item-icon"><i class="fas fa-user-shield text-[12px]"></i></span>
    <span>Usuarios</span>
  </a>
</nav>
```

`mt-2` actual del `<nav>` se cambia por `py-3` (respiro arriba y abajo). Sin `mt-2` adicional.

---

## 4. Estado objetivo del `<body x-data>`

```html
<body class="h-full bg-slate-900 text-slate-200 font-sans antialiased"
      x-data="{
        searchOpen: false,
        sidebarMobile: false,
        mode: (function(){ const s = localStorage.getItem('dasic_sidebar_mode'); return s === 'collapsed' ? 'expanded' : (s || 'expanded'); })(),
        setMode(m) { this.mode = m; localStorage.setItem('dasic_sidebar_mode', m); document.body.dataset.sidebar = m; },
        hide() { this.setMode('hidden'); },
        show() { this.setMode('expanded'); }
      }"
      x-init="document.body.dataset.sidebar = mode"
      :data-sidebar="mode"
      @keydown.meta.k.window.prevent="searchOpen = true"
      @keydown.ctrl.k.window.prevent="searchOpen = true"
      @keydown.window="if ($event.key === '\\' && ($event.metaKey || $event.ctrlKey)) { $event.preventDefault(); mode === 'hidden' ? show() : hide(); }">
```

Eliminados: `groups`, `isGroupOpen`, `toggleGroup`. El resto sin cambios.

---

## 5. CSS a eliminar

Dentro del bloque `<style>`, borrar las siguientes reglas (Task 1 de Sidebar Tactical Restyle las introdujo):

```css
.sidebar-group { @apply mt-3; }
.sidebar-group:first-of-type { @apply mt-1; }
.sidebar-group:not(:first-of-type) {
  border-top: 1px solid var(--sidebar-rule);
  padding-top: 12px;
}

.sidebar-group-header {
  @apply w-full flex items-center justify-between rounded-md px-2.5 py-2
         text-[10px] font-bold uppercase tracking-[0.28em] text-white/45
         hover:text-white/75 hover:bg-white/5 transition-colors;
}
.sidebar-group-chevron { @apply text-[9px] transition-transform duration-200 text-white/30; }
.sidebar-group-items { @apply mt-1 mb-1 space-y-1; }
```

`.sidebar-item` y `.sidebar-item-icon` se conservan exactamente como están.

---

## 6. Script a eliminar

```html
<!-- Alpine.js + collapse plugin (deferred; plugin must load BEFORE core) -->
<script defer src="https://cdn.jsdelivr.net/npm/@alpinejs/collapse@3.x.x/dist/cdn.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

Pasa a:
```html
<!-- Alpine.js (deferred) -->
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

---

## 7. Comportamientos preservados

- `Cmd/Ctrl+K` abre Quick Search.
- `Cmd/Ctrl+\` toggle hide/show del sidebar.
- Active item highlight por `_path`.
- Header (search inline + Inbox + Notifications + clock) sin cambios.
- Footer card del usuario (avatar + nombre + rol + ONLINE + v2.0) sin cambios.
- Mobile backdrop + botón flotante "Mostrar sidebar" sin cambios.

---

## 8. Out of scope

- Búsqueda dentro del sidebar.
- Badges de count en items (cotizaciones pendientes, stock crítico, etc.).
- Reordering por usuario.
- Subitems anidados.
- Limpieza activa del localStorage `dasic_sidebar_groups` (queda inerte).

---

## 9. Riesgos

| # | Riesgo | Mitigación |
|---|---|---|
| R1 | El plugin `@alpinejs/collapse` está cargado en otra plantilla (cotizador, etc.) y al borrarlo aquí se rompe algo | Solo `base.html` lo cargaba. Cotizador extiende base.html sin agregar Alpine plugins. Verificado en grep durante smoke. |
| R2 | Algún sticker visual depende de `.sidebar-group` indirectamente | El uso es exclusivo del sidebar. Smoke test confirma 9/9 rutas SSR sin errores y active highlight funciona. |
| R3 | `dasic_sidebar_groups` huérfano molesta a alguien | Cero efecto funcional. Puede limpiarse en una iteración futura si surge. |

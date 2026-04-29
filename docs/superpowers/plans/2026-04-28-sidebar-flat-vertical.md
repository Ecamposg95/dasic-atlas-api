# Sidebar Flat Vertical Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convertir el sidebar de 5 grupos colapsables a una lista plana vertical con los 9 módulos directos como anchors.

**Architecture:** Edición localizada a `app/templates/base.html`: 4 sub-cambios atómicos (eliminar plugin `@alpinejs/collapse`, limpiar Alpine state de grupos, borrar CSS `.sidebar-group*`, reescribir `<nav>` plano). Un solo commit. Sin nuevos archivos. Smoke test verifica que el active highlight y los atajos siguen funcionando.

**Tech Stack:** Jinja2 SSR · Tailwind CSS CDN · Alpine.js 3 · Cookie auth.

**Spec:** `docs/superpowers/specs/2026-04-28-sidebar-flat-vertical.md`

---

## File map

**Modify:**
- `app/templates/base.html` — única edición. 4 secciones tocadas:
  - Bloque de scripts CDN (~líneas 31-33): quitar el plugin collapse.
  - Bloque CSS sidebar (`<style>`, ~líneas 92-110): quitar reglas `.sidebar-group*`.
  - `<body x-data>` (~líneas 152-167): quitar `groups`, `isGroupOpen`, `toggleGroup`.
  - `<nav>` interior del `<aside>` (~líneas 232-329): reemplazar por 9 `<a>` planos.

**Out of touch:**
- Otros templates (heredan `base.html`).
- Routers, modelos, JS estático.
- Header, footer card, brand header del sidebar — todos sin cambios.
- Modal Quick Search — sin cambios.

---

## Sequencing

```
Task 1: Aplicar 4 ediciones en base.html  (un commit)
        ↓
Task 2: Smoke test                         (verification only)
```

---

## Task 1: Convertir sidebar a lista plana

**Files:**
- Modify: `app/templates/base.html` (4 ediciones)

- [ ] **Step 1: Eliminar el plugin `@alpinejs/collapse`**

Localiza en `app/templates/base.html` (alrededor de las líneas 31-33):
```html
    <!-- Alpine.js + collapse plugin (deferred; plugin must load BEFORE core) -->
    <script defer src="https://cdn.jsdelivr.net/npm/@alpinejs/collapse@3.x.x/dist/cdn.min.js"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

Reemplaza por:
```html
    <!-- Alpine.js (deferred) -->
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

- [ ] **Step 2: Eliminar el CSS de grupos del bloque `<style>`**

Localiza dentro de `<style>` (alrededor de las líneas 92-110):
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

Bórralo entero (incluye las líneas en blanco si quedan). El bloque `.sidebar-shell { ... }` debe seguirlo directamente la regla `.sidebar-item { ... }`.

- [ ] **Step 3: Limpiar el `x-data` del `<body>`**

Localiza el bloque actual (alrededor de las líneas 152-167):
```html
<body class="h-full bg-slate-900 text-slate-200 font-sans antialiased"
      x-data="{
        searchOpen: false,
        sidebarMobile: false,
        mode: (function(){ const s = localStorage.getItem('dasic_sidebar_mode'); return s === 'collapsed' ? 'expanded' : (s || 'expanded'); })(),
        groups: JSON.parse(localStorage.getItem('dasic_sidebar_groups') || 'null'),
        setMode(m) { this.mode = m; localStorage.setItem('dasic_sidebar_mode', m); document.body.dataset.sidebar = m; },
        hide() { this.setMode('hidden'); },
        show() { this.setMode('expanded'); },
        isGroupOpen(key) { if (this.groups && key in this.groups) return this.groups[key]; return true; },
        toggleGroup(key) { const next = Object.assign({}, this.groups || {}); next[key] = !this.isGroupOpen(key); this.groups = next; localStorage.setItem('dasic_sidebar_groups', JSON.stringify(next)); }
      }"
      x-init="document.body.dataset.sidebar = mode"
      :data-sidebar="mode"
      @keydown.meta.k.window.prevent="searchOpen = true"
      @keydown.ctrl.k.window.prevent="searchOpen = true"
      @keydown.window="if ($event.key === '\\' && ($event.metaKey || $event.ctrlKey)) { $event.preventDefault(); mode === 'hidden' ? show() : hide(); }">
```

Reemplaza por (sin `groups`, `isGroupOpen`, `toggleGroup`):
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

- [ ] **Step 4: Reemplazar el `<nav>` interior del `<aside>` por lista plana**

Localiza el bloque actual del `<nav>` (alrededor de las líneas 232-329):
```html
    <!-- Nav -->
    <nav class="flex-1 min-h-0 overflow-y-auto px-3 mt-2">

      <!-- RESUMEN -->
      <div class="sidebar-group">
        <button class="sidebar-group-header" @click="toggleGroup('resumen')">
          <span>Resumen</span>
          <i class="fas fa-chevron-down sidebar-group-chevron"
             :class="isGroupOpen('resumen') ? 'rotate-0' : '-rotate-90'"></i>
        </button>
        <div x-show="isGroupOpen('resumen')" x-collapse class="sidebar-group-items">
          <a href="/dashboard" class="sidebar-item {% if _path == '/dashboard' %}is-active{% endif %}">
            <span class="sidebar-item-icon"><i class="fas fa-chart-line text-[12px]"></i></span>
            <span>Dashboard</span>
          </a>
        </div>
      </div>

      <!-- CRM -->
      <div class="sidebar-group">
        <button class="sidebar-group-header" @click="toggleGroup('crm')">
          <span>CRM</span>
          <i class="fas fa-chevron-down sidebar-group-chevron"
             :class="isGroupOpen('crm') ? 'rotate-0' : '-rotate-90'"></i>
        </button>
        <div x-show="isGroupOpen('crm')" x-collapse class="sidebar-group-items">
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
        </div>
      </div>

      <!-- OPERACIÓN -->
      <div class="sidebar-group">
        <button class="sidebar-group-header" @click="toggleGroup('operacion')">
          <span>Operación</span>
          <i class="fas fa-chevron-down sidebar-group-chevron"
             :class="isGroupOpen('operacion') ? 'rotate-0' : '-rotate-90'"></i>
        </button>
        <div x-show="isGroupOpen('operacion')" x-collapse class="sidebar-group-items">
          <a href="/inventario" class="sidebar-item {% if _path == '/inventario' %}is-active{% endif %}">
            <span class="sidebar-item-icon"><i class="fas fa-boxes-stacked text-[12px]"></i></span>
            <span>Inventario</span>
          </a>
          <a href="/compras" class="sidebar-item {% if _path == '/compras' %}is-active{% endif %}">
            <span class="sidebar-item-icon"><i class="fas fa-truck text-[12px]"></i></span>
            <span>Compras</span>
          </a>
        </div>
      </div>

      <!-- REPORTES -->
      <div class="sidebar-group">
        <button class="sidebar-group-header" @click="toggleGroup('reportes')">
          <span>Reportes</span>
          <i class="fas fa-chevron-down sidebar-group-chevron"
             :class="isGroupOpen('reportes') ? 'rotate-0' : '-rotate-90'"></i>
        </button>
        <div x-show="isGroupOpen('reportes')" x-collapse class="sidebar-group-items">
          <a href="/reportes" class="sidebar-item {% if _path == '/reportes' %}is-active{% endif %}">
            <span class="sidebar-item-icon"><i class="fas fa-chart-pie text-[12px]"></i></span>
            <span>Reportes</span>
          </a>
          <a href="/gastos" class="sidebar-item {% if _path == '/gastos' %}is-active{% endif %}">
            <span class="sidebar-item-icon"><i class="fas fa-file-invoice-dollar text-[12px]"></i></span>
            <span>Gastos</span>
          </a>
        </div>
      </div>

      <!-- SISTEMA -->
      <div class="sidebar-group">
        <button class="sidebar-group-header" @click="toggleGroup('sistema')">
          <span>Sistema</span>
          <i class="fas fa-chevron-down sidebar-group-chevron"
             :class="isGroupOpen('sistema') ? 'rotate-0' : '-rotate-90'"></i>
        </button>
        <div x-show="isGroupOpen('sistema')" x-collapse class="sidebar-group-items">
          <a href="/usuarios" class="sidebar-item {% if _path == '/usuarios' %}is-active{% endif %}">
            <span class="sidebar-item-icon"><i class="fas fa-user-shield text-[12px]"></i></span>
            <span>Usuarios</span>
          </a>
        </div>
      </div>

    </nav>
```

Reemplaza ENTERAMENTE por:
```html
    <!-- Nav -->
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

Cambios clave: `mt-2`→`py-3 space-y-1`, los 5 `<div class="sidebar-group">` desaparecen, los headers de grupo y los `x-collapse` desaparecen, el orden lineal es Dashboard → Clientes → Cotizador → Seguimiento → Inventario → Compras → Reportes → Gastos → Usuarios.

- [ ] **Step 5: Verify**

```bash
cd /home/atlas-tech/Devs/Dasic_Atlas_api-flat

# 1. Plugin collapse fuera
grep -c 'alpinejs/collapse' app/templates/base.html
```

Expected: `0`.

```bash
# 2. State y métodos de grupos fuera
grep -nE 'isGroupOpen|toggleGroup|sidebar-group-header|sidebar-group-chevron|sidebar-group-items|x-collapse|dasic_sidebar_groups' app/templates/base.html
```

Expected: cero hits.

```bash
# 3. Los 9 anchors directos están
grep -cE 'href="/(dashboard|clientes|ventas/cotizador|seguimiento|inventario|compras|reportes|gastos|usuarios)"' app/templates/base.html
```

Expected: `9`.

```bash
# 4. Atajos preservados
grep -nE 'searchOpen|hide\\(\\)|show\\(\\)' app/templates/base.html | head -10
```

Expected: múltiples hits (modal trigger, hide/show).

```bash
# 5. Jinja parse
DATABASE_URL='postgresql+psycopg://x:x@localhost:5432/dummy' SECRET_KEY='dummy' \
  uv run --with-requirements requirements.txt python -c "
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('app/templates'))
tmpl = env.get_template('base.html')
print('Jinja parse OK')
"
```

Expected: `Jinja parse OK`.

- [ ] **Step 6: Commit**

```bash
git add app/templates/base.html
git commit -m "refactor(ui): sidebar lista plana — drop grupos colapsables, 9 anchors directos"
```

---

## Task 2: Smoke test

**Files:**
- Read-only verification (server runtime).

- [ ] **Step 1: Crear DB de smoke**

```bash
psql "postgresql://postgres:toor@localhost:5432/postgres" -c "CREATE DATABASE dasic_flat_smoke;"
```

- [ ] **Step 2: Arrancar uvicorn**

```bash
cd /home/atlas-tech/Devs/Dasic_Atlas_api-flat
DATABASE_URL='postgresql+psycopg://postgres:toor@localhost:5432/dasic_flat_smoke' \
  SECRET_KEY='smoke-flat' \
  uv run --with-requirements requirements.txt uvicorn app.main:app --port 8004 \
  > /tmp/uvicorn-flat.log 2>&1 &
sleep 6
```

- [ ] **Step 3: Health + login**

```bash
curl -s http://127.0.0.1:8004/health
curl -s -c /tmp/cookies-flat.txt -X POST http://127.0.0.1:8004/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@dasic.com&password=admin123"
```

Expected: health `{"status":"ok",...}`, login devuelve `access_token`.

- [ ] **Step 4: 9 rutas SSR siguen 200 y traen los 9 anchors directos**

```bash
for path in /dashboard /clientes /ventas/cotizador /seguimiento /inventario /compras /gastos /reportes /usuarios; do
  code=$(curl -s -o /tmp/last.html -w "%{http_code}" -b /tmp/cookies-flat.txt "http://127.0.0.1:8004${path}")
  size=$(wc -c < /tmp/last.html)
  anchors=$(grep -cE 'href="/(dashboard|clientes|ventas/cotizador|seguimiento|inventario|compras|reportes|gastos|usuarios)" class="sidebar-item' /tmp/last.html)
  echo "${path} → ${code} (${size}B) anchors=${anchors}"
done
```

Expected: cada línea `200`, size > 5000B, `anchors=9`.

- [ ] **Step 5: Active item highlight funciona en cada vista**

```bash
for pair in "/dashboard:dashboard" "/clientes:clientes" "/ventas/cotizador:cotizador" "/inventario:inventario" "/usuarios:usuarios"; do
  path="${pair%:*}"
  needle="${pair#*:}"
  curl -s -b /tmp/cookies-flat.txt "http://127.0.0.1:8004${path}" > /tmp/page.html
  match=$(grep -cE "href=\"[^\"]*${needle}[^\"]*\" class=\"sidebar-item is-active\"" /tmp/page.html)
  echo "${path} → active match=${match}"
done
```

Expected: cada `match=1`.

- [ ] **Step 6: Plugin collapse no se carga**

```bash
curl -s -b /tmp/cookies-flat.txt http://127.0.0.1:8004/dashboard | grep -c 'alpinejs/collapse'
```

Expected: `0`.

- [ ] **Step 7: Modal Quick Search aún operable**

```bash
curl -s -b /tmp/cookies-flat.txt http://127.0.0.1:8004/dashboard | grep -cE '@click="searchOpen = true"'
```

Expected: `2` (botón desktop + botón móvil del header).

- [ ] **Step 8: Sidebar sin headers de grupo ni `x-collapse` ni `toggleGroup`**

```bash
curl -s -b /tmp/cookies-flat.txt http://127.0.0.1:8004/dashboard > /tmp/page.html
grep -cE 'sidebar-group-header|x-collapse|toggleGroup|isGroupOpen' /tmp/page.html
```

Expected: `0`.

- [ ] **Step 9: Stop uvicorn + cleanup**

```bash
pkill -f 'uvicorn app.main:app' || true
sleep 1
psql "postgresql://postgres:toor@localhost:5432/postgres" -c "DROP DATABASE IF EXISTS dasic_flat_smoke;"
```

---

## Definition of Done

- [ ] `grep -E 'isGroupOpen|toggleGroup|sidebar-group|x-collapse|alpinejs/collapse|dasic_sidebar_groups' app/templates/base.html` → cero resultados.
- [ ] `grep -cE 'class="sidebar-item' app/templates/base.html` → `9`.
- [ ] Las 9 rutas SSR responden 200 con HTML válido.
- [ ] Cada ruta resalta su propio item con `is-active` (smoke verifica 5 muestras).
- [ ] `Cmd/Ctrl+K` sigue abriendo Quick Search.
- [ ] `Cmd/Ctrl+\` sigue toggleando hide/show del sidebar.

# Sidebar Tactical Restyle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mover Quick Search/Inbox/Notifications del sidebar al header. Restilizar el sidebar a un look tactical industrial (Linear/Nostromo-vibe): hairlines, micro-labels, navy profundo, footer card industrial.

**Architecture:** Una sola fase de 3 ediciones en `app/templates/base.html`: (1) CSS tokens y classes del sidebar, (2) markup del `<aside>` (header marca con status dot, remover quick-rows, footer card tactical), (3) markup del `<header>` con search inline + inbox/notifications. Cada edición = un commit. Sin nuevos archivos, sin nuevos JS, sin tocar otras templates.

**Tech Stack:** Jinja2 SSR · Tailwind CSS CDN · Alpine.js 3 + collapse plugin · Cookie auth.

**Spec:** `docs/superpowers/specs/2026-04-28-sidebar-tactical-restyle.md`

---

## File map

**Modify:**
- `app/templates/base.html` — única edición. Tres secciones tocadas:
  - Bloque `<style>` (líneas ~36-142): tokens + clases sidebar.
  - Bloque `<aside>` (líneas ~188-367): header marca, eliminar quick-rows, footer card.
  - Bloque `<header>` (líneas ~375-407): page title micro-label + search bar inline + inbox/notifications + clock retocado.

**Out of touch:**
- Otros templates (heredan automáticamente).
- Routers, modelos, JS estático.
- El modal Quick Search (líneas ~420-438) — sigue idéntico, solo cambian sus triggers.

---

## Sequencing

```
Task 1: CSS tokens + sidebar classes        (commit 1)
        ↓
Task 2: Sidebar markup (aside)               (commit 2)
        ↓
Task 3: Header markup                        (commit 3)
        ↓
Task 4: Smoke test                           (verification only)
```

Cada commit deja la app funcional. Si paras después de Task 1 los items se ven sin la mejora visual completa, pero no hay regresión.

---

## Task 1: Update CSS tokens + sidebar classes

**Files:**
- Modify: `app/templates/base.html` (bloque `<style>`, líneas ~36-142)

- [ ] **Step 1: Reemplazar el bloque `:root` (líneas ~36-47)**

Localiza el `:root { --sidebar-width: 256px; ... }` actual y sustitúyelo por:

```css
      :root {
        --sidebar-width: 268px;
        --sidebar-bg: #0a1429;
        --sidebar-bg-bottom: #050a1a;
        --sidebar-text: #cbd5e1;
        --sidebar-text-dim: #64748b;
        --sidebar-rule: rgba(255,255,255,0.06);
        --sidebar-rule-strong: rgba(255,255,255,0.10);
        --sidebar-active-bg: rgba(0, 212, 224, 0.08);
        --sidebar-hover-bg: rgba(255, 255, 255, 0.04);
        --sidebar-accent-glow: #00d4e0;
        --sidebar-accent-deep: #2563eb;
        --header-h:  64px;
        --footer-h:  36px;
      }
```

Notas: ancho 256→268, navy más profundo, nuevos `--sidebar-text-dim`, `--sidebar-rule`, `--sidebar-rule-strong`. Se elimina `--sidebar-text: #ffffff` (lo reemplaza `#cbd5e1`).

- [ ] **Step 2: Reemplazar el bloque scrollbar (líneas ~49-52)**

Localiza el bloque actual:
```css
      ::-webkit-scrollbar { width: 5px; height: 5px; }
      ::-webkit-scrollbar-track { background: #0f172a; }
      ::-webkit-scrollbar-thumb { background: #334155; border-radius: 99px; }
      ::-webkit-scrollbar-thumb:hover { background: #475569; }
```

Reemplaza por:
```css
      ::-webkit-scrollbar { width: 4px; height: 4px; }
      ::-webkit-scrollbar-track { background: transparent; }
      ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 99px; }
      ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.16); }
```

- [ ] **Step 3: Reemplazar TODO el bloque sidebar CSS (líneas ~86-142)**

Localiza el comentario `/* ── SIDEBAR ─────...` (línea ~86) y todas las clases hasta el final del media query del `.main-shell` (línea ~142). Reemplaza por:

```css
      /* ── SIDEBAR ─────────────────────────────────────────── */
      .sidebar-shell {
        background: linear-gradient(180deg, var(--sidebar-bg) 0%, var(--sidebar-bg-bottom) 100%);
        transition: transform 0.25s ease;
        font-feature-settings: "tnum", "ss01";
      }

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

      .sidebar-item {
        @apply relative flex items-center gap-3 rounded-lg px-3 py-2.5
               text-[13.5px] font-medium text-slate-300 transition-all duration-150 hover:text-white;
      }
      .sidebar-item:hover { background: var(--sidebar-hover-bg); }
      .sidebar-item.is-active {
        background: var(--sidebar-active-bg);
        color: #ffffff;
        font-weight: 600;
      }
      .sidebar-item.is-active::before {
        content: ""; position: absolute; left: -6px; top: 6px; bottom: 6px;
        width: 4px; border-radius: 9999px;
        background: linear-gradient(180deg, var(--sidebar-accent-glow), #22d3ee);
        box-shadow: 0 0 12px rgba(0, 212, 224, 0.4);
      }
      .sidebar-item-icon {
        @apply flex h-8 w-8 shrink-0 items-center justify-center rounded-md
               text-slate-400 transition-colors duration-150;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.04);
      }
      .sidebar-item:hover .sidebar-item-icon {
        color: #ffffff;
        background: rgba(255,255,255,0.06);
      }
      .sidebar-item.is-active .sidebar-item-icon {
        color: var(--sidebar-accent-glow);
        background: rgba(0, 212, 224, 0.10);
        border-color: rgba(0, 212, 224, 0.30);
        box-shadow: inset 0 0 0 1px rgba(0, 212, 224, 0.25);
      }

      /* Layout principal */
      .main-shell { margin-left: 0; transition: margin-left 0.22s ease; }
      @media (min-width: 1024px) {
        body[data-sidebar="expanded"] .main-shell { margin-left: var(--sidebar-width); }
        body[data-sidebar="hidden"]   .main-shell { margin-left: 0; }
      }
```

> **Important:** `.quick-row`, `.quick-icon`, `.quick-badge` quedan ELIMINADAS (ya no aplican — Task 2 borra el HTML que las usa).

- [ ] **Step 4: Verificar**

```bash
cd /home/atlas-tech/Devs/Dasic_Atlas_api-tactical
grep -nE "quick-row|quick-icon|quick-badge|--sidebar-rule|--sidebar-text-dim|font-feature-settings" app/templates/base.html
```

Expected:
- `quick-row|quick-icon|quick-badge`: zero (clases CSS borradas — quedan referencias en HTML que Task 2 quitará).
- `--sidebar-rule`, `--sidebar-text-dim`, `font-feature-settings`: present (nuevos tokens).

> Es OK que el grep encuentre `quick-row`/`quick-icon`/`quick-badge` en el HTML del `<aside>` — esas referencias se limpian en Task 2.

```bash
DATABASE_URL='postgresql+psycopg://x:x@localhost:5432/dummy' SECRET_KEY='dummy' \
  uv run --with-requirements requirements.txt python -c "
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('app/templates'))
tmpl = env.get_template('base.html')
print('Jinja parse OK')
"
```

Expected: `Jinja parse OK`.

- [ ] **Step 5: Commit**

```bash
git add app/templates/base.html
git commit -m "refactor(ui): tokens y classes sidebar para look tactical (hairlines + navy profundo)"
```

---

## Task 2: Restyle sidebar markup (`<aside>` block)

**Files:**
- Modify: `app/templates/base.html` (bloque `<aside>`, líneas ~196-367)

Tres ediciones distintas dentro del `<aside>`:

- [ ] **Step 1: Header marca con status dot operativo**

Localiza el bloque actual:
```html
    <!-- Header marca -->
    <div class="flex h-16 shrink-0 items-center justify-between px-4 border-b border-white/10">
      <div class="flex items-center gap-3">
        <div class="flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-400/10 ring-1 ring-cyan-400/30">
          <i class="fas fa-layer-group text-cyan-400 text-base"></i>
        </div>
        <div>
          <p class="text-[15px] font-bold tracking-wide text-white leading-none">DASIC</p>
          <p class="text-[9px] text-cyan-300/80 uppercase tracking-[0.18em] font-semibold mt-1">Industrial ERP</p>
        </div>
      </div>
      <button @click="sidebarMobile = false"
              class="lg:hidden h-8 w-8 flex items-center justify-center rounded-lg
                     text-slate-400 hover:text-white hover:bg-white/5 transition"
              title="Cerrar">
        <i class="fas fa-xmark text-sm"></i>
      </button>
    </div>
```

Reemplaza por:
```html
    <!-- Header marca -->
    <div class="flex h-16 shrink-0 items-center justify-between px-4 border-b" style="border-color: var(--sidebar-rule)">
      <div class="flex items-center gap-3">
        <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-400/10 ring-1 ring-cyan-400/30">
          <i class="fas fa-layer-group text-cyan-400 text-base"></i>
        </div>
        <div>
          <div class="flex items-center gap-2">
            <p class="text-[14px] font-bold tracking-[0.06em] text-white leading-none">DASIC</p>
            <span class="relative flex h-1.5 w-1.5" title="Operational">
              <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
              <span class="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
            </span>
          </div>
          <p class="text-[8.5px] text-cyan-300/70 uppercase tracking-[0.28em] font-bold mt-1">Industrial · OPS</p>
        </div>
      </div>
      <button @click="sidebarMobile = false"
              class="lg:hidden h-8 w-8 flex items-center justify-center rounded-lg
                     text-slate-400 hover:text-white hover:bg-white/5 transition"
              title="Cerrar">
        <i class="fas fa-xmark text-sm"></i>
      </button>
    </div>
```

Cambios: `rounded-xl`→`rounded-lg` en el logo box; tipografía DASIC más tactical; status dot pulsante verde; subtítulo "Industrial · OPS".

- [ ] **Step 2: Eliminar el bloque Quick Search / Inbox / Notifications**

Localiza el bloque actual (líneas ~215-232):
```html
    <!-- Quick Search + badges -->
    <div class="px-3 pt-3 space-y-1 shrink-0">
      <div class="quick-row" @click="searchOpen = true">
        <span class="quick-icon"><i class="fas fa-magnifying-glass text-[12px]"></i></span>
        <span>Quick search</span>
        <span class="ml-auto text-[10px] font-mono text-slate-400/70 px-1.5 py-0.5 rounded bg-white/5">⌘K</span>
      </div>
      <div class="quick-row">
        <span class="quick-icon"><i class="fas fa-inbox text-[12px]"></i></span>
        <span>Inbox</span>
        <span class="quick-badge">0</span>
      </div>
      <div class="quick-row">
        <span class="quick-icon"><i class="fas fa-bell text-[12px]"></i></span>
        <span>Notifications</span>
        <span class="quick-badge">0</span>
      </div>
    </div>
```

Bórralo entero (incluyendo el comentario y el `<div>` envolvente). Quita la línea en blanco que pueda quedar entre el header marca y la `<nav>`.

- [ ] **Step 3: Reemplazar el footer del usuario por tactical card**

Localiza el bloque actual (líneas ~330-365):
```html
    <!-- Footer usuario -->
    <div class="shrink-0 border-t border-white/10 px-3 py-3">
      <div class="rounded-xl border border-white/8 bg-white/5 p-2.5 flex items-center gap-2.5">
        <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full
                    bg-gradient-to-br from-cyan-500 to-blue-600 text-white font-bold text-xs
                    ring-2 ring-white/10">
          {{ (current_user.nombre[0] | upper) if current_user else "U" }}
        </div>
        <div class="min-w-0 flex-1">
          <p class="truncate text-[12.5px] font-semibold text-white leading-tight">
            {{ current_user.nombre if current_user else "Usuario" }}
          </p>
          <span class="flex items-center gap-1.5 text-[10px] text-slate-400 mt-0.5">
            <span class="relative flex h-1.5 w-1.5">
              <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
              <span class="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
            </span>
            En línea
          </span>
        </div>
        <button @click="hide()"
                class="hidden lg:flex h-7 w-7 items-center justify-center rounded-md
                       text-slate-400 hover:text-slate-100 hover:bg-white/5 transition"
                title="Ocultar sidebar (Ctrl+\)">
          <i class="fas fa-eye-slash text-xs"></i>
        </button>
        <form action="/api/auth/logout" method="post" class="shrink-0">
          <button type="submit"
                  class="flex h-7 w-7 items-center justify-center rounded-md
                         text-slate-400 hover:text-red-400 hover:bg-red-500/10
                         transition-all duration-200" title="Cerrar sesión">
            <i class="fas fa-arrow-right-from-bracket text-xs"></i>
          </button>
        </form>
      </div>
    </div>
```

Reemplaza por:
```html
    <!-- Footer usuario -->
    <div class="shrink-0 border-t px-3 py-3" style="border-color: var(--sidebar-rule)">
      <div class="rounded-lg p-3 flex items-start gap-3"
           style="background: rgba(255,255,255,0.025); border: 1px solid rgba(255,255,255,0.05)">
        <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-md
                    bg-gradient-to-br from-cyan-500 to-blue-600 text-white
                    font-bold text-[13px] tracking-tight">
          {{ (current_user.nombre[0] | upper) if current_user else "U" }}
        </div>
        <div class="min-w-0 flex-1">
          <p class="truncate text-[11.5px] font-bold uppercase tracking-[0.08em] text-white leading-tight">
            {{ current_user.nombre if current_user else "Usuario" }}
          </p>
          <p class="text-[9px] uppercase tracking-[0.18em] text-slate-500 mt-0.5 truncate">
            {% if current_user and current_user.rol %}{{ current_user.rol.value }}{% else %}—{% endif %}
          </p>
          <div class="flex items-center gap-1.5 mt-1.5">
            <span class="h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
            <span class="text-[9px] uppercase tracking-[0.2em] text-emerald-400 font-bold">Online</span>
            <span class="text-[9px] text-slate-600 ml-auto font-mono">v2.0</span>
          </div>
        </div>
        <div class="flex flex-col gap-1 shrink-0">
          <button @click="hide()"
                  class="hidden lg:flex h-6 w-6 items-center justify-center rounded
                         text-slate-500 hover:text-slate-200 hover:bg-white/5 transition"
                  title="Ocultar sidebar (Ctrl+\)">
            <i class="fas fa-eye-slash text-[10px]"></i>
          </button>
          <form action="/api/auth/logout" method="post">
            <button type="submit"
                    class="flex h-6 w-6 items-center justify-center rounded
                           text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition"
                    title="Cerrar sesión">
              <i class="fas fa-arrow-right-from-bracket text-[10px]"></i>
            </button>
          </form>
        </div>
      </div>
    </div>
```

Cambios: avatar rectangular tipo "tactical badge"; nombre uppercase tracking-wide; rol como micro-label debajo; status "ONLINE" + version pin "v2.0" en línea inferior; botones hide+logout en stack vertical a la derecha.

- [ ] **Step 4: Verificar**

```bash
cd /home/atlas-tech/Devs/Dasic_Atlas_api-tactical
grep -nE "quick-row|quick-icon|quick-badge|En línea" app/templates/base.html
```

Expected: zero hits (todas las referencias HTML al patrón viejo se fueron).

```bash
grep -nE "Industrial · OPS|tracking-\[0\.28em\]|v2\.0" app/templates/base.html
```

Expected: hits que confirman las nuevas adiciones.

```bash
DATABASE_URL='postgresql+psycopg://x:x@localhost:5432/dummy' SECRET_KEY='dummy' \
  uv run --with-requirements requirements.txt python -c "
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('app/templates'))
tmpl = env.get_template('base.html')
print('Jinja parse OK')
"
```

- [ ] **Step 5: Commit**

```bash
git add app/templates/base.html
git commit -m "refactor(ui): sidebar tactical — header con status dot, footer industrial card, drop quick rows"
```

---

## Task 3: Restyle header markup (insert search + utilities)

**Files:**
- Modify: `app/templates/base.html` (bloque `<header>`, líneas ~375-407)

- [ ] **Step 1: Reemplazar TODO el `<header>` por la versión nueva**

Localiza el bloque actual (líneas ~375-407):
```html
    <!-- HEADER -->
    <header class="sticky top-0 z-30 flex h-16 shrink-0 items-center justify-between
                   border-b border-slate-700/60 bg-slate-900/80 backdrop-blur-md px-4 sm:px-8 gap-3">

      <button @click="sidebarMobile = !sidebarMobile"
              class="lg:hidden h-9 w-9 flex items-center justify-center rounded-lg
                     text-slate-400 hover:text-slate-100 hover:bg-slate-700/60 transition"
              aria-label="Abrir menú">
        <i class="fas fa-bars text-base"></i>
      </button>

      <!-- Toggle desktop: muestra sidebar si está oculto -->
      <button @click="show()"
              x-show="mode === 'hidden'"
              x-cloak
              class="hidden lg:flex h-9 w-9 items-center justify-center rounded-lg
                     text-slate-400 hover:text-slate-100 hover:bg-slate-700/60 transition"
              title="Mostrar sidebar">
        <i class="fas fa-bars-staggered text-base"></i>
      </button>

      <h1 class="text-lg font-bold text-slate-100 tracking-tight truncate flex-1">
        {% block page_title %}Panel{% endblock %}
      </h1>

      <div class="flex items-center gap-3">
        {% block header_actions %}{% endblock %}

        <span class="hidden md:block text-xs font-mono text-slate-500"
              x-data="{ t: '' }"
              x-init="setInterval(()=>{ t=new Date().toLocaleTimeString('es-MX') }, 1000); t=new Date().toLocaleTimeString('es-MX')"
              x-text="t"></span>
      </div>
    </header>
```

Reemplaza por:
```html
    <!-- HEADER -->
    <header class="sticky top-0 z-30 flex h-16 shrink-0 items-center
                   border-b border-slate-700/60 bg-slate-900/80 backdrop-blur-md
                   px-4 sm:px-6 gap-3">

      <button @click="sidebarMobile = !sidebarMobile"
              class="lg:hidden h-9 w-9 flex items-center justify-center rounded-lg
                     text-slate-400 hover:text-slate-100 hover:bg-slate-700/60 transition"
              aria-label="Abrir menú">
        <i class="fas fa-bars text-base"></i>
      </button>

      <!-- Toggle desktop: muestra sidebar si está oculto -->
      <button @click="show()"
              x-show="mode === 'hidden'"
              x-cloak
              class="hidden lg:flex h-9 w-9 items-center justify-center rounded-lg
                     text-slate-400 hover:text-slate-100 hover:bg-slate-700/60 transition"
              title="Mostrar sidebar">
        <i class="fas fa-bars-staggered text-base"></i>
      </button>

      <h1 class="text-[13px] font-semibold uppercase tracking-[0.18em] text-slate-300 truncate shrink-0">
        {% block page_title %}Panel{% endblock %}
      </h1>

      <!-- Search bar inline (desktop) -->
      <button @click="searchOpen = true"
              class="hidden md:flex flex-1 max-w-2xl items-center gap-2 h-9 px-3
                     bg-slate-800/60 border border-slate-700/60
                     hover:border-slate-600 hover:bg-slate-800/80
                     rounded-md text-left transition-colors">
        <i class="fas fa-magnifying-glass text-[12px] text-slate-500"></i>
        <span class="text-[12px] text-slate-400 flex-1">Buscar cotización, cliente, producto…</span>
        <span class="text-[10px] font-mono text-slate-500 px-1.5 py-0.5 rounded bg-slate-700/50 border border-slate-600/40">⌘K</span>
      </button>

      <!-- Spacer para móvil cuando search es icono -->
      <div class="md:hidden flex-1"></div>

      <!-- Search icono (mobile) -->
      <button @click="searchOpen = true"
              class="md:hidden h-9 w-9 flex items-center justify-center rounded-md
                     text-slate-400 hover:text-slate-100 hover:bg-slate-700/60 transition"
              title="Buscar (⌘K)">
        <i class="fas fa-magnifying-glass text-base"></i>
      </button>

      <!-- Inbox -->
      <button class="relative h-9 w-9 flex items-center justify-center rounded-md
                     text-slate-400 hover:text-slate-100 hover:bg-slate-700/60 transition"
              title="Inbox">
        <i class="fas fa-inbox text-base"></i>
      </button>

      <!-- Notifications -->
      <button class="relative h-9 w-9 flex items-center justify-center rounded-md
                     text-slate-400 hover:text-slate-100 hover:bg-slate-700/60 transition"
              title="Notifications">
        <i class="fas fa-bell text-base"></i>
      </button>

      {% block header_actions %}{% endblock %}

      <span class="hidden md:block text-[11px] font-mono text-slate-500 tracking-wider shrink-0"
            x-data="{ t: '' }"
            x-init="setInterval(()=>{ t=new Date().toLocaleTimeString('es-MX') }, 1000); t=new Date().toLocaleTimeString('es-MX')"
            x-text="t"></span>
    </header>
```

Cambios:
- `justify-between` removido (el flex layout ahora apila con `gap-3` y `flex-1` en el search).
- `px-4 sm:px-8` → `px-4 sm:px-6` (un poco menos padding horizontal por densidad).
- Page title pasa a micro-label (`text-[13px] font-semibold uppercase tracking-[0.18em]`) y pierde `flex-1`.
- Search bar inline ocupa el `flex-1` (con `max-w-2xl` para no estirarse infinito).
- Search compacto en móvil con icono solo + spacer.
- Inbox + Notifications como botones con icono.
- `header_actions` block se queda (cualquier vista que lo use sigue inyectando ahí).
- Clock retocado a `text-[11px]` con `tracking-wider`.

- [ ] **Step 2: Verificar**

```bash
cd /home/atlas-tech/Devs/Dasic_Atlas_api-tactical
grep -nE 'fa-magnifying-glass|fa-inbox|fa-bell' app/templates/base.html | head
```

Expected: 4+ hits (1 search desktop button, 1 search mobile button, 1 search modal icon, 1 inbox, 1 notifications).

```bash
grep -nE 'tracking-\[0\.18em\]' app/templates/base.html
```

Expected: 1 hit en el page title.

```bash
DATABASE_URL='postgresql+psycopg://x:x@localhost:5432/dummy' SECRET_KEY='dummy' \
  uv run --with-requirements requirements.txt python -c "
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('app/templates'))
tmpl = env.get_template('base.html')
print('Jinja parse OK')
"
```

- [ ] **Step 3: Commit**

```bash
git add app/templates/base.html
git commit -m "refactor(ui): header con search inline + inbox/notifications + micro-label title"
```

---

## Task 4: Smoke test end-to-end

**Files:**
- Read-only verification

- [ ] **Step 1: Crear DB de smoke**

```bash
psql "postgresql://postgres:toor@localhost:5432/postgres" -c "CREATE DATABASE dasic_tactical_smoke;"
```

- [ ] **Step 2: Arrancar uvicorn**

```bash
cd /home/atlas-tech/Devs/Dasic_Atlas_api-tactical
DATABASE_URL='postgresql+psycopg://postgres:toor@localhost:5432/dasic_tactical_smoke' \
  SECRET_KEY='smoke-tactical' \
  uv run --with-requirements requirements.txt uvicorn app.main:app --port 8003 \
  > /tmp/uvicorn-tactical.log 2>&1 &
sleep 6
```

- [ ] **Step 3: Health + login**

```bash
curl -s http://127.0.0.1:8003/health
curl -s -c /tmp/cookies-tactical.txt -X POST http://127.0.0.1:8003/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@dasic.com&password=admin123"
```

Expected: health `{"status":"ok",...}`, login returns access_token.

- [ ] **Step 4: 9 rutas SSR siguen 200**

```bash
for path in /dashboard /clientes /ventas/cotizador /seguimiento /inventario /compras /gastos /reportes /usuarios; do
  code=$(curl -s -o /tmp/last.html -w "%{http_code}" -b /tmp/cookies-tactical.txt "http://127.0.0.1:8003${path}")
  size=$(wc -c < /tmp/last.html)
  echo "${path} → ${code} (${size}B)"
done
```

Expected: cada línea 200 + tamaño > 5000B.

- [ ] **Step 5: Header tiene search inline + utilities**

```bash
curl -s -b /tmp/cookies-tactical.txt http://127.0.0.1:8003/dashboard > /tmp/dash.html
grep -c 'Buscar cotización, cliente, producto' /tmp/dash.html
grep -c 'fa-inbox' /tmp/dash.html
grep -c 'fa-bell' /tmp/dash.html
```

Expected: 1 / 1 / 2 (la 2 del bell incluye Notifications + posible match en algún tooltip; lo importante es ≥1).

- [ ] **Step 6: Sidebar NO tiene quick-rows (clases CSS)**

```bash
grep -cE 'quick-row|quick-icon|quick-badge' /tmp/dash.html
```

Expected: 0 (las clases CSS de las viejas quick rows se fueron del HTML).

> Nota: la cadena "Quick search" puede aparecer en el body del modal Quick Search (texto placeholder "Quick search aún no conectado..."). Eso es OK — solo verificamos que las CLASES CSS están limpias.

- [ ] **Step 7: Status dot operativo + tactical card en sidebar**

```bash
grep -c 'Industrial · OPS\|tracking-\[0\.28em\]\|tactical' /tmp/dash.html
grep -c 'ONLINE\|v2.0' /tmp/dash.html
```

Expected: 1+ y 2+ (subtítulo OPS + version pin + status uppercase en el footer card).

- [ ] **Step 8: Active item highlight sigue funcionando**

```bash
curl -s -b /tmp/cookies-tactical.txt http://127.0.0.1:8003/inventario > /tmp/inv.html
grep -E 'href="/inventario" class="sidebar-item is-active' /tmp/inv.html | head -1
```

Expected: una línea con la clase `is-active` aplicada al item correcto.

- [ ] **Step 9: Modal de búsqueda sigue accionable desde el header**

```bash
grep -E '@click="searchOpen = true"' /tmp/dash.html | head
```

Expected: 2+ matches (botón desktop search + botón mobile search). El sidebar ya no contiene este pattern.

- [ ] **Step 10: Apagar uvicorn + limpiar smoke DB**

```bash
pkill -f 'uvicorn app.main:app' || true
sleep 1
psql "postgresql://postgres:toor@localhost:5432/postgres" -c "DROP DATABASE IF EXISTS dasic_tactical_smoke;"
```

- [ ] **Step 11 (opcional): UX visual check**

Si el smoke automatizado pasa, abre el navegador en `http://127.0.0.1:8003/dashboard` con el server arriba y verifica:
- Header: search bar inline visible en desktop, icono de search en móvil; iconos de inbox/notifications a la derecha.
- Sidebar: status dot pulsante verde junto a "DASIC", subtítulo "Industrial · OPS", grupos con separador hairline arriba (excepto el primero), items con padding más generoso.
- Footer del sidebar: nombre en uppercase tracking-wide, rol debajo, "ONLINE" en verde, "v2.0" mono pin, dos botones (hide + logout) en stack vertical a la derecha.
- ⌘K abre el modal; click en el botón search del header también lo abre.
- El icono active item en una vista actual (ej. `/clientes`) tiene glow más intenso que antes.

---

## Definition of Done

- [ ] `git grep -nE 'quick-row|quick-icon|quick-badge' app/` → cero resultados.
- [ ] El `<aside>` en base.html tiene status dot operativo verde y subtítulo "Industrial · OPS".
- [ ] El footer del sidebar es la tactical card con avatar rectangular, nombre uppercase, rol, ONLINE, v2.0.
- [ ] El `<header>` contiene search bar inline (desktop) + search icono (mobile) + inbox + notifications + clock retocado.
- [ ] Las 9 rutas SSR responden 200 con HTML > 5000B.
- [ ] `searchOpen` se activa desde el header (no desde el sidebar).
- [ ] `Cmd/Ctrl+K` sigue abriendo el modal.
- [ ] `Cmd/Ctrl+\` sigue toggleando hide/show del sidebar.
- [ ] Active item highlight funciona en cada ruta.

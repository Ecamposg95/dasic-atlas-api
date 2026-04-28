# Sidebar Tactical Restyle — Design Spec

**Date:** 2026-04-28
**Owner:** Atlas_Tech
**Scope:** Mover Quick Search / Inbox / Notifications del sidebar al header. Restilizar el sidebar a un look "tactical industrial" (Linear/Nostromo-vibe) con más respiro, hairlines, micro-labels y dígitos refinados.

---

## 1. Decisiones marco

| # | Decisión | Justificación |
|---|---|---|
| 1 | **Mover Quick Search / Inbox / Notifications al header** | El sidebar se ve amontonado; estos elementos son utilities globales más naturales como header bar. El modal `searchOpen` ya existe en `base.html`, solo cambia el trigger. |
| 2 | **Look tactical industrial (opción B)** | Coherente con DASIC = ERP industrial con datos densos. Densidad media, dígitos monospace, micro-labels en mayúsculas, líneas hairline, navy profundo. |
| 3 | **Sin cambios funcionales** | Mismas rutas, misma Alpine state (`searchOpen`, `groups`, `mode`), mismas keybindings. Solo CSS + reubicación HTML + iconos nuevos en header. |
| 4 | **Single-tenant, dark-only** | No introducir toggles de tema ni branding cross-tenant. |

---

## 2. Forma — un solo commit

Edición localizada a `app/templates/base.html`. Sin nuevos archivos, sin nuevos JS, sin tocar otras templates. El cambio es atómico y mergeable solo.

---

## 3. Header — recibir las utilities

### Layout objetivo

```
[☰ mobile] [↗ reopen-desktop]  [Page Title]  [🔍 search bar (flex-1) ⌘K]  [📥 Inbox] [🔔 Notif]  [⏱ clock]
```

### Cambios a `<header>` en `base.html`

1. **Page title:** reducir a micro-label industrial:
   - Antes: `text-lg font-bold text-slate-100 tracking-tight truncate flex-1`
   - Después: `text-[13px] font-semibold uppercase tracking-[0.18em] text-slate-300 truncate shrink-0`
   - Quitar `flex-1` del title (ya no es flexible — el search lo es).

2. **Insertar barra de búsqueda inline** (después del title, antes del bloque actions):

   ```html
   <button @click="searchOpen = true"
           class="hidden md:flex flex-1 max-w-2xl items-center gap-2 h-9 px-3
                  bg-slate-800/60 border border-slate-700/60
                  hover:border-slate-600 hover:bg-slate-800/80
                  rounded-md text-left transition-colors">
     <i class="fas fa-magnifying-glass text-[12px] text-slate-500"></i>
     <span class="text-[12px] text-slate-400 flex-1">Buscar cotización, cliente, producto…</span>
     <span class="text-[10px] font-mono text-slate-500 px-1.5 py-0.5 rounded bg-slate-700/50 border border-slate-600/40">⌘K</span>
   </button>
   ```

   En móvil (`md:hidden`) — ver punto 3.

3. **Botón de búsqueda compacto en móvil** (icono solo):

   ```html
   <button @click="searchOpen = true"
           class="md:hidden h-9 w-9 flex items-center justify-center rounded-md
                  text-slate-400 hover:text-slate-100 hover:bg-slate-700/60 transition"
           title="Buscar (⌘K)">
     <i class="fas fa-magnifying-glass text-base"></i>
   </button>
   ```

4. **Iconos Inbox + Notifications** (dentro del actions block, antes del clock):

   ```html
   <button class="relative h-9 w-9 flex items-center justify-center rounded-md
                  text-slate-400 hover:text-slate-100 hover:bg-slate-700/60 transition"
           title="Inbox">
     <i class="fas fa-inbox text-base"></i>
     <!-- dot oculto hasta que haya count > 0 -->
   </button>
   <button class="relative h-9 w-9 flex items-center justify-center rounded-md
                  text-slate-400 hover:text-slate-100 hover:bg-slate-700/60 transition"
           title="Notifications">
     <i class="fas fa-bell text-base"></i>
   </button>
   ```

5. **Clock** se mantiene al final con `text-[11px] font-mono text-slate-500 tracking-wider hidden md:block`.

### Reordenamiento del `<header>` final

```html
<header class="sticky top-0 z-30 flex h-16 shrink-0 items-center
               border-b border-slate-700/60 bg-slate-900/80 backdrop-blur-md
               px-4 sm:px-6 gap-3">

  <button ...hamburger-mobile...></button>
  <button ...show-sidebar-desktop...></button>

  <h1 class="text-[13px] font-semibold uppercase tracking-[0.18em] text-slate-300 truncate shrink-0">
    {% block page_title %}Panel{% endblock %}
  </h1>

  <!-- Search inline (desktop) -->
  <button @click="searchOpen = true" class="hidden md:flex flex-1 max-w-2xl ...">
    ...
  </button>

  <!-- Spacer para móvil cuando search es icono -->
  <div class="md:hidden flex-1"></div>

  <!-- Search icono (mobile) -->
  <button @click="searchOpen = true" class="md:hidden ...">...</button>

  <!-- Inbox + Notifications -->
  <button title="Inbox">...</button>
  <button title="Notifications">...</button>

  {% block header_actions %}{% endblock %}

  <!-- Clock -->
  <span class="hidden md:block text-[11px] font-mono text-slate-500 tracking-wider"
        x-data="{ t: '' }"
        x-init="setInterval(()=>{ t=new Date().toLocaleTimeString('es-MX') }, 1000); t=new Date().toLocaleTimeString('es-MX')"
        x-text="t"></span>
</header>
```

---

## 4. Sidebar — tactical restyle

### Tokens CSS (reemplazar `:root` actual)

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
  --header-h: 64px;
  --footer-h: 36px;
}
```

### Scrollbar más fina

```css
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.16); }
```

### Sidebar shell

```css
.sidebar-shell {
  background: linear-gradient(180deg, var(--sidebar-bg) 0%, var(--sidebar-bg-bottom) 100%);
  transition: transform 0.25s ease;
  font-feature-settings: "tnum", "ss01";
}
```

### Header marca (sidebar top)

Markup:
```html
<div class="flex h-16 shrink-0 items-center justify-between px-4 border-b" style="border-color: var(--sidebar-rule)">
  <div class="flex items-center gap-3">
    <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-400/10 ring-1 ring-cyan-400/30">
      <i class="fas fa-layer-group text-cyan-400 text-base"></i>
    </div>
    <div>
      <div class="flex items-center gap-2">
        <p class="text-[14px] font-bold tracking-[0.06em] text-white leading-none">DASIC</p>
        <span class="relative flex h-1.5 w-1.5">
          <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
          <span class="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
        </span>
      </div>
      <p class="text-[8.5px] text-cyan-300/70 uppercase tracking-[0.28em] font-bold mt-1">Industrial · OPS</p>
    </div>
  </div>
  <button @click="sidebarMobile = false" class="lg:hidden ..."><i class="fas fa-xmark"></i></button>
</div>
```

(El módulo verde pulsante = "operational status" tactical.)

### Group headers (`.sidebar-group-header`)

```css
.sidebar-group { @apply mt-3; }
.sidebar-group:first-of-type { @apply mt-1; }
.sidebar-group:not(:first-of-type) { border-top: 1px solid var(--sidebar-rule); padding-top: 12px; }

.sidebar-group-header {
  @apply w-full flex items-center justify-between rounded-md px-2.5 py-2
         text-[10px] font-bold uppercase tracking-[0.28em] text-white/45
         hover:text-white/75 hover:bg-white/5 transition-colors;
}
.sidebar-group-chevron { @apply text-[9px] transition-transform duration-200 text-white/30; }
.sidebar-group-items { @apply mt-1 mb-1 space-y-1; }
```

### Items (`.sidebar-item`)

```css
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
```

### Quick rows del sidebar — eliminadas

Ya no existen `.quick-row`, `.quick-icon`, `.quick-badge` en el sidebar. Se borran del CSS.

### Eliminar el bloque HTML

Borrar el bloque `<div class="px-3 pt-3 space-y-1 shrink-0">...</div>` que contiene Quick Search, Inbox, Notifications. Inicia con el Header marca y le sigue directamente la `<nav>`.

### Footer del usuario (tactical card)

Markup nuevo:
```html
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
        {{ current_user.rol.value if current_user and current_user.rol else "—" }}
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
              title="Ocultar (Ctrl+\)">
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

(Avatar más rectangular tipo "tactical badge", info en columna con micro-labels, controles a la derecha en stack vertical, versión visible.)

### Modal Quick Search — sin cambios

Ya está en el body de `base.html` con `searchOpen`. Solo cambian sus triggers (header en lugar de sidebar).

---

## 5. Comportamientos preservados

- `searchOpen` se sigue activando con `Cmd/Ctrl+K`.
- `Cmd/Ctrl+\` sigue toggleando hide/show del sidebar.
- Estado de grupos (`dasic_sidebar_groups`) persiste en localStorage.
- Modo del sidebar (`dasic_sidebar_mode`: expanded/hidden) persiste.
- Atajo de cerrar modal con `Escape` se mantiene.

---

## 6. Out of scope

- Búsqueda funcional (sigue placeholder).
- Inbox / Notifications con datos reales (los iconos quedan como botones inertes con tooltip).
- Animaciones complejas (mantenemos transitions cortas + Alpine collapse).
- Tipografía nueva (Outfit sigue siendo la fuente).
- Toggle de tema.

---

## 7. Riesgos

| # | Riesgo | Mitigación |
|---|---|---|
| R1 | El header con search inline se desborda en md (768-1024px) | El search usa `flex-1 max-w-2xl`. En `<md` se colapsa a icono. Page title con `truncate shrink-0`. |
| R2 | `current_user.rol.value` puede explotar si rol no está mapeado | Usar `if current_user and current_user.rol` guard. Si rol no es enum válido, el template renderiza `—`. |
| R3 | Cambio de tipografía/spacing rompe layouts en otras vistas | Las variables y clases solo aplican al sidebar y header — los blocks `content` no cambian. Smoke test verifica todas las vistas. |
| R4 | Border-top en grupos se ve mal con el primer grupo | CSS usa `:not(:first-of-type)` para excluirlo. Test visual lo confirma. |

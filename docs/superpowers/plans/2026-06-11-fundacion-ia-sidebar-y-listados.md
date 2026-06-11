# Fundación IA/sidebar + estandarización de listados — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganizar el sidebar/IA (B) y estandarizar todos los listados con primitivas compartidas + paleta de estatus única (A), sin fusionar lógica de negocio.

**Architecture:** B reescribe `SECTIONS` del sidebar, agrega una página `KpisPage` con tabs que embebe las dos páginas analíticas existentes, y convierte las rutas viejas en redirects. A crea 4 primitivas en `@/components/ui` + un mapa de tonos en `@/lib`, y las barre por los módulos en olas (arreglar paginación rota → agregar filtros → consistencia visual).

**Tech Stack:** React 18 + TS + Vite + Tailwind (tokens) + TanStack Query v5 + React Router v6.4 (lazy routes). Backend FastAPI + SQLAlchemy. **No hay suite de tests** (CLAUDE.md): validación = `python3 -m py_compile` (backend) + `cd web && npm run build` (front, debe quedar verde; el `tsc -b` corre antes de vite) + QA visual del usuario por ola. `app/static/dist/` se commitea.

**Spec:** `docs/superpowers/specs/2026-06-11-fundacion-ia-sidebar-y-listados-design.md`

**Convenciones:** EstatusOrden en front es lowercase; `toast()` es función; primitivas en `@/components/ui`; `cn` de `@/lib/utils`. Push directo a main dispara Railway (al final de cada ola, coordinado con el usuario).

---

## File Structure

**Nuevos:**
- `web/src/components/ui/pagination.tsx` — `<Pagination>` (Anterior/Siguiente + "Página X de Y").
- `web/src/components/ui/list-toolbar.tsx` — `<ListToolbar>` (búsqueda + filtros + acciones).
- `web/src/components/ui/status-badge.tsx` — `<StatusBadge>`.
- `web/src/components/ui/tabs.tsx` — `<Tabs>` estándar (subrayado).
- `web/src/lib/status-tones.ts` — `StatusTone`, `statusTone()`, `toneClasses()`.
- `web/src/features/analitica/pages/KpisPage.tsx` — host con tabs.

**Modificados (B):** `web/src/components/layout/Sidebar.tsx`, `web/src/router.tsx`.

**Modificados (A, por ola):** las `pages/*Page.tsx` y `hooks/use*.ts` de cada feature listada + sus endpoints backend en `app/routers/`.

---

## WAVE B — Sidebar / IA

### Task B1: Reescribir `SECTIONS` del sidebar

**Files:**
- Modify: `web/src/components/layout/Sidebar.tsx`

- [ ] **Step 1: Reemplazar el arreglo `SECTIONS` y los imports de iconos**

Sustituir el bloque `const SECTIONS: NavSection[] = [ ... ];` (líneas ~14-73) por:

```tsx
const SECTIONS: NavSection[] = [
  {
    title: 'Comercial',
    items: [
      { to: '/spa/dashboard', label: 'Dashboard', Icon: LayoutDashboard },
      { to: '/spa/crm', label: 'CRM Pipeline', Icon: KanbanSquare },
      { to: '/spa/cotizador', label: 'Cotizador', Icon: FileText },
      { to: '/spa/borradores', label: 'Borradores', Icon: FileClock },
      { to: '/spa/seguimiento', label: 'Seguimiento', Icon: ListChecks },
      { to: '/spa/recordatorios', label: 'Recordatorios', Icon: BellRing },
    ],
  },
  {
    title: 'Clientes',
    items: [
      { to: '/spa/clientes', label: 'Empresas', Icon: Users },
      { to: '/spa/contactos', label: 'Contactos', Icon: Contact },
    ],
  },
  {
    title: 'Operación',
    items: [
      { to: '/spa/compras', label: 'Compras', Icon: ShoppingCart },
      { to: '/spa/remisiones', label: 'Remisiones', Icon: Truck },
      { to: '/spa/reportes-servicio-docs', label: 'Reportes de servicio', Icon: ClipboardCheck },
    ],
  },
  {
    title: 'Catálogo',
    items: [
      { to: '/spa/inventario', label: 'Catálogo de productos', Icon: Package },
      { to: '/spa/servicios', label: 'Servicios', Icon: Wrench },
      { to: '/spa/precios', label: 'Precios', Icon: Tags },
      { to: '/spa/fantasmas', label: 'Fantasmas', Icon: Ghost },
      { to: '/spa/catalogos', label: 'Diccionarios', Icon: BookMarked },
    ],
  },
  {
    title: 'Finanzas',
    items: [
      { to: '/spa/cuentas-por-cobrar', label: 'Cuentas por cobrar', Icon: Wallet },
      { to: '/spa/gastos', label: 'Gastos', Icon: Receipt },
      { to: '/spa/fx', label: 'Tipo de cambio', Icon: Coins },
    ],
  },
  {
    title: 'Analítica',
    items: [
      { to: '/spa/analitica', label: 'KPIs', Icon: BarChart3 },
    ],
  },
  {
    title: 'Sistema',
    items: [
      { to: '/spa/usuarios', label: 'Usuarios', Icon: UserCog },
    ],
  },
  {
    title: 'Plataforma',
    items: [
      { to: '/spa/superadmin', label: 'Consola', Icon: ShieldCheck },
    ],
  },
];
```

Los iconos `Activity` (ya no se usa, era de "Analítica de servicios") puede quedar importado sin uso → quitarlo del import para que `tsc` no marque warning si está en `noUnusedLocals`. Verificar el import line 4-8 y borrar `Activity` si quedó huérfano.

- [ ] **Step 2: Validar build**

Run: `cd web && npm run build`
Expected: build verde (sin errores TS). Si `Activity` quedó sin usar y hay `noUnusedLocals`, el build fallará → quitar el import.

- [ ] **Step 3: Commit**

```bash
git add web/src/components/layout/Sidebar.tsx
git commit -m "feat(sidebar): reorg IA — secciones Clientes/Analítica, Fantasmas→Catálogo, Gastos→Finanzas"
```

---

### Task B2: Página `KpisPage` con tabs (embebe las dos analíticas)

**Files:**
- Create: `web/src/features/analitica/pages/KpisPage.tsx`

- [ ] **Step 1: Crear `KpisPage`**

```tsx
import { useSearchParams } from 'react-router-dom';
import { ReportesPage } from '@/features/reportes/pages/ReportesPage';
import { ReportesServicioPage } from '@/features/reportes_servicio/pages/ReportesServicioPage';

const TABS = [
  { key: 'ventas', label: 'Ventas' },
  { key: 'operativo', label: 'Operativo' },
] as const;

export function KpisPage() {
  const [params, setParams] = useSearchParams();
  const active = params.get('tab') === 'operativo' ? 'operativo' : 'ventas';

  return (
    <div className="p-6 max-w-7xl mx-auto w-full space-y-4">
      <div className="flex items-center gap-1 border-b border-border">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setParams({ tab: t.key }, { replace: true })}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition ${
              active === t.key
                ? 'border-accent-glow text-foreground'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>
      {active === 'ventas' ? <ReportesPage /> : <ReportesServicioPage />}
    </div>
  );
}
```

> Nota: las dos páginas embebidas traen su propio `<header>` interno; es aceptable para el MVP. De-duplicar el encabezado (prop `embedded`) es un nit de seguimiento, no de este plan. Verificar que ambas se exportan como named export (`export function ReportesPage` / `export function ReportesServicioPage`); el router ya las importa así.

- [ ] **Step 2: Validar build**

Run: `cd web && npm run build`
Expected: verde.

- [ ] **Step 3: Commit**

```bash
git add web/src/features/analitica/pages/KpisPage.tsx
git commit -m "feat(analitica): KpisPage con tabs Ventas/Operativo (embebe analíticas)"
```

---

### Task B3: Rutas — agregar `/spa/analitica` + redirects de las viejas

**Files:**
- Modify: `web/src/router.tsx`

- [ ] **Step 1: Registrar el lazy de KpisPage**

Tras la línea de `const recordatorios = lazyPage(...)` (línea ~68), agregar:

```tsx
const analitica = lazyPage(() => import('@/features/analitica/pages/KpisPage'), 'KpisPage');
```

- [ ] **Step 2: Reemplazar las rutas standalone de reportes por redirects + agregar analitica**

Dentro de los `children` de `/spa` (líneas ~104-106), reemplazar:

```tsx
      { path: 'reportes', lazy: reportes },
      { path: 'reportes-servicio', lazy: reportesServicio },
```

por:

```tsx
      { path: 'analitica', lazy: analitica },
      { path: 'reportes', element: <Navigate to="/spa/analitica?tab=ventas" replace /> },
      { path: 'reportes-servicio', element: <Navigate to="/spa/analitica?tab=operativo" replace /> },
```

(Dejar `reportes-servicio-docs` intacto — es el documento.)

- [ ] **Step 3: Redirigir también las rutas legacy**

En el bloque de rutas legacy (líneas ~139-140) reemplazar:

```tsx
  legacyRoute('/reportes', reportes),
  legacyRoute('/reportes-servicio', reportesServicio),
```

por:

```tsx
  { path: '/reportes', element: <Layout />, children: [{ index: true, element: <Navigate to="/spa/analitica?tab=ventas" replace /> }] },
  { path: '/reportes-servicio', element: <Layout />, children: [{ index: true, element: <Navigate to="/spa/analitica?tab=operativo" replace /> }] },
```

> Los `const reportes` y `const reportesServicio` siguen existiendo (KpisPage importa las páginas directo, no via lazy), pero ya no se referencian en el router. Si `noUnusedLocals` marca error, eliminarlos. Verificar tras el build.

- [ ] **Step 4: Validar build**

Run: `cd web && npm run build`
Expected: verde. Si falla por `reportes`/`reportesServicio` sin usar, borrar esas dos `const`.

- [ ] **Step 5: Commit + push de la ola B**

```bash
git add web/src/router.tsx web/src/components/layout/Sidebar.tsx app/static/dist
git commit -m "feat(router): /spa/analitica + redirects desde /reportes y /reportes-servicio"
```
Coordinar push de la ola B con el usuario (push directo a main → Railway).

---

## WAVE A0 — Primitivas compartidas

### Task A0.1: `status-tones.ts`

**Files:**
- Create: `web/src/lib/status-tones.ts`

- [ ] **Step 1: Crear el mapa de tonos**

```ts
export type StatusTone = 'success' | 'warning' | 'info' | 'danger' | 'neutral';

const TONE_CLASSES: Record<StatusTone, string> = {
  success: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  warning: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  info: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
  danger: 'bg-rose-500/15 text-rose-400 border-rose-500/30',
  neutral: 'bg-surface-2 text-muted-foreground border-border',
};

export function toneClasses(tone: StatusTone): string {
  return TONE_CLASSES[tone];
}

// Estatus crudo del backend (lowercase) → tono semántico.
const STATUS_TONE: Record<string, StatusTone> = {
  cotizacion: 'info', borrador: 'info', pendiente: 'warning', pagada: 'success', cancelada: 'danger',
  pospuesto: 'warning', completado: 'success',
  activo: 'success', prospecto: 'warning', inactivo: 'danger',
  recibida: 'success', recibida_parcial: 'warning', en_oc: 'info', recibido: 'success',
  promovido: 'success', descartado: 'danger',
  vigente: 'success', vencida: 'danger', por_vencer: 'warning',
};

export function statusTone(status: string | null | undefined): StatusTone {
  if (!status) return 'neutral';
  return STATUS_TONE[status.toLowerCase()] ?? 'neutral';
}
```

- [ ] **Step 2: Commit** — `git add web/src/lib/status-tones.ts && git commit -m "feat(ui): status-tones (paleta semántica única)"`

### Task A0.2: `status-badge.tsx`

**Files:** Create: `web/src/components/ui/status-badge.tsx`

- [ ] **Step 1:**

```tsx
import { cn } from '@/lib/utils';
import { statusTone, toneClasses, type StatusTone } from '@/lib/status-tones';

export function StatusBadge({
  status, tone, label, className,
}: {
  status?: string | null;
  tone?: StatusTone;
  label?: string;
  className?: string;
}) {
  const t = tone ?? statusTone(status);
  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border',
        toneClasses(t),
        className,
      )}
    >
      {label ?? status ?? '—'}
    </span>
  );
}
```

- [ ] **Step 2: Commit** — `git add web/src/components/ui/status-badge.tsx && git commit -m "feat(ui): StatusBadge"`

### Task A0.3: `pagination.tsx`

**Files:** Create: `web/src/components/ui/pagination.tsx`

- [ ] **Step 1:**

```tsx
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export function Pagination({
  page, totalPages, onPageChange, isLoading, className,
}: {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  isLoading?: boolean;
  className?: string;
}) {
  if (totalPages <= 1) return null;
  const hasPrev = page > 1;
  const hasNext = page < totalPages;
  return (
    <div className={cn('flex items-center justify-between text-sm text-muted-foreground', isLoading && 'opacity-50', className)}>
      <Button variant="outline" size="sm" disabled={!hasPrev || isLoading} onClick={() => onPageChange(Math.max(1, page - 1))}>
        <ChevronLeft className="h-4 w-4 mr-1" /> Anterior
      </Button>
      <span>Página {page} de {totalPages}</span>
      <Button variant="outline" size="sm" disabled={!hasNext || isLoading} onClick={() => onPageChange(page + 1)}>
        Siguiente <ChevronRight className="h-4 w-4 ml-1" />
      </Button>
    </div>
  );
}
```

- [ ] **Step 2: Commit** — `git add web/src/components/ui/pagination.tsx && git commit -m "feat(ui): Pagination (extrae patrón de borradores)"`

### Task A0.4: `list-toolbar.tsx`

**Files:** Create: `web/src/components/ui/list-toolbar.tsx`

- [ ] **Step 1:**

```tsx
import * as React from 'react';
import { Search } from 'lucide-react';
import { cn } from '@/lib/utils';

export function ListToolbar({
  search, onSearchChange, searchPlaceholder = 'Buscar…', filters, actions, className,
}: {
  search?: string;
  onSearchChange?: (v: string) => void;
  searchPlaceholder?: string;
  filters?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn('flex flex-wrap items-center gap-2', className)}>
      {onSearchChange && (
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            value={search ?? ''}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder={searchPlaceholder}
            className="w-full pl-8 pr-3 py-1.5 text-sm rounded-md bg-surface-2 border border-border focus:outline-none focus:ring-1 focus:ring-accent-glow"
          />
        </div>
      )}
      {filters}
      {actions && <div className="ml-auto flex items-center gap-2">{actions}</div>}
    </div>
  );
}
```

- [ ] **Step 2: Commit** — `git add web/src/components/ui/list-toolbar.tsx && git commit -m "feat(ui): ListToolbar"`

### Task A0.5: `tabs.tsx` (estilo subrayado estándar)

**Files:** Create: `web/src/components/ui/tabs.tsx`

- [ ] **Step 1:**

```tsx
import { cn } from '@/lib/utils';

export function Tabs<T extends string>({
  tabs, value, onChange, className,
}: {
  tabs: ReadonlyArray<{ key: T; label: string }>;
  value: T;
  onChange: (key: T) => void;
  className?: string;
}) {
  return (
    <div className={cn('flex items-center gap-1 border-b border-border', className)} role="tablist">
      {tabs.map((t) => (
        <button
          key={t.key}
          role="tab"
          aria-selected={value === t.key}
          onClick={() => onChange(t.key)}
          className={cn(
            'px-4 py-2 text-sm font-medium border-b-2 -mb-px transition',
            value === t.key
              ? 'border-accent-glow text-foreground'
              : 'border-transparent text-muted-foreground hover:text-foreground',
          )}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Validar build** — `cd web && npm run build` → verde.
- [ ] **Step 3: Commit + push A0** — `git add web/src/components/ui/tabs.tsx app/static/dist && git commit -m "feat(ui): Tabs estándar (subrayado)"`. Coordinar push de A0.

---

## WAVE A1 — Arreglar paginación rota / faltante

> Patrón general: el endpoint devuelve `{ page, page_size, total, items }`. El hook pasa `page`; la página usa `const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))` y `<Pagination page={page} totalPages={totalPages} onPageChange={setPage} isLoading={isPlaceholderData} />`. Donde el listado no tenga paginación de servidor, como mínimo aplicar `<DataTable maxBodyHeight="calc(100vh - 16rem)">` + `<DataTableHead sticky>` para que la página no crezca.

### Task A1.1: Recordatorios — acotar scroll + botón "+ Nuevo recordatorio"

**Files:**
- Modify: `web/src/features/recordatorios/pages/RecordatoriosPage.tsx`
- Read first: `web/src/features/recordatorios/components/` (buscar el modal `RecordatorioFormModal`)

Contexto: `GET /api/recordatorios/?vista=X` devuelve un array plano (sin paginación server-side, ver `hooks/useRecordatorios.ts`). NO inventar paginación de servidor; acotar altura y agregar creación directa.

- [ ] **Step 1:** En `RecordatoriosPage.tsx`, envolver la tabla con `<DataTable maxBodyHeight="calc(100vh - 16rem)">` y poner `sticky` en `<DataTableHead>` (mismo patrón aplicado a borradores en commit previo).
- [ ] **Step 2:** Agregar estado `const [modalOpen, setModalOpen] = useState(false)` y un botón en el header `<Button onClick={() => setModalOpen(true)}><Plus … /> Nuevo recordatorio</Button>`. Renderizar el modal `RecordatorioFormModal` (el mismo que usa Seguimiento) con `orden_id` opcional (sin orden). Si el modal exige `orden_id`, ajustar su prop a opcional — verificar su firma en `components/`. Al guardar, invalidar `['recordatorios']`.
- [ ] **Step 3: Validar** — `cd web && npm run build` → verde.
- [ ] **Step 4: Commit** — `git commit -am "fix(recordatorios): acota scroll (maxBodyHeight) + botón Nuevo recordatorio"`

### Task A1.2: Gastos — paginación server-side

**Files:**
- Modify backend: `app/routers/gastos.py` (endpoint de listado) — agregar `page`/`page_size` + `total` (patrón de `listar_borradores` en `app/routers/ventas.py:1461`).
- Modify front: `web/src/features/gastos/hooks/use*.ts` (pasar page/page_size) + `pages/GastosPage.tsx` (usar `<Pagination>`).

- [ ] **Step 1 (backend):** En el endpoint de gastos, reemplazar `limit=500` por params `page:int=1, page_size:int=50`, computar `total = query.count()` antes de `.offset().limit()`, y devolver `{ page, page_size, total, items: [...] }`. Validar `python3 -m py_compile app/routers/gastos.py`.
- [ ] **Step 2 (front):** Actualizar el hook para enviar `?page=&page_size=50` y tipar la respuesta `{ total, items }`. En `GastosPage.tsx` agregar `const [page,setPage]=useState(1)` y `<Pagination …>` debajo de la tabla; los filtros existentes (búsqueda/categoría/fechas) deben resetear `page` a 1 al cambiar.
- [ ] **Step 3: Validar** — `cd web && npm run build` → verde.
- [ ] **Step 4: Commit** — `git commit -am "feat(gastos): paginación server-side + total"`

### Task A1.3: Precios — exponer paginación en UI

**Files:**
- Modify: `web/src/features/precios/hooks/use*.ts` + `pages/PreciosPage.tsx`
- Verify backend: el endpoint de precios ya acepta page/page_size; confirmar que devuelve `total` (si no, agregarlo como en A1.2).

- [ ] **Step 1:** Hacer que el hook envíe `page` y deje de cargar `page_size=200` fijo (bajar a 50). Si el backend no devuelve `total`, agregarlo (`query.count()`).
- [ ] **Step 2:** En `PreciosPage.tsx` añadir estado `page` y `<Pagination>`. Mantener la comparativa lateral existente.
- [ ] **Step 3: Validar** — `cd web && npm run build` → verde. `python3 -m py_compile` si se tocó backend.
- [ ] **Step 4: Commit** — `git commit -am "feat(precios): paginación en UI"`

### Task A1.4: Servicios — paginación + búsqueda server-side

**Files:**
- Modify backend: `app/routers/servicios.py` (o donde viva el listado) — agregar `page`/`page_size`/`q` + `total`.
- Modify front: `web/src/features/servicios/hooks/use*.ts` + `pages/ServiciosPage.tsx`.

- [ ] **Step 1 (backend):** Agregar params `page`, `page_size=50`, `q` (filtra por código/nombre/descripción, `ilike`), devolver `{ page, page_size, total, items }`. Validar `python3 -m py_compile`.
- [ ] **Step 2 (front):** Migrar de "carga todo en memoria" a paginación server-side: el hook envía `page` + `q` (debounce 300ms vía estado), la página usa `<ListToolbar onSearchChange=…>` + `<Pagination>`. Quitar el filtrado client-side previo.
- [ ] **Step 3: Validar** — `cd web && npm run build` → verde; `python3 -m py_compile app/routers/servicios.py`.
- [ ] **Step 4: Commit** — `git commit -am "feat(servicios): paginación + búsqueda server-side"`

### Task A1.5: Diccionarios (Marcas) y CxC — acotar altura

**Files:**
- Modify: `web/src/features/catalogos/pages/CatalogosPage.tsx` (tab Marcas) y `web/src/features/cxc/pages/CuentasPorCobrarPage.tsx`.

- [ ] **Step 1:** En ambas tablas largas (Marcas; tabla de vencimientos de CxC) aplicar `<DataTable maxBodyHeight="calc(100vh - 18rem)">` + `<DataTableHead sticky>`. (No agregar paginación de servidor en esta ola; solo evitar que la página crezca.)
- [ ] **Step 2: Validar** — `cd web && npm run build` → verde.
- [ ] **Step 3: Commit + push A1** — `git commit -am "feat(catalogos,cxc): acota scroll de tablas largas"`. Coordinar push de A1.

---

## WAVE A2 — Agregar búsqueda / filtros donde faltan

> Patrón: agregar `<ListToolbar>` con búsqueda (y filtros relevantes) arriba de la `<DataTable>`; el hook pasa `q`/filtros como query params; el endpoint los aplica con `ilike`/igualdad y devuelve `total` para `<Pagination>`.

### Task A2.1: Remisiones — búsqueda + filtro estatus recepción

**Files:** backend `app/routers/remisiones.py` (listado) + front `web/src/features/remisiones/hooks/use*.ts` + `pages/RemisionesPage.tsx`.

- [ ] **Step 1 (backend):** Agregar `q` (folio/cliente), `recibida:bool|None`, y `total` al listado paginado.
- [ ] **Step 2 (front):** `<ListToolbar>` con búsqueda + dropdown "Recibida/Pendiente/Todas"; el hook envía los params; resetear page a 1 al filtrar.
- [ ] **Step 3: Validar** — build verde + `py_compile`.
- [ ] **Step 4: Commit** — `git commit -am "feat(remisiones): búsqueda + filtro recepción"`

### Task A2.2: Reportes de servicio (lista de documentos) — búsqueda

**Files:** backend `app/routers/reportes_servicio_docs.py` (listado) + front `web/src/features/reportes_servicio_docs/hooks/use*.ts` + `pages/ReportesServicioDocsPage.tsx`.

- [ ] **Step 1 (backend):** Agregar `q` (folio/cliente/técnico) + `total` al listado.
- [ ] **Step 2 (front):** `<ListToolbar>` con búsqueda + `<Pagination>` por `total`.
- [ ] **Step 3: Validar** — build verde + `py_compile`.
- [ ] **Step 4: Commit** — `git commit -am "feat(reportes-servicio-docs): búsqueda en listado"`

### Task A2.3: Usuarios — búsqueda + filtro por rol/estado

**Files:** front `web/src/features/usuarios/pages/UsuariosPage.tsx` (filtrado puede ser client-side si la lista es chica) + hook.

- [ ] **Step 1:** Agregar `<ListToolbar>` con búsqueda (nombre/email) + dropdown rol + dropdown activo/inactivo, filtrando client-side sobre la lista cargada (los usuarios son pocos; no requiere backend).
- [ ] **Step 2: Validar** — build verde.
- [ ] **Step 3: Commit** — `git commit -am "feat(usuarios): búsqueda + filtros por rol/estado"`

### Task A2.4: Contactos — orden por columnas

**Files:** front `web/src/features/contactos/pages/ContactosPage.tsx` (+ hook si el orden es server-side).

- [ ] **Step 1:** Hacer clickeables los headers (nombre/empresa/cargo) para ordenar (mismo patrón que ClientesPage, que ya tiene sort con ↑↓ — copiar ese mecanismo). Si ClientesPage ordena server-side, replicar params; si client-side, replicar el sort en memoria.
- [ ] **Step 2: Validar** — build verde (+ `py_compile` si se tocó backend).
- [ ] **Step 3: Commit + push A2** — `git commit -am "feat(contactos): orden por columnas"`. Coordinar push de A2.

---

## WAVE A3 — Consistencia visual (badges + tabs)

### Task A3.1: Migrar badges de estatus a `<StatusBadge>`

**Files (uno por feature, un commit por feature para diffs chicos):**
- `web/src/features/seguimiento/pages/SeguimientoPage.tsx`
- `web/src/features/clientes/pages/ClientesPage.tsx` (+ tabs de EmpresaDetalle)
- `web/src/features/recordatorios/pages/RecordatoriosPage.tsx`
- `web/src/features/compras/pages/ComprasPage.tsx`
- `web/src/features/fantasmas/pages/FantasmasPage.tsx`
- `web/src/features/borradores/pages/BorradoresPage.tsx`
- `web/src/features/remisiones/` y `web/src/features/reportes_servicio_docs/` (estatus recepción)

- [ ] **Step 1 (por feature):** Localizar los `<span className="… bg-{color}-…">{estatus}</span>` ad-hoc y reemplazarlos por `<StatusBadge status={item.estatus} />` (o `tone=` explícito + `label=` cuando el texto mostrado difiera del valor crudo). El mapa `statusTone` ya cubre los valores; si aparece un estatus sin mapear, agregarlo a `STATUS_TONE` en `status-tones.ts`.
- [ ] **Step 2 (por feature):** `cd web && npm run build` → verde. QA visual rápido del módulo (light/dark).
- [ ] **Step 3 (por feature):** Commit `git commit -am "refactor(<feature>): badges → StatusBadge"`.

### Task A3.2: Unificar tabs al estilo subrayado

**Files:** `web/src/features/recordatorios/pages/RecordatoriosPage.tsx` (tabs redondeado-arriba → `<Tabs>`), y cualquier otro tabset que use estilo distinto (EmpresaDetalle ya usa subrayado; alinear si difiere).

- [ ] **Step 1:** Reemplazar la barra de tabs ad-hoc por `<Tabs tabs={…} value={vista} onChange={setVista} />`.
- [ ] **Step 2: Validar** — `cd web && npm run build` → verde.
- [ ] **Step 3: Commit + push A3** — `git commit -am "refactor(ui): tabs unificados al estilo subrayado"`. Coordinar push de A3.

---

## Validación final (tras todas las olas)

- [ ] `cd web && npm run build` verde; `python3 -m py_compile` sobre todos los routers tocados (`gastos.py`, `servicios.py`, `precios*`, `remisiones.py`, `reportes_servicio_docs.py`).
- [ ] QA visual del usuario por ola: sidebar nuevo navegable; `/spa/analitica` con tabs; redirects de `/spa/reportes` y `/spa/reportes-servicio` funcionan; listados con paginación/altura acotada; badges/tabs consistentes; light/dark y ~375px.
- [ ] Sin cambios de esquema: confirmar que ningún endpoint tocado requirió migración (solo query params + `count()`). Si alguno la requiriera, agregar revisión Alembic + espejo en `_BACKFILL_DDL` (`app/db/seeds.py`).

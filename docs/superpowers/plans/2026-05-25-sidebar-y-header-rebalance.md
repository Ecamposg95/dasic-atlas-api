# Sidebar rebrand + Header rebalance — Plan

> **For agentic workers:** Implementación directa en `main` (no worktrees). Pequeña, 2 archivos.

**Goal:** (1) En el sidebar, intercambiar "Atlas ONE" (grande) con "DASIC" (chico); (2) En el header del cotizador, invertir el ratio de las columnas para que Moneda+TC tengan más espacio y la `TCMiniTable` no se desborde.

**Architecture:** Cambios puramente visuales. Cero lógica, cero backend, cero cálculos. 2 archivos tocados.

**Tech Stack:** React 18 + Tailwind.

---

## File Structure

**Modificar:**
- `web/src/components/layout/Sidebar.tsx` — swap textos del header del sidebar (líneas 71-74)
- `web/src/features/cotizador/components/HeaderCotizacion.tsx` — invertir `col-span` de Cliente y Moneda+TC

**Sin cambios:** Header global, Footer, LoginPage (esos tienen "Atlas ONE" en otros contextos — el usuario solo pidió cambiar el sidebar).

---

### Task 1: Sidebar — "DASIC" grande, "Atlas ONE" en subtítulo

**Files:**
- Modify: `web/src/components/layout/Sidebar.tsx`

- [ ] **Step 1: Cambiar líneas 71-74 del Sidebar**

Localiza en `web/src/components/layout/Sidebar.tsx`:

```tsx
// ANTES
<div className="text-xl font-bold leading-tight">Atlas ONE</div>
<div className="text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-0.5">
  DASIC <span className="text-accent-glow">·</span> Sistema Industrial
</div>
```

Reemplaza con:

```tsx
// DESPUÉS
<div className="text-xl font-bold leading-tight">DASIC</div>
<div className="text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-0.5">
  Atlas ONE <span className="text-accent-glow">·</span> Sistema Industrial
</div>
```

- [ ] **Step 2: Type check**

```bash
cd web && npx tsc --noEmit 2>&1 | tail -5
```

Expected: zero output (sin errores).

---

### Task 2: Cotizador header — invertir col-span

El grid actual es `md:grid-cols-3` con Cliente en `md:col-span-2` (ocupa 2/3 del ancho) y el bloque Moneda+TC en el slot restante (1/3). Como el bloque Moneda+TC contiene la `TCMiniTable` (grid interno de 3 columnas con números a 4 decimales + badges), 1/3 del ancho no le alcanza. Invertimos: Cliente a 1/3, Moneda+TC a 2/3.

**Files:**
- Modify: `web/src/features/cotizador/components/HeaderCotizacion.tsx`

- [ ] **Step 1: Cliente pasa a col-span-1 (default)**

En `HeaderCotizacion.tsx`, línea ~50:

```tsx
// ANTES
<div className="md:col-span-2">
  <label className="text-[10px] uppercase tracking-[0.15em] font-bold text-slate-400 mb-1 flex items-center gap-1.5">
    <User className="h-3 w-3" />
    Cliente
  </label>
  <ClientPicker />
  <UltimaCotHint clienteId={clienteId} />
</div>
```

```tsx
// DESPUÉS — borrar el md:col-span-2 (default = 1 col en md+)
<div>
  <label className="text-[10px] uppercase tracking-[0.15em] font-bold text-slate-400 mb-1 flex items-center gap-1.5">
    <User className="h-3 w-3" />
    Cliente
  </label>
  <ClientPicker />
  <UltimaCotHint clienteId={clienteId} />
</div>
```

- [ ] **Step 2: Moneda+TC pasa a col-span-2**

En el mismo archivo, encuentra el `<div className="grid grid-cols-2 gap-2">` que contiene los dos sub-bloques (Moneda + TC) — está alrededor de la línea 59. Envuélvelo en un wrapper que extienda 2 columnas del grid padre:

```tsx
// ANTES
<div className="grid grid-cols-2 gap-2">
  <div>
    <label … />
    <select … />
  </div>
  <div className={tcNecesario ? '' : 'opacity-60'}>
    <label … />
    <Input … />
    <TCMiniTable />
  </div>
</div>
```

Reemplazar el `<div className="grid grid-cols-2 gap-2">` por uno con `md:col-span-2`:

```tsx
// DESPUÉS
<div className="md:col-span-2 grid grid-cols-2 gap-2">
  <div>
    <label … />
    <select … />
  </div>
  <div className={tcNecesario ? '' : 'opacity-60'}>
    <label … />
    <Input … />
    <TCMiniTable />
  </div>
</div>
```

(El interior se queda igual — solo agregas `md:col-span-2` al wrapper.)

- [ ] **Step 3: Type check**

```bash
cd web && npx tsc --noEmit 2>&1 | tail -5
```

Expected: zero output.

---

### Task 3: Build + commit + push

- [ ] **Step 1: Regenerar bundle**

```bash
cd web && npm run build 2>&1 | tail -8
```

Expected: `✓ built in <N>s`.

- [ ] **Step 2: Commit**

```bash
cd /mnt/c/Users/ecamp/Devs/Dasic_Atlas_api
git add web/src/components/layout/Sidebar.tsx \
        web/src/features/cotizador/components/HeaderCotizacion.tsx \
        app/static/dist
git commit -m "style: DASIC primary en sidebar + balance col-span cotizador

Sidebar:
- 'DASIC' como título grande (antes 'Atlas ONE')
- 'Atlas ONE · Sistema Industrial' como subtítulo (antes solo 'DASIC · Sistema Industrial')

Header cotizador:
- Cliente pasa de md:col-span-2 a default (1/3)
- Moneda+TC pasa a md:col-span-2 (2/3) — la TCMiniTable ya no se desborda

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 3: Push**

```bash
git push origin main
```

Railway autodeploy en marcha.

---

### Task 4: Verificación manual

- [ ] Sidebar muestra "DASIC" grande y "Atlas ONE · Sistema Industrial" chiquito abajo.
- [ ] En `/cotizador/nueva`, en pantallas md+ (>=768px), el Cliente ocupa 1/3 del ancho y el bloque Moneda+TC ocupa 2/3. La `TCMiniTable` ya no comprime las 3 columnitas; los valores DOF/MN→USD/USD→MN se leen sin truncar.
- [ ] En mobile (<768px), todo sigue apilado en 1 columna (sin cambio).
- [ ] El resto del header (fechas creación/vencimiento, vigencia hint) sigue igual.

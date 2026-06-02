# Dropdowns SAT en campos de captura — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reemplazar los inputs de texto libre de los campos SAT (`clave_prod_serv`, `clave_unidad_sat`) por un combobox con búsqueda typeahead en los 3 modales de captura, y sembrar un set curado de claves de unidad para que el dropdown tenga datos.

**Architecture:** Un seeder idempotente puebla `sat_clave_unidad` con ~32 claves comunes. Un componente reutilizable `SatCombobox` (input editable + dropdown debounced que llama a los endpoints typeahead existentes) reemplaza los inputs en producto, fantasma-editar y cotizador-agregar-fantasma. El valor sigue siendo el código string (retrocompatible); se permite texto libre como fallback.

**Tech Stack:** FastAPI + SQLAlchemy (Postgres); React 18 + Vite + TS + Tailwind.

**Verificación (este repo NO tiene suite de tests — CLAUDE.md):** backend `python3 -m py_compile`; frontend `cd web && npm run build`. Sin migración (la tabla `sat_clave_unidad` ya existe en el modelo; create_all/lifespan la materializa). Los endpoints typeahead ya existen (`GET /api/sat/clave-unidad?q=`, `GET /api/sat/clave-prod-serv?q=`).

**Referencia de diseño:** `docs/superpowers/specs/2026-06-01-dropdowns-sat-captura-design.md`.

---

## Fase 1 — Backend: sembrar ClaveUnidad curada

### Task 1: Data file + seeder + wire

**Files:**
- Create: `app/data/sat/claves_unidad.py`
- Modify: `app/db/seeds.py` (nueva función `seed_sat_clave_unidad` + llamada en `run_all_seeds`)

- [ ] **Step 1: Crear la lista curada**

Crear `app/data/sat/claves_unidad.py`:

```python
"""Set curado de claves de unidad SAT (c_ClaveUnidad) de uso frecuente.

El catálogo completo (~2.4K) requiere importer del XLS oficial del SAT; este
subconjunto da datos inmediatos al dropdown de captura. Códigos ≤ 3 chars
(la columna codigo es VARCHAR(3))."""

CLAVE_UNIDAD_COMUNES = [
    ("H87", "Pieza"),
    ("EA", "Elemento"),
    ("E48", "Unidad de servicio"),
    ("ACT", "Actividad"),
    ("XUN", "Unidad"),
    ("C62", "Uno"),
    ("KGM", "Kilogramo"),
    ("GRM", "Gramo"),
    ("MGM", "Miligramo"),
    ("TNE", "Tonelada"),
    ("LTR", "Litro"),
    ("MLT", "Mililitro"),
    ("MTR", "Metro"),
    ("CMT", "Centímetro"),
    ("MMT", "Milímetro"),
    ("KMT", "Kilómetro"),
    ("MTK", "Metro cuadrado"),
    ("MTQ", "Metro cúbico"),
    ("XBX", "Caja"),
    ("XPK", "Paquete"),
    ("XRO", "Rollo"),
    ("XBG", "Bolsa"),
    ("SET", "Juego"),
    ("PR", "Par"),
    ("DZN", "Docena"),
    ("HUR", "Hora"),
    ("DAY", "Día"),
    ("WEE", "Semana"),
    ("MON", "Mes"),
    ("ANN", "Año"),
    ("A9", "Tarifa"),
    ("E51", "Trabajo"),
]
```

- [ ] **Step 2: Agregar el seeder en `seeds.py`**

En `app/db/seeds.py`, justo después de la función `seed_sat_catalogos_pequenos` (que termina antes de `def run_all_seeds`), agregar:

```python
def seed_sat_clave_unidad(db: Session) -> None:
    """Siembra un set curado de claves de unidad SAT (idempotente). El catálogo
    completo requiere importer; esto da datos al dropdown de captura."""
    from app.data.sat.claves_unidad import CLAVE_UNIDAD_COMUNES

    existentes = {row[0] for row in db.query(models.SatClaveUnidad.codigo).all()}
    nuevos = 0
    for codigo, nombre in CLAVE_UNIDAD_COMUNES:
        if codigo in existentes:
            continue
        db.add(models.SatClaveUnidad(codigo=codigo, nombre=nombre, activo=True))
        nuevos += 1
    if nuevos:
        db.commit()
        logger.info("seed_sat_clave_unidad: %s claves de unidad sembradas", nuevos)
```

- [ ] **Step 3: Engancharlo en `run_all_seeds`**

En `app/db/seeds.py`, dentro de `run_all_seeds`, localizar la línea `seed_sat_catalogos_pequenos(db)` (~611) y agregar inmediatamente después:

```python
    seed_sat_clave_unidad(db)
```

- [ ] **Step 4: Verificar**

Run: `python3 -m py_compile app/data/sat/claves_unidad.py app/db/seeds.py`
Expected: sin salida (OK). (`logger` y `models` ya están en scope en seeds.py.)

- [ ] **Step 5: Commit**

```bash
git add app/data/sat/claves_unidad.py app/db/seeds.py
git commit -m "feat(sat): siembra curada de claves de unidad SAT para el dropdown"
```

---

## Fase 2 — Frontend: componente `SatCombobox`

### Task 2: Crear `SatCombobox`

**Files:**
- Create: `web/src/components/ui/sat-combobox.tsx`

- [ ] **Step 1: Crear el componente**

```tsx
import { useEffect, useRef, useState } from 'react';
import { Input } from '@/components/ui/input';

// El endpoint clave-unidad devuelve `nombre`; clave-prod-serv devuelve
// `descripcion`. Leemos ambos para la etiqueta.
type SatItem = { codigo: string; descripcion?: string | null; nombre?: string | null };

export function SatCombobox({
  value,
  onChange,
  endpoint,
  minChars = 2,
  placeholder,
  maxLength,
  className,
}: {
  value: string;
  onChange: (code: string) => void;
  endpoint: string;
  minChars?: number;
  placeholder?: string;
  maxLength?: number;
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<SatItem[]>([]);
  const [loading, setLoading] = useState(false);
  const boxRef = useRef<HTMLDivElement | null>(null);

  // Búsqueda debounced mientras el panel está abierto y hay >= minChars.
  useEffect(() => {
    const q = value.trim();
    if (!open || q.length < minChars) {
      setItems([]);
      return;
    }
    let cancel = false;
    setLoading(true);
    const t = setTimeout(async () => {
      try {
        const r = await fetch(`${endpoint}?q=${encodeURIComponent(q)}&limit=20`, {
          credentials: 'include',
        });
        if (!r.ok) {
          if (!cancel) setItems([]);
          return;
        }
        const data = (await r.json()) as SatItem[];
        if (!cancel) setItems(Array.isArray(data) ? data : []);
      } catch {
        if (!cancel) setItems([]);
      } finally {
        if (!cancel) setLoading(false);
      }
    }, 250);
    return () => {
      cancel = true;
      clearTimeout(t);
    };
  }, [value, open, endpoint, minChars]);

  // Cerrar al click fuera.
  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener('mousedown', onDocClick);
    return () => document.removeEventListener('mousedown', onDocClick);
  }, []);

  function label(it: SatItem) {
    return it.descripcion ?? it.nombre ?? '';
  }

  return (
    <div className="relative" ref={boxRef}>
      <Input
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        placeholder={placeholder}
        maxLength={maxLength}
        className={className}
      />
      {open && value.trim().length >= minChars && (items.length > 0 || loading) && (
        <div className="absolute left-0 right-0 mt-1 max-h-56 overflow-y-auto bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-md shadow-xl z-30">
          {loading && items.length === 0 ? (
            <div className="px-2 py-2 text-xs text-slate-500">Buscando…</div>
          ) : (
            items.map((it) => (
              <button
                key={it.codigo}
                type="button"
                onClick={() => {
                  onChange(it.codigo);
                  setOpen(false);
                }}
                className="w-full text-left px-2 py-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 border-b border-slate-100 dark:border-slate-800 last:border-b-0 flex items-baseline gap-2"
              >
                <span className="font-mono text-xs text-accent-glow">{it.codigo}</span>
                <span className="text-xs text-slate-600 dark:text-slate-300 truncate">{label(it)}</span>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Verificar**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores TS.

- [ ] **Step 3: Commit**

```bash
git add web/src/components/ui/sat-combobox.tsx
git commit -m "feat(ui): SatCombobox — typeahead reutilizable para claves SAT"
```

---

## Fase 3 — Frontend: cablear en los 3 modales

### Task 3: Reemplazar los inputs SAT por `SatCombobox`

**Files:**
- Modify: `web/src/features/inventario/components/ProductoFormModal.tsx`
- Modify: `web/src/features/fantasmas/pages/FantasmasPage.tsx`
- Modify: `web/src/features/cotizador/components/AgregarFantasmaModal.tsx`

- [ ] **Step 1: `ProductoFormModal.tsx`**

Agregar el import (junto a los otros imports de `@/components/ui/...`):
```tsx
import { SatCombobox } from '@/components/ui/sat-combobox';
```
Reemplazar:
```tsx
              <Input value={claveProdServ} onChange={(e) => setClaveProdServ(e.target.value)} maxLength={8} placeholder="Ej. 31181701" className="font-mono" />
```
por:
```tsx
              <SatCombobox value={claveProdServ} onChange={setClaveProdServ} endpoint="/api/sat/clave-prod-serv" minChars={2} maxLength={8} placeholder="Buscar o escribir (ej. 31181701)" className="font-mono" />
```
Y reemplazar:
```tsx
              <Input value={claveUnidadSat} onChange={(e) => setClaveUnidadSat(e.target.value)} maxLength={10} placeholder="Ej. H87" className="font-mono" />
```
por:
```tsx
              <SatCombobox value={claveUnidadSat} onChange={setClaveUnidadSat} endpoint="/api/sat/clave-unidad" minChars={1} maxLength={10} placeholder="Buscar unidad (ej. H87)" className="font-mono" />
```

- [ ] **Step 2: `FantasmasPage.tsx` (modal editar)**

Agregar el import (junto a los otros imports de `@/components/ui/...`):
```tsx
import { SatCombobox } from '@/components/ui/sat-combobox';
```
Reemplazar (en el modal editar, ~líneas 563-568):
```tsx
          <Input value={claveProdServ} onChange={(e) => setClaveProdServ(e.target.value)} maxLength={8} placeholder="Ej. 31181701" className="font-mono" />
```
por:
```tsx
          <SatCombobox value={claveProdServ} onChange={setClaveProdServ} endpoint="/api/sat/clave-prod-serv" minChars={2} maxLength={8} placeholder="Buscar o escribir (ej. 31181701)" className="font-mono" />
```
Y reemplazar:
```tsx
          <Input value={claveUnidadSat} onChange={(e) => setClaveUnidadSat(e.target.value)} maxLength={10} placeholder="Ej. H87" className="font-mono" />
```
por:
```tsx
          <SatCombobox value={claveUnidadSat} onChange={setClaveUnidadSat} endpoint="/api/sat/clave-unidad" minChars={1} maxLength={10} placeholder="Buscar unidad (ej. H87)" className="font-mono" />
```

- [ ] **Step 3: `AgregarFantasmaModal.tsx`**

Agregar el import (junto a `import { Input } from '@/components/ui/input';`):
```tsx
import { SatCombobox } from '@/components/ui/sat-combobox';
```
Reemplazar (~líneas 363-367):
```tsx
            <Input value={claveProdServ} onChange={(e) => setClaveProdServ(e.target.value)} maxLength={8} placeholder="Ej. 31181701" className="h-8 text-xs font-mono" />
```
por:
```tsx
            <SatCombobox value={claveProdServ} onChange={setClaveProdServ} endpoint="/api/sat/clave-prod-serv" minChars={2} maxLength={8} placeholder="Buscar o escribir" className="h-8 text-xs font-mono" />
```
Y reemplazar:
```tsx
            <Input value={claveUnidadSat} onChange={(e) => setClaveUnidadSat(e.target.value)} maxLength={10} placeholder="Ej. H87" className="h-8 text-xs font-mono" />
```
por:
```tsx
            <SatCombobox value={claveUnidadSat} onChange={setClaveUnidadSat} endpoint="/api/sat/clave-unidad" minChars={1} maxLength={10} placeholder="Buscar unidad" className="h-8 text-xs font-mono" />
```

> Nota: `Input` sigue usándose en los 3 archivos para otros campos — NO quitar su import. Si el build reporta `Input` sin usar en alguno, entonces sí quitarlo, pero es improbable.

- [ ] **Step 4: Verificar**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores TS.

- [ ] **Step 5: Commit**

```bash
git add web/src/features/inventario/components/ProductoFormModal.tsx web/src/features/fantasmas/pages/FantasmasPage.tsx web/src/features/cotizador/components/AgregarFantasmaModal.tsx
git commit -m "feat(sat): dropdowns SAT (SatCombobox) en captura de producto, fantasma y cotizador"
```

---

## Fase 4 — Build final + push

### Task 4: Build del SPA y push

- [ ] **Step 1: Build final**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores; `app/static/dist/` regenerado.

- [ ] **Step 2: Commit del dist + push**

```bash
git add app/static/dist
git commit -m "build: recompila SPA (dist) — dropdowns SAT en captura"
git push origin main
```

---

## Notas de verificación manual (post-deploy, recomendado)

- Tras el deploy, `run_all_seeds` puebla `sat_clave_unidad` con las ~32 claves curadas (idempotente).
- Inventario → nuevo/editar producto → campo "Clave unidad SAT": escribir "pie" o "H8" → debe aparecer dropdown con coincidencias (H87 – Pieza); al elegir, el campo queda con el código.
- Campo "Clave producto/servicio SAT": escribir un código → mientras el catálogo esté vacío no hay sugerencias, pero el texto libre se guarda igual (fallback).
- Repetir en el modal de fantasma (editar) y en el cotizador (agregar fantasma).
- Confirmar que guardar el producto/fantasma persiste el código (el value sigue siendo string).

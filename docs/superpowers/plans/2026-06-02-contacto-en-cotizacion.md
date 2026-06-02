# Contacto en la cotización (sub-2) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que la cotización guarde opcionalmente qué contacto (persona) de la empresa hizo el pedido, lo elija en el picker (empresa→contacto) y lo muestre en PDF/Word ("Atención: <contacto>").

**Architecture:** Cambio aditivo: `OrdenVenta.contacto_id` (nullable FK → `contactos`), propagado en los 3 sitios de guardado, expuesto en `/detalle-json`, y renderizado en PDF/Word. El cotizador gana `contacto_id` en el store + un sub-selector en el ClientPicker con autollenado del contacto principal.

**Tech Stack:** FastAPI + SQLAlchemy + Alembic (Postgres); React 18 + Vite + TS + TanStack Query + Zustand.

**Verificación (este repo NO tiene suite de tests — CLAUDE.md):** backend `python3 -m py_compile`; frontend `cd web && npm run build`. Migración nueva requiere espejo en `app/db/seeds.py::_BACKFILL_DDL`. La FK referencia `contactos` (creada en `20260601_05`).

**Referencia de diseño:** `docs/superpowers/specs/2026-06-02-contacto-en-cotizacion-design.md`.

---

## Fase 1 — Backend

### Task 1: Modelo + migración + espejo

**Files:**
- Modify: `app/models/sales.py`
- Create: `migrations/versions/20260601_06_orden_contacto.py`
- Modify: `app/db/seeds.py`

- [ ] **Step 1: Modelo `OrdenVenta`**

En `app/models/sales.py`, después de `cliente_id = Column(Integer, ForeignKey("clientes.id"))` (línea 18), agregar:
```python
    contacto_id = Column(Integer, ForeignKey("contactos.id"), nullable=True)
```
Y después de `cliente = relationship("Cliente", back_populates="ordenes")` (línea 67), agregar:
```python
    contacto = relationship("Contacto", foreign_keys=[contacto_id])
```

- [ ] **Step 2: Migración**

```python
"""orden_contacto — contacto_id en ordenes_venta (sub-2)

Revision ID: 20260601_06
Revises: 20260601_05
Create Date: 2026-06-02
"""
from alembic import op
import sqlalchemy as sa

revision = "20260601_06"
down_revision = "20260601_05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ordenes_venta", sa.Column("contacto_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_ordenes_venta_contacto_id", "ordenes_venta", "contactos",
        ["contacto_id"], ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_ordenes_venta_contacto_id", "ordenes_venta", type_="foreignkey")
    op.drop_column("ordenes_venta", "contacto_id")
```

- [ ] **Step 3: Espejo en `_BACKFILL_DDL`**

En `app/db/seeds.py`, dentro de `_BACKFILL_DDL`, antes del `]` de cierre:
```python
    # 20260601_06 — contacto de la orden (sub-2). FK a contactos (creada en 05).
    "ALTER TABLE IF EXISTS ordenes_venta ADD COLUMN IF NOT EXISTS contacto_id INTEGER REFERENCES contactos(id)",
```

- [ ] **Step 4: Verificar**

Run: `python3 -m py_compile app/models/sales.py migrations/versions/20260601_06_orden_contacto.py app/db/seeds.py`
Expected: sin salida (OK).

- [ ] **Step 5: Commit**

```bash
git add app/models/sales.py migrations/versions/20260601_06_orden_contacto.py app/db/seeds.py
git commit -m "feat(db): OrdenVenta.contacto_id (FK a contactos) + migración + espejo (sub-2)"
```

### Task 2: Schema + persistencia + /detalle-json + PDF

**Files:**
- Modify: `app/schemas/sales.py`
- Modify: `app/routers/ventas.py`

- [ ] **Step 1: Schema `OrdenVentaCreate`**

En `app/schemas/sales.py`, en `OrdenVentaCreate`, después de `cliente_id: int`, agregar:
```python
    contacto_id: Optional[int] = None
```

- [ ] **Step 2: POST crear — constructor de `OrdenVenta`**

En `app/routers/ventas.py`, en el `nueva_orden = models.OrdenVenta(...)` (POST crear), después de `cliente_id=cliente.id,`, agregar:
```python
        contacto_id=orden_data.contacto_id,
```

- [ ] **Step 3: PUT actualizar — asignación de cabecera**

En el bloque de actualización de cabecera, después de `orden.cliente_id = orden_update.cliente_id`, agregar:
```python
    orden.contacto_id = orden_update.contacto_id
```

- [ ] **Step 4: Recotizar — clone**

En el `nueva = models.OrdenVenta(...)` de `recotizar`, después de `cliente_id=origen.cliente_id,`, agregar:
```python
        contacto_id=origen.contacto_id,
```

- [ ] **Step 5: `/detalle-json`**

En el dict de cabecera que retorna `obtener_detalle_orden`, después de `"cliente_id": orden.cliente_id,`, agregar:
```python
        "contacto_id": orden.contacto_id,
```

- [ ] **Step 6: PDF — bloque cliente**

En el template `PDF_TEMPLATE_VENTA`, en el `<div class="cliente">`, después del bloque del email (el `{% endif %}` que cierra el email del cliente) y antes de `</div>`, agregar:
```jinja
        {% if orden.contacto %}<div class="row"><span class="lbl">Atención:</span> {{ orden.contacto.nombre }}</div>{% endif %}
```

- [ ] **Step 7: Verificar**

Run: `python3 -m py_compile app/schemas/sales.py app/routers/ventas.py`
Expected: sin salida (OK).

- [ ] **Step 8: Commit**

```bash
git add app/schemas/sales.py app/routers/ventas.py
git commit -m "feat(api): persiste contacto_id (crear/editar/recotizar) + /detalle-json + Atención en PDF (sub-2)"
```

### Task 3: Word — "Atención"

**Files:**
- Modify: `app/services/word_service.py`

- [ ] **Step 1: Bloque de contacto**

En `build_cotizacion_docx`, después del bloque que agrega los `extras` del cliente (`if extras: doc.add_paragraph("   ".join(extras))...`), agregar:
```python
    # Contacto de la orden (US sub-2): "Atención: <nombre>"
    if getattr(orden, "contacto", None):
        atenc = doc.add_paragraph()
        atenc.add_run("Atención: ").bold = True
        atenc.add_run(orden.contacto.nombre)
```

- [ ] **Step 2: Verificar**

Run: `python3 -m py_compile app/services/word_service.py`
Expected: sin salida (OK).

- [ ] **Step 3: Commit**

```bash
git add app/services/word_service.py
git commit -m "feat(word): Atención <contacto> en el .docx de cotización (sub-2)"
```

---

## Fase 2 — Frontend

### Task 4: Tipos + store + serialize + snapshots

**Files:**
- Modify: `web/src/features/cotizador/types.ts`
- Modify: `web/src/features/cotizador/store.ts`
- Modify: `web/src/features/cotizador/lib/serialize.ts`
- Modify: `web/src/features/cotizador/components/TotalsBar.tsx`
- Modify: `web/src/features/cotizador/pages/CotizadorPage.tsx`

- [ ] **Step 1: Tipos**

En `types.ts`, en `OrdenVentaCreate`, después de `cliente_id: number | null;`, agregar:
```ts
  contacto_id: number | null;
```
En el header de `OrdenVentaDetail` (donde está `cliente_id: number | null;`), agregar después:
```ts
  contacto_id: number | null;
```
Y al final del archivo agregar:
```ts
// Contacto de la empresa (subset para el sub-selector del cotizador).
export type ContactoLite = {
  id: number;
  nombre: string;
  cargo: string | null;
  es_principal: boolean;
};
```

- [ ] **Step 2: Store**

En `store.ts`:
- En el tipo `CotizadorState`, después de `cliente_id: number | null;` agregar `contacto_id: number | null;`.
- En los setters del tipo, después de `setCliente: (id: number | null) => void;` agregar `setContacto: (id: number | null) => void;`.
- En el `initialState`/objeto inicial, después de `cliente_id: null` agregar `contacto_id: null as number | null,`.
- En la implementación de los setters, después de `setCliente: (cliente_id) => set({ cliente_id }),` agregar `setContacto: (contacto_id) => set({ contacto_id }),`.
- En `hydrateFromOrden` (donde setea `cliente_id: orden.cliente_id,`), agregar después `contacto_id: orden.contacto_id ?? null,`.

- [ ] **Step 3: serialize**

En `lib/serialize.ts`:
- En `CotizadorSnapshot`, después de `cliente_id: number | null;` agregar `contacto_id: number | null;`.
- En `buildSavePayload`, después de `cliente_id: s.cliente_id,` agregar `contacto_id: s.contacto_id,`.

- [ ] **Step 4: Snapshots (TotalsBar + CotizadorPage)**

En `components/TotalsBar.tsx`, en el objeto snapshot (donde está `cliente_id: s.cliente_id,`), agregar después `contacto_id: s.contacto_id,`.
En `pages/CotizadorPage.tsx`, en el objeto snapshot (donde está `cliente_id: s.cliente_id,`), agregar después `contacto_id: s.contacto_id,`.

> Si el build (`tsc`) reporta otro constructor de `CotizadorSnapshot` sin `contacto_id`, agregarlo ahí también (es un campo requerido del tipo).

- [ ] **Step 5: Verificar**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores TS.

- [ ] **Step 6: Commit**

```bash
git add web/src/features/cotizador/types.ts web/src/features/cotizador/store.ts web/src/features/cotizador/lib/serialize.ts web/src/features/cotizador/components/TotalsBar.tsx web/src/features/cotizador/pages/CotizadorPage.tsx
git commit -m "feat(cotizador): contacto_id en store/serialize/tipos + snapshots (sub-2)"
```

### Task 5: ClientPicker con sub-selector de contacto

**Files:**
- Modify: `web/src/features/cotizador/components/ClientPicker.tsx`

- [ ] **Step 1: Reemplazar el archivo completo**

```tsx
import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { api } from '@/lib/api';
import { useClientes } from '../hooks/useClientes';
import { useCotizador } from '../store';
import type { ContactoLite } from '../types';

export function ClientPicker() {
  const { data: clientes, isLoading, error } = useClientes();
  const cliente_id = useCotizador((s) => s.cliente_id);
  const setCliente = useCotizador((s) => s.setCliente);
  const contacto_id = useCotizador((s) => s.contacto_id);
  const setContacto = useCotizador((s) => s.setContacto);
  const [q, setQ] = useState('');
  const [open, setOpen] = useState(false);

  const selected = useMemo(
    () => clientes?.find((c) => c.id === cliente_id) ?? null,
    [clientes, cliente_id],
  );

  const matches = useMemo(() => {
    const lista = clientes ?? [];
    const needle = q.trim().toLowerCase();
    if (!needle) return lista.slice(0, 50);
    return lista
      .filter(
        (c) =>
          c.nombre_empresa.toLowerCase().includes(needle) ||
          (c.rfc_tax_id ?? '').toLowerCase().includes(needle) ||
          (c.contacto_nombre ?? '').toLowerCase().includes(needle) ||
          (c.email ?? '').toLowerCase().includes(needle),
      )
      .slice(0, 50);
  }, [clientes, q]);

  // Contactos de la empresa seleccionada (para el sub-selector "Atiende a").
  const { data: contactos } = useQuery<ContactoLite[]>({
    queryKey: ['contactos', cliente_id],
    queryFn: () => api.get<ContactoLite[]>(`/api/clientes/${cliente_id}/contactos`),
    enabled: cliente_id !== null,
  });

  // Autollenar con el contacto principal cuando hay contactos y aún no hay
  // contacto elegido. El guard "solo si null" evita pisar el contacto de una
  // orden ya cargada en edición.
  useEffect(() => {
    if (cliente_id === null || contacto_id !== null) return;
    const lista = contactos ?? [];
    if (lista.length === 0) return;
    const principal = lista.find((c) => c.es_principal) ?? lista[0];
    setContacto(principal.id);
  }, [contactos, cliente_id, contacto_id, setContacto]);

  if (isLoading) {
    return (
      <div className="text-xs text-slate-500 px-3 py-2 border border-slate-700 rounded-md bg-slate-900">
        Cargando clientes…
      </div>
    );
  }
  if (error) {
    return (
      <div className="text-xs text-rose-400 px-3 py-2 border border-rose-800 rounded-md bg-slate-900">
        Error al cargar clientes
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="relative">
        {selected && !open ? (
          <button
            type="button"
            onClick={() => setOpen(true)}
            className="w-full text-left px-3 py-2 border border-slate-700 rounded-md bg-slate-900 hover:border-accent-glow transition"
          >
            <div className="text-sm font-medium">{selected.nombre_empresa}</div>
            <div className="flex items-center gap-2 text-xs text-slate-500">
              {selected.rfc_tax_id && <span className="font-mono">{selected.rfc_tax_id}</span>}
              {selected.email && <span className="truncate">{selected.email}</span>}
            </div>
          </button>
        ) : (
          <div>
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
              <Input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                onFocus={() => setOpen(true)}
                placeholder="Buscar cliente por nombre, RFC, contacto, correo…"
                className="pl-8"
                autoFocus={open}
              />
            </div>
            {open && (
              <div className="absolute left-0 right-0 mt-1 max-h-64 overflow-y-auto bg-slate-900 border border-slate-700 rounded-md shadow-xl z-20">
                {matches.length === 0 ? (
                  <div className="px-3 py-4 text-xs text-slate-500 text-center">
                    Sin coincidencias
                  </div>
                ) : (
                  matches.map((c) => (
                    <button
                      key={c.id}
                      type="button"
                      onClick={() => {
                        setCliente(c.id);
                        setContacto(null);
                        setQ('');
                        setOpen(false);
                      }}
                      className="w-full text-left px-3 py-2 hover:bg-slate-800 transition border-b border-slate-800 last:border-b-0"
                    >
                      <div className="text-sm">{c.nombre_empresa}</div>
                      <div className="flex items-center gap-2 text-[11px] text-slate-500">
                        {c.rfc_tax_id && <span className="font-mono">{c.rfc_tax_id}</span>}
                        {c.email && <span className="truncate">{c.email}</span>}
                      </div>
                    </button>
                  ))
                )}
                {selected && (
                  <button
                    type="button"
                    onClick={() => {
                      setCliente(null);
                      setContacto(null);
                      setQ('');
                      setOpen(false);
                    }}
                    className="w-full text-left px-3 py-2 text-xs text-rose-400 hover:bg-rose-900/20 border-t border-slate-700"
                  >
                    Quitar selección
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {cliente_id !== null && (contactos ?? []).length > 0 && (
        <div>
          <label className="block text-[11px] uppercase tracking-wider text-slate-500 mb-1">Atiende a</label>
          <select
            value={contacto_id ?? ''}
            onChange={(e) => setContacto(e.target.value ? Number(e.target.value) : null)}
            className="w-full h-8 rounded border border-slate-700 bg-slate-900 px-2 text-xs"
          >
            <option value="">— Sin contacto —</option>
            {(contactos ?? []).map((c) => (
              <option key={c.id} value={c.id}>
                {c.nombre}{c.cargo ? ` · ${c.cargo}` : ''}{c.es_principal ? ' ★' : ''}
              </option>
            ))}
          </select>
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
git add web/src/features/cotizador/components/ClientPicker.tsx
git commit -m "feat(cotizador): sub-selector de contacto en ClientPicker + autollenado del principal (sub-2)"
```

---

## Fase 3 — Build final + push

### Task 6: Build del SPA y push

- [ ] **Step 1: Build final**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores; `app/static/dist/` regenerado.

- [ ] **Step 2: Commit del dist + push**

```bash
git add app/static/dist
git commit -m "build: recompila SPA (dist) — contacto en la cotización (sub-2)"
git push origin main
```

---

## Notas de verificación manual (post-deploy, recomendado)

- Cotizador → elegir una empresa → aparece "Atiende a:" autollenado con el contacto principal (★); se puede cambiar o dejar "— Sin contacto —".
- Guardar la cotización → reabrir para editar → el contacto se conserva (round-trip vía /detalle-json).
- Generar el PDF y el Word → aparece "Atención: <contacto>" en el bloque del cliente cuando hay contacto.
- Recotizar → la nueva versión hereda el contacto.
- Cambiar de empresa en el picker → el contacto se resetea y autollena con el principal de la nueva empresa.

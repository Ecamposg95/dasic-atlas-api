# C1 — Unificar contactos (form + hooks compartidos) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminar la duplicación frontend de Contactos: un tipo canónico, los hooks de contacto en el dominio Contactos, y un único `ContactoFormModal` usado por el directorio global y por el tab de empresa.

**Architecture:** El backend ya está unificado (write bajo `/api/clientes/{id}/contactos`, read global en `/api/contactos/`). Este plan solo reordena el frontend: mueve el tipo y los hooks de contacto a `features/contactos/`, agrega un modo `clienteIdFijo` al modal, y reemplaza el form inline del tab por el modal compartido.

**Tech Stack:** React 18 + TS + Vite + TanStack Query v5. **No hay suite de tests** (CLAUDE.md): validación = `cd web && npm run build` verde (corre `tsc -b` antes de vite) por tarea. `app/static/dist/` se commitea. Sin backend ni esquema.

**Spec:** `docs/superpowers/specs/2026-06-12-c1-contactos-dedup-design.md`

---

## File Structure

- `web/src/features/contactos/types.ts` — **dueño** de `Contacto`, `ContactoInput`, `ContactoGlobal` (canónicos).
- `web/src/features/clientes/types.ts` — deja de declarar `Contacto`/`ContactoInput`; los re-exporta desde contactos.
- `web/src/features/contactos/hooks/useContactoMutations.ts` (NUEVO) — `useContactosEmpresa`, `useGuardarContacto`, `useEliminarContacto`.
- `web/src/features/clientes/hooks/useEmpresaDetalle.ts` — pierde esas 3 funciones; conserva el resto.
- `web/src/features/contactos/components/ContactoFormModal.tsx` — gana prop `clienteIdFijo`.
- `web/src/features/clientes/components/tabs/ContactosTab.tsx` — usa el modal en vez del form inline.
- `web/src/features/contactos/pages/ContactosPage.tsx` — re-apunta el import de `useEliminarContacto`.

---

## Task 1: Tipo canónico de contacto

**Files:**
- Modify: `web/src/features/contactos/types.ts`
- Modify: `web/src/features/clientes/types.ts:40-56`

- [ ] **Step 1: Agregar `Contacto` y `ContactoInput` a contactos/types.ts y derivar `ContactoGlobal`**

En `web/src/features/contactos/types.ts`, reemplazar el bloque `export type ContactoGlobal = { ... }` por:

```ts
export type Contacto = {
  id: number;
  cliente_id: number;
  nombre: string;
  cargo: string | null;
  email: string | null;
  telefono: string | null;
  es_principal: boolean;
};

export type ContactoInput = {
  nombre: string;
  cargo?: string | null;
  email?: string | null;
  telefono?: string | null;
  es_principal?: boolean;
};

export type ContactoGlobal = Contacto & { empresa_nombre: string | null };
```

(Conservar `ContactosResponse` y `ContactoOrden` tal cual; `ContactosResponse.items` sigue siendo `ContactoGlobal[]`.)

- [ ] **Step 2: En clientes/types.ts, reemplazar las declaraciones por un re-export**

En `web/src/features/clientes/types.ts`, borrar los dos bloques `export type Contacto = { ... };` y `export type ContactoInput = { ... };` (líneas ~40-56) y poner en su lugar:

```ts
export type { Contacto, ContactoInput } from '@/features/contactos/types';
```

- [ ] **Step 3: Validar build**

Run: `cd web && npm run build`
Expected: verde. (`Contacto`/`ContactoInput` ahora vienen de contactos; `useEmpresaDetalle.ts` y `ContactosTab.tsx` que importan `Contacto` desde `../types`/`../../types` siguen resolviendo vía el re-export.)

- [ ] **Step 4: Commit**

```bash
git add web/src/features/contactos/types.ts web/src/features/clientes/types.ts
git commit -m "refactor(contactos): tipo canónico Contacto/ContactoInput en features/contactos"
```

---

## Task 2: Mover los hooks de contacto al dominio Contactos

**Files:**
- Create: `web/src/features/contactos/hooks/useContactoMutations.ts`
- Modify: `web/src/features/clientes/hooks/useEmpresaDetalle.ts:1-37`
- Modify: `web/src/features/contactos/components/ContactoFormModal.tsx:7`
- Modify: `web/src/features/contactos/pages/ContactosPage.tsx:11`
- Modify: `web/src/features/clientes/components/tabs/ContactosTab.tsx:9-19` (re-apunte mínimo; el rewrite completo es Task 4)

- [ ] **Step 1: Crear `useContactoMutations.ts`**

```ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Contacto, ContactoInput } from '../types';

export function useContactosEmpresa(clienteId: number | null) {
  return useQuery<Contacto[]>({
    queryKey: ['contactos', clienteId],
    queryFn: () => api.get<Contacto[]>(`/api/clientes/${clienteId}/contactos`),
    enabled: clienteId !== null,
  });
}

export function useGuardarContacto(clienteId: number) {
  const qc = useQueryClient();
  return useMutation<Contacto, { status?: number; detail?: string }, { id?: number; data: ContactoInput }>({
    mutationFn: ({ id, data }) =>
      id
        ? api.patch<Contacto>(`/api/clientes/${clienteId}/contactos/${id}`, data)
        : api.post<Contacto>(`/api/clientes/${clienteId}/contactos`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['contactos', clienteId] });
      qc.invalidateQueries({ queryKey: ['clientes'] });
      void qc.invalidateQueries({ queryKey: ['contactos', 'global'] });
    },
  });
}

export function useEliminarContacto(clienteId: number) {
  const qc = useQueryClient();
  return useMutation<{ ok: boolean }, { status?: number; detail?: string }, number>({
    mutationFn: (id) => api.delete<{ ok: boolean }>(`/api/clientes/${clienteId}/contactos/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['contactos', clienteId] });
      void qc.invalidateQueries({ queryKey: ['contactos', 'global'] });
    },
  });
}
```

- [ ] **Step 2: Quitar las 3 funciones de `useEmpresaDetalle.ts`**

En `web/src/features/clientes/hooks/useEmpresaDetalle.ts`: borrar `useContactos` (líneas 5-11), `useGuardarContacto` (13-26) y `useEliminarContacto` (28-37). En el import de la línea 3, quitar `Contacto, ContactoInput` (ya no se usan en este archivo), dejando:

```ts
import type { TransaccionCuenta, CxCClienteResponse } from '../types';
```

(Conservar `useEstadoCuenta`, `useCxCCliente`, `useOrdenesEmpresa`, `useRegistrarPago` sin cambios.)

- [ ] **Step 3: Re-apuntar `ContactoFormModal.tsx`**

En `web/src/features/contactos/components/ContactoFormModal.tsx` línea 7, cambiar:

```ts
import { useGuardarContacto } from '@/features/clientes/hooks/useEmpresaDetalle';
```
por:
```ts
import { useGuardarContacto } from '../hooks/useContactoMutations';
```

- [ ] **Step 4: Re-apuntar `ContactosPage.tsx`**

En `web/src/features/contactos/pages/ContactosPage.tsx` línea 11, cambiar:

```ts
import { useEliminarContacto } from '@/features/clientes/hooks/useEmpresaDetalle';
```
por:
```ts
import { useEliminarContacto } from '../hooks/useContactoMutations';
```

- [ ] **Step 5: Re-apunte mínimo de `ContactosTab.tsx` (para mantener el build verde; el rewrite es Task 4)**

En `web/src/features/clientes/components/tabs/ContactosTab.tsx`, cambiar el import de hooks (líneas 9-13):

```ts
import {
  useContactosEmpresa,
  useGuardarContacto,
  useEliminarContacto,
} from '@/features/contactos/hooks/useContactoMutations';
```

y en la línea 19 cambiar `useContactos(clienteId)` por `useContactosEmpresa(clienteId)`.

- [ ] **Step 6: Validar build**

Run: `cd web && npm run build`
Expected: verde. Si `tsc` marca algún otro importador de las funciones movidas, re-apuntarlo al nuevo archivo (no debería haber más: solo ContactoFormModal, ContactosPage y ContactosTab las usaban).

- [ ] **Step 7: Commit**

```bash
git add web/src/features/contactos/hooks/useContactoMutations.ts web/src/features/clientes/hooks/useEmpresaDetalle.ts web/src/features/contactos/components/ContactoFormModal.tsx web/src/features/contactos/pages/ContactosPage.tsx web/src/features/clientes/components/tabs/ContactosTab.tsx
git commit -m "refactor(contactos): hooks de contacto en features/contactos/useContactoMutations"
```

---

## Task 3: Prop `clienteIdFijo` en `ContactoFormModal`

**Files:**
- Modify: `web/src/features/contactos/components/ContactoFormModal.tsx`

- [ ] **Step 1: Aceptar `clienteIdFijo` y un `editing` más amplio**

En el import de tipos (línea 8) cambiar:
```ts
import type { ContactoGlobal } from '../types';
```
por:
```ts
import type { Contacto, ContactoGlobal } from '../types';
```

Cambiar la firma del componente:
```tsx
export function ContactoFormModal({
  open,
  onClose,
  editing,
  clienteIdFijo,
}: {
  open: boolean;
  onClose: () => void;
  editing: Contacto | ContactoGlobal | null;
  clienteIdFijo?: number;
}) {
  const { data: empresas } = useClientes({ page: 1, q: '', pageSize: 500 });
  const [empresaId, setEmpresaId] = useState<number | null>(clienteIdFijo ?? editing?.cliente_id ?? null);
```

(El resto de los `useState` de campos quedan igual.)

- [ ] **Step 2: Ocultar el bloque de empresa cuando hay `clienteIdFijo`**

En el JSX, envolver el bloque de empresa para que solo se muestre cuando NO hay empresa fija. Reemplazar el bloque actual:

```tsx
        <div>
          <label className="block text-xs text-slate-500 mb-1">Empresa *</label>
          {editing ? (
            <div className="text-sm text-foreground">{editing.empresa_nombre}</div>
          ) : (
            <select
              value={empresaId ?? ''}
              onChange={(e) => setEmpresaId(e.target.value ? parseInt(e.target.value, 10) : null)}
              className="w-full h-9 text-sm rounded border border-border-strong bg-card px-2"
            >
              <option value="">— Elige empresa —</option>
              {(empresas ?? []).map((c) => (
                <option key={c.id} value={c.id}>{c.nombre_empresa}</option>
              ))}
            </select>
          )}
        </div>
```

por:

```tsx
        {clienteIdFijo == null && (
          <div>
            <label className="block text-xs text-slate-500 mb-1">Empresa *</label>
            {editing ? (
              <div className="text-sm text-foreground">{(editing as ContactoGlobal).empresa_nombre}</div>
            ) : (
              <select
                value={empresaId ?? ''}
                onChange={(e) => setEmpresaId(e.target.value ? parseInt(e.target.value, 10) : null)}
                className="w-full h-9 text-sm rounded border border-border-strong bg-card px-2"
              >
                <option value="">— Elige empresa —</option>
                {(empresas ?? []).map((c) => (
                  <option key={c.id} value={c.id}>{c.nombre_empresa}</option>
                ))}
              </select>
            )}
          </div>
        )}
```

(El `onSave` no cambia: con `clienteIdFijo` el `empresaId` ya viene fijo, así que la guarda `if (!empresaId)` pasa. `useGuardarContacto(empresaId ?? 0)` sigue igual.)

- [ ] **Step 3: Validar build**

Run: `cd web && npm run build`
Expected: verde. El consumidor global (`ContactosPage`) no pasa `clienteIdFijo` → comportamiento idéntico al actual.

- [ ] **Step 4: Commit**

```bash
git add web/src/features/contactos/components/ContactoFormModal.tsx
git commit -m "feat(contactos): ContactoFormModal con modo clienteIdFijo (empresa bloqueada)"
```

---

## Task 4: `ContactosTab` usa el modal compartido + limpieza

**Files:**
- Modify (rewrite): `web/src/features/clientes/components/tabs/ContactosTab.tsx`

- [ ] **Step 1: Reescribir `ContactosTab.tsx`**

Reemplazar TODO el archivo por:

```tsx
import { useState } from 'react';
import { confirm } from '@/lib/confirm';
import { useNavigate } from 'react-router-dom';
import { Plus, Star, Trash2, Pencil, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { Contacto } from '@/features/contactos/types';
import { useContactosEmpresa, useEliminarContacto } from '@/features/contactos/hooks/useContactoMutations';
import { ContactoFormModal } from '@/features/contactos/components/ContactoFormModal';

export function ContactosTab({ clienteId }: { clienteId: number }) {
  const navigate = useNavigate();
  const { data: contactos } = useContactosEmpresa(clienteId);
  const eliminar = useEliminarContacto(clienteId);

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Contacto | null>(null);

  function abrirNuevo() { setEditing(null); setModalOpen(true); }
  function abrirEditar(c: Contacto) { setEditing(c); setModalOpen(true); }

  return (
    <div className="p-1 space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm text-muted-foreground">{(contactos ?? []).length} contacto(s)</span>
        <Button size="sm" onClick={abrirNuevo}><Plus className="h-3.5 w-3.5 mr-1" /> Agregar</Button>
      </div>
      <div className="space-y-1">
        {(contactos ?? []).map((c) => (
          <div key={c.id} className="flex items-center justify-between rounded-md border border-border px-3 py-2">
            <div className="min-w-0">
              <div className="flex items-center gap-1.5 text-sm">
                {c.es_principal && <Star className="h-3.5 w-3.5 text-amber-500 shrink-0" />}
                <span className="font-medium truncate">{c.nombre}</span>
                {c.cargo && <span className="text-xs text-muted-foreground">· {c.cargo}</span>}
              </div>
              <div className="text-xs text-muted-foreground truncate">{[c.email, c.telefono].filter(Boolean).join(' · ') || '—'}</div>
            </div>
            <div className="flex items-center gap-1 shrink-0">
              <button
                onClick={() => navigate(`/spa/cotizador?cliente=${clienteId}&contacto=${c.id}`)}
                className="p-1 text-muted-foreground hover:text-emerald-500"
                title="Cotizar"
              >
                <FileText className="h-4 w-4" />
              </button>
              <button onClick={() => abrirEditar(c)} className="p-1 text-muted-foreground hover:text-cyan-500" title="Editar"><Pencil className="h-4 w-4" /></button>
              <button
                onClick={async () => {
                  if (await confirm({ mensaje: `¿Eliminar a ${c.nombre}?`, tono: 'danger' })) eliminar.mutate(c.id);
                }}
                className="p-1 text-muted-foreground hover:text-rose-500"
                title="Eliminar"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        ))}
        {(contactos ?? []).length === 0 && <p className="text-xs text-muted-foreground py-2">Sin contactos.</p>}
      </div>

      {modalOpen && (
        <ContactoFormModal
          key={editing?.id ?? 'new'}
          open={modalOpen}
          onClose={() => setModalOpen(false)}
          editing={editing}
          clienteIdFijo={clienteId}
        />
      )}
    </div>
  );
}
```

(Esto elimina el form inline, `VACIO`, el estado `form`/`showForm`, `guardarContacto`, y los imports muertos de `Input`/`ContactoInput`/`useGuardarContacto`/`toast`. El modal maneja crear/editar y su propio toast/cierre; al guardar invalida `['contactos', clienteId]` vía el hook, refrescando la lista.)

- [ ] **Step 2: Validar build**

Run: `cd web && npm run build`
Expected: verde, sin warnings de imports sin usar.

- [ ] **Step 3: Commit (incluye dist)**

```bash
git add web/src/features/clientes/components/tabs/ContactosTab.tsx app/static/dist
git commit -m "refactor(clientes): ContactosTab usa ContactoFormModal compartido (quita form inline)"
```

---

## Self-Review / Validación final

- [ ] `cd web && npm run build` verde; `git status app/static/dist` → 0 cambios tras rebuild (dist reproducible).
- [ ] Grep de control: `grep -rn "useEmpresaDetalle" web/src` no debe mostrar imports de `useContactos`/`useGuardarContacto`/`useEliminarContacto`; `grep -rn "ContactoGlobal = {" web/src` solo en contactos/types (no dup en clientes).
- [ ] QA visual del usuario: **directorio global** (`/spa/contactos`) — crear (pide empresa), editar, eliminar, historial, cotizar. **Tab de empresa** (`/spa/empresas/:id` → Contactos) — "Agregar" abre modal con empresa bloqueada, editar/eliminar/★ principal, la lista refresca. Light/dark.
```

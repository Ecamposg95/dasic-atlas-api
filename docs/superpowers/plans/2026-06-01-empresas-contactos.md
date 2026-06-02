# Empresas + Contactos (sub-1) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convertir el área de Clientes en un área de Empresas con contactos (personas) por empresa, crédito por empresa (ya existente), y un detalle de empresa con contactos + estado de cuenta/CxC cableado.

**Architecture:** La tabla `clientes` se conserva como la empresa (crédito/FKs intactas). Se agrega tabla `contactos` (hijos) con CRUD anidado bajo `/api/clientes/{id}/contactos`. El "contacto principal" sincroniza los campos denormalizados `contacto_nombre/email/telefono` del cliente (que ya leen picker/PDF). El frontend gana un `EmpresaDetalleDrawer` con secciones de contactos y estado de cuenta/CxC (reutilizando endpoints existentes).

**Tech Stack:** FastAPI + SQLAlchemy + Alembic (Postgres); React 18 + Vite + TS + TanStack Query.

**Verificación (este repo NO tiene suite de tests — CLAUDE.md):** backend `python3 -m py_compile`; frontend `cd web && npm run build`. Migración nueva requiere espejo en `app/db/seeds.py::_BACKFILL_DDL`. Schemas nuevos requieren re-export en `app/schemas/__init__.py`.

**Referencia de diseño:** `docs/superpowers/specs/2026-06-01-empresas-contactos-design.md`.

---

## Fase 1 — Backend: modelo + migración + backfill

### Task 1: Modelo `Contacto` + relationship + export

**Files:**
- Modify: `app/models/clients.py`
- Modify: `app/models/__init__.py`

- [ ] **Step 1: Imports + modelo en `clients.py`**

Reemplazar la línea de imports:
```python
from sqlalchemy import Column, DECIMAL, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
```
por:
```python
from sqlalchemy import Boolean, Column, DECIMAL, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
```

En la clase `Cliente`, después de `creado_por = relationship("Usuario", foreign_keys=[creado_por_id])`, agregar:
```python
    contactos = relationship("Contacto", back_populates="cliente", cascade="all, delete-orphan")
```

Al final del archivo, agregar el modelo:
```python
class Contacto(Base):
    """Persona de contacto de una empresa (cliente). Varias por empresa."""
    __tablename__ = "contactos"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False, index=True)
    nombre = Column(String(120), nullable=False)
    cargo = Column(String(80), nullable=True)
    email = Column(String(120), nullable=True)
    telefono = Column(String(40), nullable=True)
    es_principal = Column(Boolean, nullable=False, server_default=text("false"))
    creado_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    cliente = relationship("Cliente", back_populates="contactos")
```

- [ ] **Step 2: Exportar `Contacto` en `app/models/__init__.py`**

Buscar la línea que importa de `app.models.clients` (ej. `from app.models.clients import (Cliente, Proveedor)`) y agregar `Contacto`. Si hay un `__all__`, agregar `"Contacto"`. (Replica el patrón de los demás modelos del archivo.)

- [ ] **Step 3: Verificar**

Run: `python3 -m py_compile app/models/clients.py app/models/__init__.py`
Expected: sin salida (OK).

- [ ] **Step 4: Commit**

```bash
git add app/models/clients.py app/models/__init__.py
git commit -m "feat(models): tabla contactos (personas por empresa) + relationship"
```

### Task 2: Migración + espejo `_BACKFILL_DDL`

**Files:**
- Create: `migrations/versions/20260601_05_contactos.py`
- Modify: `app/db/seeds.py`

- [ ] **Step 1: Migración**

```python
"""contactos — personas por empresa (sub-1 empresas+contactos)

Revision ID: 20260601_05
Revises: 20260601_04
Create Date: 2026-06-01
"""
from alembic import op
import sqlalchemy as sa

revision = "20260601_05"
down_revision = "20260601_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "contactos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cliente_id", sa.Integer(), sa.ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("cargo", sa.String(80), nullable=True),
        sa.Column("email", sa.String(120), nullable=True),
        sa.Column("telefono", sa.String(40), nullable=True),
        sa.Column("es_principal", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("contactos")
```

- [ ] **Step 2: Espejo en `_BACKFILL_DDL`**

En `app/db/seeds.py`, dentro de la lista `_BACKFILL_DDL`, antes del `]` de cierre, agregar:
```python
    # ====================================================================
    # 20260601_05 — contactos (personas por empresa). Aditivo.
    # ====================================================================
    """CREATE TABLE IF NOT EXISTS contactos (
        id SERIAL PRIMARY KEY,
        cliente_id INTEGER NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
        nombre VARCHAR(120) NOT NULL,
        cargo VARCHAR(80),
        email VARCHAR(120),
        telefono VARCHAR(40),
        es_principal BOOLEAN NOT NULL DEFAULT FALSE,
        creado_en TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
    )""",
    "CREATE INDEX IF NOT EXISTS ix_contactos_cliente_id ON contactos (cliente_id)",
```

- [ ] **Step 3: Verificar**

Run: `python3 -m py_compile migrations/versions/20260601_05_contactos.py app/db/seeds.py`
Expected: sin salida (OK).

- [ ] **Step 4: Commit**

```bash
git add migrations/versions/20260601_05_contactos.py app/db/seeds.py
git commit -m "feat(db): tabla contactos (migración + espejo _BACKFILL_DDL)"
```

### Task 3: Backfill idempotente del contacto principal

**Files:**
- Modify: `app/db/seeds.py`

- [ ] **Step 1: Agregar el seeder**

En `app/db/seeds.py`, antes de `def run_all_seeds`, agregar:
```python
def seed_contactos_principal(db: Session) -> None:
    """Backfill idempotente: por cada Cliente con contacto_nombre y SIN contactos,
    crea un Contacto principal copiando nombre/email/telefono."""
    clientes = db.query(models.Cliente).all()
    creados = 0
    for c in clientes:
        if not (c.contacto_nombre or "").strip():
            continue
        existe = db.query(models.Contacto.id).filter(models.Contacto.cliente_id == c.id).first()
        if existe:
            continue
        db.add(models.Contacto(
            cliente_id=c.id,
            nombre=c.contacto_nombre.strip(),
            email=(c.email or None),
            telefono=(c.telefono or None),
            es_principal=True,
        ))
        creados += 1
    if creados:
        db.commit()
        logger.info("seed_contactos_principal: %s contactos principales creados", creados)
```

- [ ] **Step 2: Engancharlo en `run_all_seeds`**

En `run_all_seeds`, antes de `logger.info("Startup completado correctamente.")`, agregar:
```python
    seed_contactos_principal(db)
```

- [ ] **Step 3: Verificar**

Run: `python3 -m py_compile app/db/seeds.py`
Expected: sin salida (OK).

- [ ] **Step 4: Commit**

```bash
git add app/db/seeds.py
git commit -m "feat(db): backfill idempotente de contacto principal por empresa"
```

---

## Fase 2 — Backend: schemas + endpoints de contactos

### Task 4: Schemas `Contacto*` + re-export

**Files:**
- Modify: `app/schemas/clients.py`
- Modify: `app/schemas/__init__.py`

- [ ] **Step 1: Schemas en `clients.py`**

Al final de `app/schemas/clients.py`, agregar:
```python
class ContactoBase(BaseModel):
    nombre: str
    cargo: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    es_principal: bool = False


class ContactoCreate(ContactoBase):
    pass


class ContactoUpdate(BaseModel):
    nombre: Optional[str] = None
    cargo: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    es_principal: Optional[bool] = None


class ContactoResponse(ContactoBase):
    id: int
    cliente_id: int
    model_config = ConfigDict(from_attributes=True)
```

- [ ] **Step 2: Re-export en `app/schemas/__init__.py`**

En el bloque `from app.schemas.clients import (...)`, agregar `ContactoBase, ContactoCreate, ContactoUpdate, ContactoResponse`. En `__all__`, después de la línea de clients, agregar:
```python
    "ContactoBase", "ContactoCreate", "ContactoUpdate", "ContactoResponse",
```

- [ ] **Step 3: Verificar**

Run: `python3 -m py_compile app/schemas/clients.py app/schemas/__init__.py && python3 -c "import app.schemas; app.schemas.ContactoResponse" 2>/dev/null || echo "import-check requiere venv (pydantic) — revisar __init__ a ojo"`
Expected: compila; el import-check puede fallar localmente por falta de venv (pydantic) — basta revisar el `__init__.py`.

- [ ] **Step 4: Commit**

```bash
git add app/schemas/clients.py app/schemas/__init__.py
git commit -m "feat(schemas): Contacto* + re-export en app.schemas"
```

### Task 5: Endpoints de contactos (anidados en clientes.py)

**Files:**
- Modify: `app/routers/clientes.py`

- [ ] **Step 1: Helper + endpoints**

Al final de `app/routers/clientes.py`, agregar (el router tiene `prefix="/api/clientes"`; `models`, `schemas`, `get_db`, `allow_all_staff`, `List`, `logger`, `HTTPException`, `Depends`, `Session` ya están importados en el archivo):
```python
def _sync_contacto_principal(db: Session, cliente, contacto) -> None:
    """Desmarca otros principales de la empresa y sincroniza el trío
    denormalizado del cliente (lo que leen picker/PDF) desde el contacto."""
    db.query(models.Contacto).filter(
        models.Contacto.cliente_id == cliente.id,
        models.Contacto.id != contacto.id,
    ).update({models.Contacto.es_principal: False})
    cliente.contacto_nombre = contacto.nombre
    cliente.email = contacto.email
    cliente.telefono = contacto.telefono


@router.get("/{cliente_id}/contactos", response_model=List[schemas.ContactoResponse], dependencies=[Depends(allow_all_staff)])
def listar_contactos(cliente_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.Contacto)
        .filter(models.Contacto.cliente_id == cliente_id)
        .order_by(models.Contacto.es_principal.desc(), models.Contacto.nombre.asc())
        .all()
    )


@router.post("/{cliente_id}/contactos", response_model=schemas.ContactoResponse, dependencies=[Depends(allow_all_staff)])
def crear_contacto(cliente_id: int, payload: schemas.ContactoCreate, db: Session = Depends(get_db)):
    cliente = db.query(models.Cliente).filter(models.Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(404, "Empresa no encontrada")
    try:
        c = models.Contacto(
            cliente_id=cliente_id,
            nombre=payload.nombre.strip(),
            cargo=(payload.cargo or None),
            email=(payload.email or None),
            telefono=(payload.telefono or None),
            es_principal=bool(payload.es_principal),
        )
        db.add(c)
        db.flush()
        if c.es_principal:
            _sync_contacto_principal(db, cliente, c)
        db.commit()
        db.refresh(c)
        return c
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("clientes.crear_contacto falló")
        raise HTTPException(500, detail=f"{type(exc).__name__}: {exc}")


@router.patch("/{cliente_id}/contactos/{contacto_id}", response_model=schemas.ContactoResponse, dependencies=[Depends(allow_all_staff)])
def actualizar_contacto(cliente_id: int, contacto_id: int, payload: schemas.ContactoUpdate, db: Session = Depends(get_db)):
    c = (
        db.query(models.Contacto)
        .filter(models.Contacto.id == contacto_id, models.Contacto.cliente_id == cliente_id)
        .first()
    )
    if not c:
        raise HTTPException(404, "Contacto no encontrado")
    try:
        data = payload.model_dump(exclude_unset=True)
        if "nombre" in data and data["nombre"]:
            data["nombre"] = data["nombre"].strip()
        for k, v in data.items():
            setattr(c, k, v)
        db.flush()
        if c.es_principal:
            cliente = db.query(models.Cliente).filter(models.Cliente.id == cliente_id).first()
            if cliente:
                _sync_contacto_principal(db, cliente, c)
        db.commit()
        db.refresh(c)
        return c
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("clientes.actualizar_contacto falló")
        raise HTTPException(500, detail=f"{type(exc).__name__}: {exc}")


@router.delete("/{cliente_id}/contactos/{contacto_id}", dependencies=[Depends(allow_all_staff)])
def eliminar_contacto(cliente_id: int, contacto_id: int, db: Session = Depends(get_db)):
    c = (
        db.query(models.Contacto)
        .filter(models.Contacto.id == contacto_id, models.Contacto.cliente_id == cliente_id)
        .first()
    )
    if not c:
        raise HTTPException(404, "Contacto no encontrado")
    db.delete(c)
    db.commit()
    return {"ok": True}
```

- [ ] **Step 2: Verificar**

Run: `python3 -m py_compile app/routers/clientes.py`
Expected: sin salida (OK).

- [ ] **Step 3: Commit**

```bash
git add app/routers/clientes.py
git commit -m "feat(api): CRUD de contactos por empresa + sync de contacto principal"
```

---

## Fase 3 — Frontend: área de empresas

### Task 6: Tipos + hooks del detalle de empresa

**Files:**
- Modify: `web/src/features/clientes/types.ts`
- Create: `web/src/features/clientes/hooks/useEmpresaDetalle.ts`

- [ ] **Step 1: Tipos**

Al final de `web/src/features/clientes/types.ts`, agregar:
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

export type TransaccionCuenta = {
  id: number;
  fecha: string;
  monto: number | string;
  tipo: string;
  descripcion: string;
  referencia_id: number | null;
};

export type CargoAbierto = {
  id: number;
  orden_venta_id: number | null;
  folio: string | null;
  fecha: string | null;
  fecha_vencimiento: string | null;
  descripcion: string;
  monto: number;
  monto_pagado: number;
  saldo_pendiente: number;
  estatus_pago: string;
  dias_atraso: number;
};

export type CxCClienteResponse = {
  cliente: {
    id: number;
    nombre_empresa: string;
    saldo_actual: number;
    limite_credito: number;
    dias_credito: number;
    moneda_credito: string;
  };
  cargos: CargoAbierto[];
};
```

- [ ] **Step 2: Hooks**

Crear `web/src/features/clientes/hooks/useEmpresaDetalle.ts`:
```ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Contacto, ContactoInput, TransaccionCuenta, CxCClienteResponse } from '../types';

export function useContactos(clienteId: number | null) {
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
    },
  });
}

export function useEliminarContacto(clienteId: number) {
  const qc = useQueryClient();
  return useMutation<{ ok: boolean }, { status?: number; detail?: string }, number>({
    mutationFn: (id) => api.delete<{ ok: boolean }>(`/api/clientes/${clienteId}/contactos/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['contactos', clienteId] }),
  });
}

export function useEstadoCuenta(clienteId: number | null) {
  return useQuery<TransaccionCuenta[]>({
    queryKey: ['estado-cuenta', clienteId],
    queryFn: () => api.get<TransaccionCuenta[]>(`/api/clientes/${clienteId}/estado-cuenta`),
    enabled: clienteId !== null,
  });
}

export function useCxCCliente(clienteId: number | null) {
  return useQuery<CxCClienteResponse>({
    queryKey: ['cxc-cliente', clienteId],
    queryFn: () => api.get<CxCClienteResponse>(`/api/clientes/${clienteId}/cuentas-por-cobrar`),
    enabled: clienteId !== null,
  });
}

export function useRegistrarPago(clienteId: number) {
  const qc = useQueryClient();
  return useMutation<{ mensaje: string; nuevo_saldo: number }, { status?: number; detail?: string }, { monto: number; descripcion: string }>({
    mutationFn: ({ monto, descripcion }) =>
      api.post<{ mensaje: string; nuevo_saldo: number }>(
        `/api/clientes/${clienteId}/registrar-pago?monto=${monto}&descripcion=${encodeURIComponent(descripcion)}`,
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['cxc-cliente', clienteId] });
      qc.invalidateQueries({ queryKey: ['estado-cuenta', clienteId] });
      qc.invalidateQueries({ queryKey: ['clientes'] });
    },
  });
}
```

> Nota: `registrar-pago` recibe `monto`/`descripcion` como **query params** (no body) — por eso van en la URL.

- [ ] **Step 3: Verificar**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores TS.

- [ ] **Step 4: Commit**

```bash
git add web/src/features/clientes/types.ts web/src/features/clientes/hooks/useEmpresaDetalle.ts
git commit -m "feat(empresas): tipos + hooks de contactos, estado de cuenta y pago"
```

### Task 7: `EmpresaDetalleDrawer`

**Files:**
- Create: `web/src/features/clientes/components/EmpresaDetalleDrawer.tsx`

- [ ] **Step 1: Crear el componente**

```tsx
import { useState } from 'react';
import { X, Plus, Star, Trash2, Pencil } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from '@/lib/toast';
import type { Cliente, Contacto, ContactoInput } from '../types';
import {
  useContactos,
  useGuardarContacto,
  useEliminarContacto,
  useCxCCliente,
  useRegistrarPago,
} from '../hooks/useEmpresaDetalle';

function fmtMoney(n: number | string, m = 'MXN') {
  return `${m} $${Number(n || 0).toLocaleString('es-MX', { minimumFractionDigits: 2 })}`;
}

const VACIO: ContactoInput = { nombre: '', cargo: '', email: '', telefono: '', es_principal: false };

export function EmpresaDetalleDrawer({ empresa, onEditarDatos, onClose }: {
  empresa: Cliente;
  onEditarDatos: () => void;
  onClose: () => void;
}) {
  const { data: contactos } = useContactos(empresa.id);
  const { data: cxc } = useCxCCliente(empresa.id);
  const guardar = useGuardarContacto(empresa.id);
  const eliminar = useEliminarContacto(empresa.id);
  const pago = useRegistrarPago(empresa.id);

  const [editId, setEditId] = useState<number | null>(null);
  const [form, setForm] = useState<ContactoInput>(VACIO);
  const [showForm, setShowForm] = useState(false);
  const [montoPago, setMontoPago] = useState('');

  function abrirNuevo() { setEditId(null); setForm(VACIO); setShowForm(true); }
  function abrirEditar(c: Contacto) {
    setEditId(c.id);
    setForm({ nombre: c.nombre, cargo: c.cargo ?? '', email: c.email ?? '', telefono: c.telefono ?? '', es_principal: c.es_principal });
    setShowForm(true);
  }
  function guardarContacto() {
    if (!form.nombre.trim()) { toast({ kind: 'warning', title: 'El nombre es requerido' }); return; }
    guardar.mutate(
      { id: editId ?? undefined, data: { ...form, nombre: form.nombre.trim() } },
      {
        onSuccess: () => { toast({ kind: 'success', title: 'Contacto guardado' }); setShowForm(false); },
        onError: (e) => toast({ kind: 'error', title: 'No se pudo guardar', description: e.detail }),
      },
    );
  }
  function onRegistrarPago() {
    const m = parseFloat(montoPago);
    if (!Number.isFinite(m) || m <= 0) { toast({ kind: 'warning', title: 'Monto inválido' }); return; }
    pago.mutate(
      { monto: m, descripcion: 'Abono a cuenta' },
      {
        onSuccess: (r) => { toast({ kind: 'success', title: 'Pago registrado', description: `Nuevo saldo: ${fmtMoney(r.nuevo_saldo, empresa.moneda_credito)}` }); setMontoPago(''); },
        onError: (e) => toast({ kind: 'error', title: 'No se pudo registrar', description: e.detail }),
      },
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/60">
      <div className="h-full w-full max-w-2xl overflow-y-auto bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 shadow-2xl">
        <div className="sticky top-0 z-10 flex items-center justify-between px-5 py-4 border-b border-slate-200 dark:border-slate-800 bg-white/90 dark:bg-slate-900/90 backdrop-blur">
          <div>
            <h2 className="text-lg font-semibold">{empresa.nombre_empresa}</h2>
            <p className="text-xs text-slate-500">{empresa.rfc_tax_id ?? 'Sin RFC'}</p>
          </div>
          <button type="button" onClick={onClose} className="text-slate-400 hover:text-slate-600"><X className="h-5 w-5" /></button>
        </div>

        <div className="p-5 space-y-6">
          {/* Datos & crédito */}
          <section>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-500">Datos & crédito</h3>
              <Button size="sm" variant="outline" onClick={onEditarDatos}><Pencil className="h-3.5 w-3.5 mr-1" /> Editar</Button>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div><span className="text-slate-500">Crédito:</span> {fmtMoney(empresa.limite_credito, empresa.moneda_credito)}</div>
              <div><span className="text-slate-500">Saldo:</span> {fmtMoney(empresa.saldo_actual, empresa.moneda_credito)}</div>
              <div><span className="text-slate-500">Días crédito:</span> {empresa.dias_credito}</div>
              <div><span className="text-slate-500">Día corte:</span> {empresa.dia_corte ?? '—'}</div>
            </div>
          </section>

          {/* Contactos */}
          <section>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-500">Contactos</h3>
              <Button size="sm" onClick={abrirNuevo}><Plus className="h-3.5 w-3.5 mr-1" /> Agregar</Button>
            </div>
            <div className="space-y-1">
              {(contactos ?? []).map((c) => (
                <div key={c.id} className="flex items-center justify-between rounded-md border border-slate-200 dark:border-slate-800 px-3 py-2">
                  <div className="min-w-0">
                    <div className="flex items-center gap-1.5 text-sm">
                      {c.es_principal && <Star className="h-3.5 w-3.5 text-amber-500 shrink-0" />}
                      <span className="font-medium truncate">{c.nombre}</span>
                      {c.cargo && <span className="text-xs text-slate-500">· {c.cargo}</span>}
                    </div>
                    <div className="text-xs text-slate-500 truncate">{[c.email, c.telefono].filter(Boolean).join(' · ') || '—'}</div>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    <button onClick={() => abrirEditar(c)} className="p-1 text-slate-400 hover:text-cyan-500" title="Editar"><Pencil className="h-4 w-4" /></button>
                    <button onClick={() => { if (window.confirm(`¿Eliminar a ${c.nombre}?`)) eliminar.mutate(c.id); }} className="p-1 text-slate-400 hover:text-rose-500" title="Eliminar"><Trash2 className="h-4 w-4" /></button>
                  </div>
                </div>
              ))}
              {(contactos ?? []).length === 0 && <p className="text-xs text-slate-500 py-2">Sin contactos.</p>}
            </div>

            {showForm && (
              <div className="mt-3 rounded-md border border-slate-200 dark:border-slate-800 p-3 space-y-2">
                <div className="grid grid-cols-2 gap-2">
                  <Input value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} placeholder="Nombre *" />
                  <Input value={form.cargo ?? ''} onChange={(e) => setForm({ ...form, cargo: e.target.value })} placeholder="Cargo" />
                  <Input value={form.email ?? ''} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="Correo" />
                  <Input value={form.telefono ?? ''} onChange={(e) => setForm({ ...form, telefono: e.target.value })} placeholder="Teléfono" />
                </div>
                <label className="flex items-center gap-2 text-xs text-slate-500">
                  <input type="checkbox" checked={form.es_principal ?? false} onChange={(e) => setForm({ ...form, es_principal: e.target.checked })} />
                  Contacto principal
                </label>
                <div className="flex justify-end gap-2">
                  <Button size="sm" variant="ghost" onClick={() => setShowForm(false)}>Cancelar</Button>
                  <Button size="sm" onClick={guardarContacto} disabled={guardar.isPending}>Guardar</Button>
                </div>
              </div>
            )}
          </section>

          {/* Estado de cuenta / CxC */}
          <section>
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-500 mb-2">Estado de cuenta / CxC</h3>
            <div className="flex items-end gap-2 mb-3">
              <div className="flex-1">
                <label className="block text-xs text-slate-500 mb-1">Registrar pago (abono)</label>
                <Input type="number" min="0" step="0.01" value={montoPago} onChange={(e) => setMontoPago(e.target.value)} placeholder="Monto" />
              </div>
              <Button size="sm" onClick={onRegistrarPago} disabled={pago.isPending}>Registrar</Button>
            </div>
            <div className="rounded-md border border-slate-200 dark:border-slate-800 overflow-hidden">
              <table className="w-full text-xs">
                <thead className="bg-slate-100 dark:bg-slate-800 text-slate-500 uppercase">
                  <tr><th className="p-2 text-left">Folio</th><th className="p-2 text-left">Vence</th><th className="p-2 text-right">Pendiente</th><th className="p-2 text-center">Estatus</th></tr>
                </thead>
                <tbody>
                  {(cxc?.cargos ?? []).map((c) => (
                    <tr key={c.id} className="border-t border-slate-100 dark:border-slate-800">
                      <td className="p-2 font-mono">{c.folio ?? '—'}</td>
                      <td className="p-2">{c.fecha_vencimiento ? c.fecha_vencimiento.slice(0, 10) : '—'}</td>
                      <td className="p-2 text-right">{fmtMoney(c.saldo_pendiente, empresa.moneda_credito)}</td>
                      <td className="p-2 text-center">{c.estatus_pago}{c.dias_atraso > 0 ? ` (${c.dias_atraso}d)` : ''}</td>
                    </tr>
                  ))}
                  {(cxc?.cargos ?? []).length === 0 && (
                    <tr><td colSpan={4} className="p-3 text-center text-slate-500">Sin cargos abiertos.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verificar**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores TS.

- [ ] **Step 3: Commit**

```bash
git add web/src/features/clientes/components/EmpresaDetalleDrawer.tsx
git commit -m "feat(empresas): EmpresaDetalleDrawer (datos, contactos CRUD, estado de cuenta/CxC)"
```

### Task 8: Botón "Ver" en `ClientesPage` que abre el drawer

**Files:**
- Modify: `web/src/features/clientes/pages/ClientesPage.tsx`

- [ ] **Step 1: Import + estado**

Agregar el import (junto a los otros imports de componentes de la feature):
```tsx
import { EmpresaDetalleDrawer } from '../components/EmpresaDetalleDrawer';
```
Junto a los otros `useState` de la página (donde están `modalEditar`, etc.), agregar:
```tsx
  const [detalle, setDetalle] = useState<Cliente | null>(null);
```
(Si `Cliente` no está importado en el archivo, agregarlo al import de `../types`.)

- [ ] **Step 2: Botón "Ver" en la columna Acciones**

En la columna de Acciones de cada fila (donde está el botón "Editar", que hace `setModalEditar(c)`), agregar ANTES del botón Editar:
```tsx
                  <button
                    onClick={() => setDetalle(c)}
                    className="text-cyan-600 hover:text-cyan-700 dark:text-cyan-400 dark:hover:text-cyan-300 px-1.5 text-xs"
                    title="Ver empresa"
                  >
                    Ver
                  </button>
```

- [ ] **Step 3: Renderizar el drawer**

Junto a los demás modales al final del JSX de la página, agregar:
```tsx
      {detalle && (
        <EmpresaDetalleDrawer
          empresa={detalle}
          onEditarDatos={() => { setModalEditar(detalle); setDetalle(null); }}
          onClose={() => setDetalle(null)}
        />
      )}
```
(Esto reutiliza el `ClienteFormModal` de edición existente para "Editar datos": cierra el drawer y abre el modal de edición de la empresa.)

- [ ] **Step 4: Encabezado a "Empresas"**

Cambiar el título de la página de "Clientes" a "Empresas" (el `<h1>`/encabezado) y el texto del botón "+ Nuevo cliente" a "+ Nueva empresa". (Buscar esos literales en el archivo y reemplazar el texto visible; no cambiar rutas ni queryKeys.)

- [ ] **Step 5: Verificar**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores TS.

- [ ] **Step 6: Commit**

```bash
git add web/src/features/clientes/pages/ClientesPage.tsx
git commit -m "feat(empresas): ClientesPage como Empresas + botón Ver abre el detalle"
```

---

## Fase 4 — Build final + push

### Task 9: Build del SPA y push

- [ ] **Step 1: Build final**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores; `app/static/dist/` regenerado.

- [ ] **Step 2: Commit del dist + push**

```bash
git add app/static/dist
git commit -m "build: recompila SPA (dist) — área de empresas + contactos (sub-1)"
git push origin main
```

---

## Notas de verificación manual (post-deploy, recomendado)

- Tras el deploy, `seed_contactos_principal` crea un contacto principal por empresa que tenía `contacto_nombre`.
- Empresas → "Ver" una empresa → el drawer muestra datos/crédito, contactos (con el principal marcado ⭐), y estado de cuenta/CxC.
- Agregar un contacto, marcarlo principal → el contacto principal anterior se desmarca y el "contacto" de la empresa (en la tabla y el ClientPicker del cotizador) se actualiza al nuevo.
- Registrar un pago (abono) → baja el saldo y se refresca la lista de cargos.
- "Editar datos" abre el form de empresa existente.

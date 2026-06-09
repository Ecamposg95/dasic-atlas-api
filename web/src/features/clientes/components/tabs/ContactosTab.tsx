import { useState } from 'react';
import { confirm } from '@/lib/confirm';
import { useNavigate } from 'react-router-dom';
import { Plus, Star, Trash2, Pencil, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from '@/lib/toast';
import type { Contacto, ContactoInput } from '../../types';
import {
  useContactos,
  useGuardarContacto,
  useEliminarContacto,
} from '../../hooks/useEmpresaDetalle';

const VACIO: ContactoInput = { nombre: '', cargo: '', email: '', telefono: '', es_principal: false };

export function ContactosTab({ clienteId }: { clienteId: number }) {
  const navigate = useNavigate();
  const { data: contactos } = useContactos(clienteId);
  const guardar = useGuardarContacto(clienteId);
  const eliminar = useEliminarContacto(clienteId);

  const [editId, setEditId] = useState<number | null>(null);
  const [form, setForm] = useState<ContactoInput>(VACIO);
  const [showForm, setShowForm] = useState(false);

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

      {showForm && (
        <div className="mt-3 rounded-md border border-border p-3 space-y-2">
          <div className="grid grid-cols-2 gap-2">
            <Input value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} placeholder="Nombre *" />
            <Input value={form.cargo ?? ''} onChange={(e) => setForm({ ...form, cargo: e.target.value })} placeholder="Cargo" />
            <Input value={form.email ?? ''} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="Correo" />
            <Input value={form.telefono ?? ''} onChange={(e) => setForm({ ...form, telefono: e.target.value })} placeholder="Teléfono" />
          </div>
          <label className="flex items-center gap-2 text-xs text-muted-foreground">
            <input type="checkbox" checked={form.es_principal ?? false} onChange={(e) => setForm({ ...form, es_principal: e.target.checked })} />
            Contacto principal
          </label>
          <div className="flex justify-end gap-2">
            <Button size="sm" variant="ghost" onClick={() => setShowForm(false)}>Cancelar</Button>
            <Button size="sm" onClick={guardarContacto} disabled={guardar.isPending}>Guardar</Button>
          </div>
        </div>
      )}
    </div>
  );
}

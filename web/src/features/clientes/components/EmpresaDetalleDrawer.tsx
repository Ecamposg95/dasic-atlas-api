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

import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Users } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  DataTable,
  DataTableBody,
  DataTableEmpty,
  DataTableHead,
  DataTableRow,
} from '@/components/ui/data-table';
import { api } from '@/lib/api';
import { toast } from '@/lib/toast';
import { useAuth } from '@/stores/auth';
import { useClientes } from '../hooks/useClientes';
import { ClienteFormModal } from '../components/ClienteFormModal';
import type { Cliente, ClienteCreate, ClienteUpdate, MonedaCredito } from '../types';

function fmtMoney(moneda: MonedaCredito, value: number | string) {
  const n = Number(value) || 0;
  return `${moneda} $${n.toLocaleString('es-MX', { minimumFractionDigits: 2 })}`;
}

export function ClientesPage() {
  const [filtroQ, setFiltroQ] = useState('');
  const [filtroMoneda, setFiltroMoneda] = useState<MonedaCredito | ''>('');
  const [modalCrear, setModalCrear] = useState(false);
  const [modalEditar, setModalEditar] = useState<Cliente | null>(null);

  const { data: clientes, isLoading, error } = useClientes();
  const user = useAuth((s) => s.user);
  const qc = useQueryClient();

  // 401 → login
  useEffect(() => {
    const status = (error as { status?: number } | undefined)?.status;
    if (status === 401) window.location.href = '/spa/login';
  }, [error]);

  const items = clientes ?? [];

  // Filtros client-side
  const filtrados = useMemo(() => {
    const needle = filtroQ.trim().toLowerCase();
    return items.filter((c) => {
      if (filtroMoneda && c.moneda_credito !== filtroMoneda) return false;
      if (needle) {
        const hay = [c.nombre_empresa, c.rfc_tax_id ?? '', c.contacto_nombre ?? '']
          .join(' ')
          .toLowerCase();
        if (!hay.includes(needle)) return false;
      }
      return true;
    });
  }, [items, filtroQ, filtroMoneda]);

  // Mutations
  const crearMut = useMutation<Cliente, { status?: number; detail?: string }, ClienteCreate>({
    mutationFn: (body) => api.post<Cliente>('/api/clientes/', body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['clientes'] });
      toast({ kind: 'success', title: 'Cliente creado' });
      setModalCrear(false);
    },
    onError: (e) => {
      if (e.status === 401) window.location.href = '/spa/login';
      else if (e.status === 403) toast({ kind: 'error', title: 'Solo admin' });
      else toast({ kind: 'error', title: 'No se pudo crear', description: e.detail });
    },
  });

  const editarMut = useMutation<
    Cliente,
    { status?: number; detail?: string },
    { id: number; payload: ClienteUpdate }
  >({
    mutationFn: ({ id, payload }) => api.put<Cliente>(`/api/clientes/${id}`, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['clientes'] });
      toast({ kind: 'success', title: 'Cliente actualizado' });
      setModalEditar(null);
    },
    onError: (e) => {
      if (e.status === 401) window.location.href = '/spa/login';
      else if (e.status === 403) toast({ kind: 'error', title: 'Solo admin' });
      else toast({ kind: 'error', title: 'No se pudo actualizar', description: e.detail });
    },
  });

  const eliminarMut = useMutation<void, { status?: number; detail?: string }, number>({
    mutationFn: (id) => api.delete<void>(`/api/clientes/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['clientes'] });
      toast({ kind: 'success', title: 'Cliente eliminado' });
    },
    onError: (e) => {
      if (e.status === 401) window.location.href = '/spa/login';
      else if (e.status === 403) toast({ kind: 'error', title: 'Solo admin', description: 'Solo admin/asistente puede eliminar.' });
      else toast({ kind: 'error', title: 'No se pudo eliminar', description: e.detail });
    },
  });

  function onEliminar(c: Cliente) {
    if (window.confirm(`¿Eliminar al cliente "${c.nombre_empresa}"? Esta acción no se puede deshacer.`)) {
      eliminarMut.mutate(c.id);
    }
  }

  const isAdmin =
    user?.rol === 'ADMINISTRADOR' ||
    user?.rol === 'ADMIN' ||
    user?.rol === 'ASISTENTE';

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-4">
      <header className="flex items-center justify-between gap-2 flex-wrap">
        <h1 className="text-2xl font-semibold flex items-center gap-2">
          <Users className="h-5 w-5 text-cyan-400" /> Clientes
        </h1>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">{filtrados.length} cliente(s)</span>
          <Button size="sm" onClick={() => setModalCrear(true)}>
            + Nuevo cliente
          </Button>
        </div>
      </header>

      {/* Filtros */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 flex flex-wrap items-center gap-2">
        <Input
          value={filtroQ}
          onChange={(e) => setFiltroQ(e.target.value)}
          placeholder="Buscar empresa, RFC, contacto…"
          className="flex-1 min-w-[220px]"
        />
        <select
          value={filtroMoneda}
          onChange={(e) => setFiltroMoneda(e.target.value as MonedaCredito | '')}
          className="h-10 rounded-md border border-slate-700 bg-slate-900 px-3 text-sm"
        >
          <option value="">Cualquier moneda</option>
          <option value="MXN">MXN</option>
          <option value="USD">USD</option>
        </select>
        {(filtroQ || filtroMoneda) && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => { setFiltroQ(''); setFiltroMoneda(''); }}
          >
            Limpiar
          </Button>
        )}
      </div>

      {/* Tabla */}
      <DataTable>
        <DataTableHead>
          <tr>
            <th className="p-3 text-left">Empresa</th>
            <th className="p-3 text-left">Contacto</th>
            <th className="p-3 text-left">RFC</th>
            <th className="p-3 text-left">Teléfono</th>
            <th className="p-3 text-left">Email</th>
            <th className="p-3 text-right">Crédito</th>
            <th className="p-3 text-right">Saldo</th>
            <th className="p-3 text-right">Acciones</th>
          </tr>
        </DataTableHead>
        <DataTableBody>
          {isLoading && (
            <DataTableEmpty colSpan={8}>Cargando clientes…</DataTableEmpty>
          )}
          {!isLoading && filtrados.length === 0 && (
            <DataTableEmpty colSpan={8}>
              <Users className="h-8 w-8 mx-auto text-slate-700 mb-2" />
              {items.length === 0 ? 'Sin clientes registrados' : 'Sin coincidencias con la búsqueda'}
            </DataTableEmpty>
          )}
          {filtrados.map((c) => {
            const saldo = Number(c.saldo_actual) || 0;
            return (
              <DataTableRow key={c.id}>
                <td className="p-3">
                  <div className="font-medium text-slate-200 truncate max-w-[180px]" title={c.nombre_empresa}>
                    {c.nombre_empresa}
                  </div>
                </td>
                <td className="p-3 text-slate-400 text-xs">
                  {c.contacto_nombre || <span className="text-slate-600">—</span>}
                </td>
                <td className="p-3 font-mono text-xs text-slate-400">
                  {c.rfc_tax_id || <span className="text-slate-600">—</span>}
                </td>
                <td className="p-3 text-xs text-slate-400">
                  {c.telefono || <span className="text-slate-600">—</span>}
                </td>
                <td className="p-3 text-xs text-slate-400 truncate max-w-[140px]">
                  {c.email || <span className="text-slate-600">—</span>}
                </td>
                <td className="p-3 text-right whitespace-nowrap">
                  <Badge variant="cyan">
                    {fmtMoney(c.moneda_credito, c.limite_credito)}
                  </Badge>
                  {c.dias_credito > 0 && (
                    <span className="ml-1 text-[10px] text-slate-500">{c.dias_credito}d</span>
                  )}
                </td>
                <td className="p-3 text-right whitespace-nowrap">
                  {saldo > 0 ? (
                    <Badge variant="rose">{fmtMoney(c.moneda_credito, c.saldo_actual)}</Badge>
                  ) : (
                    <span className="text-xs text-slate-600">
                      {fmtMoney(c.moneda_credito, c.saldo_actual)}
                    </span>
                  )}
                </td>
                <td className="p-3 text-right whitespace-nowrap">
                  <button
                    onClick={() => setModalEditar(c)}
                    title="Editar"
                    className="text-slate-300 hover:text-slate-100 px-1.5 text-xs"
                  >
                    Editar
                  </button>
                  {isAdmin && (
                    <button
                      onClick={() => onEliminar(c)}
                      title="Eliminar"
                      className="text-rose-400 hover:text-rose-300 px-1.5 text-xs"
                      disabled={eliminarMut.isPending}
                    >
                      Eliminar
                    </button>
                  )}
                </td>
              </DataTableRow>
            );
          })}
        </DataTableBody>
      </DataTable>

      {/* Modal crear */}
      {modalCrear && (
        <ClienteFormModal
          mode="create"
          onSave={(data) => crearMut.mutate(data)}
          onClose={() => setModalCrear(false)}
          busy={crearMut.isPending}
        />
      )}

      {/* Modal editar */}
      {modalEditar && (
        <ClienteFormModal
          mode="edit"
          cliente={modalEditar}
          onSave={(data) => editarMut.mutate({ id: modalEditar.id, payload: data })}
          onClose={() => setModalEditar(null)}
          busy={editarMut.isPending}
        />
      )}
    </div>
  );
}

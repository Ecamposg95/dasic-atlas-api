import { useEffect, useRef, useState } from 'react';
import { confirm } from '@/lib/confirm';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { ChevronLeft, ChevronRight, Users } from 'lucide-react';
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
import { useIsAdmin } from '@/lib/permissions';
import { useClientes } from '../hooks/useClientes';
import { useDuplicados } from '../hooks/useDuplicados';
import { ClienteFormModal } from '../components/ClienteFormModal';
import { EmpresaDetalleDrawer } from '../components/EmpresaDetalleDrawer';
import type { Cliente, ClienteCreate, ClienteUpdate, MonedaCredito } from '../types';

const PAGE_SIZE = 50;

// Debounce helper
function useDebounced<T>(value: T, delay = 300): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return debounced;
}

function fmtMoney(moneda: MonedaCredito, value: number | string) {
  const n = Number(value) || 0;
  const amount = `$${n.toLocaleString('es-MX', { minimumFractionDigits: 2 })}`;
  // El prefijo MXN es ruido en el directorio; solo se muestra el código si NO es MXN.
  return moneda && moneda !== 'MXN' ? `${moneda} ${amount}` : amount;
}

export function ClientesPage() {
  const [filtroQ, setFiltroQ] = useState('');
  const [page, setPage] = useState(1);
  const [modalCrear, setModalCrear] = useState(false);
  const [modalEditar, setModalEditar] = useState<Cliente | null>(null);
  const [detalle, setDetalle] = useState<Cliente | null>(null);

  const navigate = useNavigate();
  const { data: dups } = useDuplicados();
  const dupCount = dups?.length ?? 0;

  const filtroQDebounced = useDebounced(filtroQ);

  // Reset page when search changes
  const prevQ = useRef(filtroQDebounced);
  useEffect(() => {
    if (prevQ.current !== filtroQDebounced) {
      setPage(1);
      prevQ.current = filtroQDebounced;
    }
  }, [filtroQDebounced]);

  const { data: clientes, isLoading, isPlaceholderData, error } = useClientes(page, filtroQDebounced);
  const qc = useQueryClient();

  // 401 → login
  useEffect(() => {
    const status = (error as { status?: number } | undefined)?.status;
    if (status === 401) window.location.href = '/spa/login';
  }, [error]);

  const filtrados = clientes ?? [];

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

  async function onEliminar(c: Cliente) {
    if (await confirm({ mensaje: `¿Eliminar al cliente "${c.nombre_empresa}"? Esta acción no se puede deshacer.`, tono: 'danger' })) {
      eliminarMut.mutate(c.id);
    }
  }

  const isAdmin = useIsAdmin();

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-4">
      <header className="flex items-center justify-between gap-2 flex-wrap">
        <h1 className="text-2xl font-semibold flex items-center gap-2">
          <Users className="h-5 w-5 text-cyan-400" /> Empresas
        </h1>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">{filtrados.length} empresa(s){page > 1 ? ` — p. ${page}` : ''}</span>
          {isAdmin && dupCount > 0 && (
            <Button size="sm" variant="outline" onClick={() => navigate('/spa/empresas-unificar')}>
              Unificar duplicados ({dupCount})
            </Button>
          )}
          <Button size="sm" onClick={() => setModalCrear(true)}>
            + Nueva empresa
          </Button>
        </div>
      </header>

      {/* Filtros */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-3 flex flex-wrap items-center gap-2">
        <Input
          value={filtroQ}
          onChange={(e) => setFiltroQ(e.target.value)}
          placeholder="Buscar empresa, RFC, contacto…"
          className="flex-1 w-full sm:w-auto sm:min-w-[220px]"
        />
        {filtroQ && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setFiltroQ('')}
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
            <th className="p-2 text-center">Contactos</th>
            <th className="p-3 text-right">Crédito</th>
            <th className="p-3 text-right">Saldo</th>
            <th className="p-3 text-right">Acciones</th>
          </tr>
        </DataTableHead>
        <DataTableBody>
          {isLoading && (
            <DataTableEmpty colSpan={9}>Cargando clientes…</DataTableEmpty>
          )}
          {!isLoading && filtrados.length === 0 && (
            <DataTableEmpty colSpan={9}>
              <Users className="h-8 w-8 mx-auto text-slate-300 dark:text-slate-700 mb-2" />
              {filtroQDebounced ? 'Sin coincidencias con la búsqueda' : 'Sin clientes registrados'}
            </DataTableEmpty>
          )}
          {filtrados.map((c) => {
            const saldo = Number(c.saldo_actual) || 0;
            return (
              <DataTableRow key={c.id}>
                <td className="p-3">
                  <div className="font-medium text-slate-800 dark:text-slate-200 truncate max-w-[180px]" title={c.nombre_empresa}>
                    {c.nombre_empresa}
                  </div>
                </td>
                <td className="p-3 text-slate-600 dark:text-slate-400 text-xs">
                  {c.contacto_nombre || <span className="text-slate-400 dark:text-slate-600">—</span>}
                </td>
                <td className="p-3 font-mono text-xs text-slate-600 dark:text-slate-400">
                  {c.rfc_tax_id || <span className="text-slate-400 dark:text-slate-600">—</span>}
                </td>
                <td className="p-3 text-xs text-slate-600 dark:text-slate-400">
                  {c.telefono || <span className="text-slate-400 dark:text-slate-600">—</span>}
                </td>
                <td className="p-3 text-xs text-slate-600 dark:text-slate-400 truncate max-w-[140px]">
                  {c.email || <span className="text-slate-400 dark:text-slate-600">—</span>}
                </td>
                <td className="p-2 text-center"><Badge variant="slate">{c.n_contactos ?? 0}</Badge></td>
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
                    <span className="text-xs text-slate-400 dark:text-slate-600">
                      {fmtMoney(c.moneda_credito, c.saldo_actual)}
                    </span>
                  )}
                </td>
                <td className="p-3 text-right whitespace-nowrap">
                  <button
                    onClick={() => setDetalle(c)}
                    className="text-cyan-600 hover:text-cyan-700 dark:text-cyan-400 dark:hover:text-cyan-300 px-1.5 text-xs"
                    title="Ver empresa"
                  >
                    Ver
                  </button>
                  <button
                    onClick={() => setModalEditar(c)}
                    title="Editar"
                    className="text-slate-700 hover:text-slate-900 dark:text-slate-300 dark:hover:text-slate-100 px-1.5 text-xs"
                  >
                    Editar
                  </button>
                  {isAdmin && (
                    <button
                      onClick={() => onEliminar(c)}
                      title="Eliminar"
                      className="text-rose-600 hover:text-rose-700 dark:text-rose-400 dark:hover:text-rose-300 px-1.5 text-xs"
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

      {/* Paginación */}
      {(page > 1 || filtrados.length === PAGE_SIZE) && (
        <div className={`flex items-center justify-between text-sm text-slate-600 dark:text-slate-400 ${isPlaceholderData ? 'opacity-50' : ''}`}>
          <Button variant="outline" size="sm" disabled={page <= 1 || isPlaceholderData} onClick={() => setPage((p) => Math.max(1, p - 1))}>
            <ChevronLeft className="h-4 w-4 mr-1" /> Anterior
          </Button>
          <span>Página {page}{filtrados.length === PAGE_SIZE ? ' — hay más registros' : ''}</span>
          <Button variant="outline" size="sm" disabled={filtrados.length < PAGE_SIZE || isPlaceholderData} onClick={() => setPage((p) => p + 1)}>
            Siguiente <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
      )}

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

      {/* Drawer detalle empresa */}
      {detalle && (
        <EmpresaDetalleDrawer
          empresa={detalle}
          onEditarDatos={() => { setModalEditar(detalle); setDetalle(null); }}
          onClose={() => setDetalle(null)}
        />
      )}
    </div>
  );
}

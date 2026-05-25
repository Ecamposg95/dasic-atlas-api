import { useState, useEffect, useMemo } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ListChecks,
  FileText,
  Pencil,
  RefreshCw,
  CheckCircle,
  XCircle,
  Loader2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  DataTable,
  DataTableHead,
  DataTableBody,
  DataTableRow,
  DataTableEmpty,
} from '@/components/ui/data-table';
import { toast } from '@/lib/toast';
import { api, type ApiError } from '@/lib/api';
import { useHistorial } from '../hooks/useHistorial';
import type {
  HistorialItem,
  EstatusFilter,
  VencimientoFilter,
  RecotizarResult,
  ConvertirResult,
} from '../types';

// ─── helpers ──────────────────────────────────────────────────────────────────

function formatTotal(item: HistorialItem): string {
  const num = typeof item.total === 'string' ? parseFloat(item.total) : item.total;
  return `${item.moneda} $${num.toLocaleString('es-MX', { minimumFractionDigits: 2 })}`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('es-MX', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

type BadgeVariant = 'cyan' | 'amber' | 'emerald' | 'rose' | 'violet' | 'slate' | 'default';

function estatusBadge(estatus: string): { label: string; variant: BadgeVariant } {
  switch (estatus.toUpperCase()) {
    case 'COTIZACION':
      return { label: 'Cotización', variant: 'cyan' };
    case 'PENDIENTE':
      return { label: 'Pendiente de pago', variant: 'amber' };
    case 'PAGADA':
      return { label: 'Pagada', variant: 'emerald' };
    case 'CANCELADA':
      return { label: 'Cancelada', variant: 'rose' };
    default:
      return { label: estatus, variant: 'slate' };
  }
}

const ESTATUS_OPTIONS: { value: EstatusFilter; label: string }[] = [
  { value: 'TODOS', label: 'Todos los estatus' },
  { value: 'COTIZACION', label: 'Cotización' },
  { value: 'PENDIENTE', label: 'Pendiente de pago' },
  { value: 'PAGADA', label: 'Pagada' },
  { value: 'CANCELADA', label: 'Cancelada' },
];
const VENCIMIENTO_OPTIONS: { value: VencimientoFilter; label: string }[] = [
  { value: 'TODAS', label: 'Todas' },
  { value: 'vigente', label: 'Vigente' },
  { value: 'vencida', label: 'Vencida' },
  { value: 'sin_fecha', label: 'Sin fecha' },
];

// ─── RowActions ────────────────────────────────────────────────────────────────

interface RowActionsProps {
  item: HistorialItem;
  onRecotizar: (id: number) => void;
  onConvertir: (item: HistorialItem) => void;
  onCancelar: (item: HistorialItem) => void;
  loadingId: number | null;
}

function RowActions({ item, onRecotizar, onConvertir, onCancelar, loadingId }: RowActionsProps) {
  const estatus = item.estatus.toUpperCase();
  const isBusy = loadingId === item.id;

  const canEdit = estatus === 'COTIZACION';
  const canRecotizar = estatus === 'COTIZACION' || estatus === 'CANCELADA';
  const canConvertir = estatus === 'COTIZACION';
  const canCancelar = estatus === 'COTIZACION' || estatus === 'PENDIENTE';

  return (
    <div className="flex items-center gap-1">
      {/* Ver PDF */}
      <Button
        variant="ghost"
        size="icon"
        title="Ver PDF"
        className="h-7 w-7 text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
        onClick={() => window.open(`/api/ventas/${item.id}/pdf`, '_blank', 'noreferrer')}
      >
        <FileText className="h-3.5 w-3.5" />
      </Button>

      {/* Editar */}
      {canEdit && (
        <Button
          variant="ghost"
          size="icon"
          title="Editar cotización"
          className="h-7 w-7 text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
          onClick={() => {
            window.location.href = `/ventas/cotizador?edit=${item.id}`;
          }}
        >
          <Pencil className="h-3.5 w-3.5" />
        </Button>
      )}

      {/* Recotizar */}
      {canRecotizar && (
        <Button
          variant="ghost"
          size="icon"
          title="Recotizar (nueva versión)"
          className="h-7 w-7 text-slate-600 hover:text-cyan-600 dark:text-slate-400 dark:hover:text-cyan-300"
          disabled={isBusy}
          onClick={() => onRecotizar(item.id)}
        >
          {isBusy ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <RefreshCw className="h-3.5 w-3.5" />
          )}
        </Button>
      )}

      {/* Convertir a venta */}
      {canConvertir && (
        <Button
          variant="ghost"
          size="icon"
          title="Convertir a venta"
          className="h-7 w-7 text-slate-600 hover:text-emerald-600 dark:text-slate-400 dark:hover:text-emerald-300"
          disabled={isBusy}
          onClick={() => onConvertir(item)}
        >
          <CheckCircle className="h-3.5 w-3.5" />
        </Button>
      )}

      {/* Cancelar */}
      {canCancelar && (
        <Button
          variant="ghost"
          size="icon"
          title="Cancelar cotización"
          className="h-7 w-7 text-slate-600 hover:text-rose-600 dark:text-slate-400 dark:hover:text-rose-400"
          disabled={isBusy}
          onClick={() => onCancelar(item)}
        >
          <XCircle className="h-3.5 w-3.5" />
        </Button>
      )}
    </div>
  );
}

// ─── SeguimientoPage ───────────────────────────────────────────────────────────

export function SeguimientoPage() {
  const qc = useQueryClient();
  const { data: historial, isLoading, error } = useHistorial(200);

  // Filtros
  const [search, setSearch] = useState('');
  const [estatusFilter, setEstatusFilter] = useState<EstatusFilter>('TODOS');
  const [vencimientoFilter, setVencimientoFilter] = useState<VencimientoFilter>('TODAS');

  // Mutations
  const [loadingId, setLoadingId] = useState<number | null>(null);

  const recotizarMutation = useMutation<RecotizarResult, ApiError, number>({
    mutationFn: (id) => api.post<RecotizarResult>(`/api/ventas/${id}/recotizar`),
    onSuccess: (data) => {
      toast({ kind: 'success', title: `Nueva versión creada: ${data.folio}` });
      qc.invalidateQueries({ queryKey: ['ventas'] });
      window.location.href = `/ventas/cotizador?edit=${data.id}`;
    },
    onError: (err) => {
      toast({ kind: 'error', title: 'Error al recotizar', description: err.detail });
    },
    onSettled: () => setLoadingId(null),
  });

  const convertirMutation = useMutation<ConvertirResult, ApiError, number>({
    mutationFn: (id) => api.post<ConvertirResult>(`/api/ventas/${id}/convertir`),
    onSuccess: (data) => {
      toast({ kind: 'success', title: `Convertida a venta: ${data.folio_venta}` });
      qc.invalidateQueries({ queryKey: ['ventas'] });
    },
    onError: (err) => {
      toast({ kind: 'error', title: 'Error al convertir', description: err.detail });
    },
    onSettled: () => setLoadingId(null),
  });

  const cancelarMutation = useMutation<void, ApiError, number>({
    mutationFn: (id) => api.post<void>(`/api/ventas/${id}/cancelar`),
    onSuccess: () => {
      toast({ kind: 'success', title: 'Cotización cancelada' });
      qc.invalidateQueries({ queryKey: ['ventas'] });
    },
    onError: (err) => {
      toast({ kind: 'error', title: 'Error al cancelar', description: err.detail });
    },
    onSettled: () => setLoadingId(null),
  });

  // Auth redirect
  useEffect(() => {
    const status = (error as ApiError | null)?.status;
    if (status === 401) window.location.href = '/spa/login';
  }, [error]);

  // Handlers
  function handleRecotizar(id: number) {
    setLoadingId(id);
    recotizarMutation.mutate(id);
  }

  function handleConvertir(item: HistorialItem) {
    if (
      !window.confirm(
        `¿Convertir ${item.folio} a venta? Esta acción no se puede deshacer.`,
      )
    )
      return;
    setLoadingId(item.id);
    convertirMutation.mutate(item.id);
  }

  function handleCancelar(item: HistorialItem) {
    if (!window.confirm(`¿Cancelar la cotización ${item.folio}?`)) return;
    setLoadingId(item.id);
    cancelarMutation.mutate(item.id);
  }

  // Client-side filtering
  const filtered = useMemo(() => {
    if (!historial) return [];
    return historial.filter((item) => {
      // Search
      if (search.trim()) {
        const q = search.trim().toLowerCase();
        const matchFolio = item.folio.toLowerCase().includes(q);
        const matchCliente = item.cliente.toLowerCase().includes(q);
        if (!matchFolio && !matchCliente) return false;
      }

      // Estatus
      if (estatusFilter !== 'TODOS' && item.estatus.toUpperCase() !== estatusFilter) {
        return false;
      }

      // Vencimiento
      if (vencimientoFilter === 'vigente' && (item.esta_vencida || item.fecha_vencimiento === null)) {
        return false;
      }
      if (vencimientoFilter === 'vencida' && !item.esta_vencida) {
        return false;
      }
      if (vencimientoFilter === 'sin_fecha' && item.fecha_vencimiento !== null) {
        return false;
      }

      return true;
    });
  }, [historial, search, estatusFilter, vencimientoFilter]);

  // Error banner (non-401)
  const apiError = error as ApiError | null;
  const showError = !!error && apiError?.status !== 401;

  return (
    <div className="flex flex-col min-h-[calc(100vh-4rem)]">
      <div className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-4">
        {/* Header */}
        <header className="flex items-center gap-3">
          <ListChecks className="h-6 w-6 text-accent-glow" />
          <h1 className="text-2xl font-semibold">Seguimiento de cotizaciones</h1>
        </header>

        {/* Error banner */}
        {showError && (
          <div className="text-sm bg-rose-100/60 border border-rose-300 text-rose-700 dark:bg-rose-900/20 dark:border-rose-700/50 dark:text-rose-300 rounded-lg p-3">
            {apiError?.detail ?? 'Error al cargar el historial.'}
          </div>
        )}

        {/* Filtros */}
        <div className="flex flex-wrap gap-3 items-center">
          <Input
            placeholder="Buscar folio o cliente…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-64"
          />

          <select
            value={estatusFilter}
            onChange={(e) => setEstatusFilter(e.target.value as EstatusFilter)}
            className="text-sm rounded-md border border-slate-300 bg-white text-slate-900 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 px-3 py-2 focus:border-accent-glow outline-none"
          >
            {ESTATUS_OPTIONS.map(({ value, label }) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>

          <select
            value={vencimientoFilter}
            onChange={(e) => setVencimientoFilter(e.target.value as VencimientoFilter)}
            className="text-sm rounded-md border border-slate-300 bg-white text-slate-900 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 px-3 py-2 focus:border-accent-glow outline-none"
          >
            {VENCIMIENTO_OPTIONS.map(({ value, label }) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>

          {historial && (
            <span className="text-xs text-slate-500 ml-auto">
              {filtered.length} / {historial.length} registros
            </span>
          )}
        </div>

        {/* Loading */}
        {isLoading && (
          <div className="flex items-center gap-2 text-sm text-slate-600 bg-white border border-slate-200 dark:text-slate-400 dark:bg-slate-900 dark:border-slate-800 rounded-lg p-4">
            <Loader2 className="h-4 w-4 animate-spin" />
            Cargando historial…
          </div>
        )}

        {/* Tabla */}
        {!isLoading && !showError && (
          <DataTable>
            <DataTableHead>
              <tr>
                <th className="px-4 py-3 text-left">Folio</th>
                <th className="px-4 py-3 text-left">Cliente</th>
                <th className="px-4 py-3 text-left">Fecha</th>
                <th className="px-4 py-3 text-left">Vencimiento</th>
                <th className="px-4 py-3 text-right">Total</th>
                <th className="px-4 py-3 text-left">Estatus</th>
                <th className="px-4 py-3 text-left">Acciones</th>
              </tr>
            </DataTableHead>
            <DataTableBody>
              {filtered.length === 0 ? (
                <DataTableEmpty colSpan={7}>
                  {historial && historial.length > 0
                    ? 'Sin resultados para los filtros seleccionados.'
                    : 'No hay cotizaciones registradas.'}
                </DataTableEmpty>
              ) : (
                filtered.map((item) => {
                  const { label: estatusLabel, variant: estatusVariant } = estatusBadge(
                    item.estatus,
                  );
                  return (
                    <DataTableRow key={item.id}>
                      {/* Folio + badge versión */}
                      <td className="px-4 py-3">
                        <span className="font-mono text-xs text-slate-900 dark:text-slate-100">{item.folio}</span>
                        {item.version > 1 && (
                          <Badge variant="amber" className="ml-1.5">
                            v{item.version}
                          </Badge>
                        )}
                      </td>

                      {/* Cliente */}
                      <td className="px-4 py-3 text-sm text-slate-700 dark:text-slate-300 max-w-[180px] truncate">
                        {item.cliente}
                      </td>

                      {/* Fecha */}
                      <td className="px-4 py-3 text-xs text-slate-600 dark:text-slate-400 whitespace-nowrap">
                        {formatDate(item.fecha)}
                      </td>

                      {/* Vencimiento */}
                      <td className="px-4 py-3 whitespace-nowrap">
                        {item.fecha_vencimiento == null ? (
                          <span className="text-xs text-slate-400 dark:text-slate-600">—</span>
                        ) : item.esta_vencida ? (
                          <Badge variant="rose">Vencida</Badge>
                        ) : (
                          <span className="flex items-center gap-1.5">
                            <Badge variant="emerald">Vigente</Badge>
                            {item.dias_restantes !== null && (
                              <span className="text-[10px] text-slate-500">
                                {item.dias_restantes}d
                              </span>
                            )}
                          </span>
                        )}
                      </td>

                      {/* Total */}
                      <td className="px-4 py-3 text-right text-sm font-mono text-slate-900 dark:text-slate-100 whitespace-nowrap">
                        {formatTotal(item)}
                      </td>

                      {/* Estatus */}
                      <td className="px-4 py-3">
                        <Badge variant={estatusVariant}>{estatusLabel}</Badge>
                      </td>

                      {/* Acciones */}
                      <td className="px-4 py-3">
                        <RowActions
                          item={item}
                          onRecotizar={handleRecotizar}
                          onConvertir={handleConvertir}
                          onCancelar={handleCancelar}
                          loadingId={loadingId}
                        />
                      </td>
                    </DataTableRow>
                  );
                })
              )}
            </DataTableBody>
          </DataTable>
        )}
      </div>
    </div>
  );
}

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { FileClock, Play, Trash2, ChevronLeft, ChevronRight } from 'lucide-react';
import { useBorradores } from '../hooks/useBorradores';
import { api } from '@/lib/api';
import { toast } from '@/lib/toast';
import { Button } from '@/components/ui/button';
import {
  DataTable,
  DataTableHead,
  DataTableBody,
  DataTableRow,
  DataTableEmpty,
} from '@/components/ui/data-table';
import type { BorradorItem } from '../types';

const PAGE_SIZE = 50;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatDistancia(isoString: string | null): string {
  if (!isoString) return '—';
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60_000);
  if (diffMin < 1) return 'hace un momento';
  if (diffMin < 60) return `hace ${diffMin} min`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return `hace ${diffH}h`;
  const diffD = Math.floor(diffH / 24);
  if (diffD === 1) return 'hace 1 día';
  if (diffD < 30) return `hace ${diffD} días`;
  const diffM = Math.floor(diffD / 30);
  if (diffM === 1) return 'hace 1 mes';
  return `hace ${diffM} meses`;
}

function formatTotal(total: number, moneda: string): string {
  const formatted = total.toLocaleString('es-MX', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return `${moneda === 'USD' ? '$' : '$'} ${formatted} ${moneda}`;
}

// ---------------------------------------------------------------------------
// Skeleton
// ---------------------------------------------------------------------------

function SkeletonRow() {
  return (
    <tr className="border-b border-slate-200 dark:border-slate-800">
      {Array.from({ length: 5 }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded animate-pulse" />
        </td>
      ))}
    </tr>
  );
}

// ---------------------------------------------------------------------------
// Fila de borrador
// ---------------------------------------------------------------------------

interface RowProps {
  item: BorradorItem;
  onDiscard: (id: number) => void;
  isDiscarding: boolean;
}

function BorradorRow({ item, onDiscard, isDiscarding }: RowProps) {
  return (
    <DataTableRow>
      <td className="px-4 py-3 font-mono text-xs text-accent-glow">{item.folio}</td>
      <td className="px-4 py-3 text-slate-700 dark:text-slate-300">
        {item.cliente_nombre ?? <span className="text-slate-500 italic">Sin cliente</span>}
      </td>
      <td className="px-4 py-3 text-right tabular-nums">
        {formatTotal(item.total, item.moneda)}
      </td>
      <td className="px-4 py-3 text-slate-600 dark:text-slate-400 text-xs">{formatDistancia(item.actualizado_en)}</td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-2 justify-end">
          <Button
            size="sm"
            variant="secondary"
            title="Continuar editando"
            onClick={() => {
              window.location.href = `/ventas/cotizador?edit=${item.id}`;
            }}
          >
            <Play className="h-3.5 w-3.5 mr-1" />
            Continuar
          </Button>
          <Button
            size="sm"
            variant="outline"
            title="Descartar borrador"
            disabled={isDiscarding}
            onClick={() => onDiscard(item.id)}
            className="text-rose-400 border-rose-900 hover:bg-rose-950 hover:text-rose-300"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      </td>
    </DataTableRow>
  );
}

// ---------------------------------------------------------------------------
// Página principal
// ---------------------------------------------------------------------------

export function BorradoresPage() {
  const [page, setPage] = useState(1);
  const qc = useQueryClient();

  const { data, isLoading, isPlaceholderData } = useBorradores(page);

  const cancelar = useMutation({
    mutationFn: (id: number) => api.post(`/api/ventas/${id}/cancelar`),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['borradores'] });
      toast({ kind: 'success', title: 'Borrador descartado' });
    },
    onError: () => {
      toast({ kind: 'error', title: 'No se pudo descartar el borrador' });
    },
  });

  function handleDiscard(id: number) {
    if (!window.confirm('¿Descartar este borrador? La acción lo cancelará y no podrá deshacerse.')) {
      return;
    }
    cancelar.mutate(id);
  }

  const items = data?.items ?? [];
  const totalCount = items.length; // visible en página actual
  const hasMore = items.length === PAGE_SIZE;
  const hasPrev = page > 1;

  return (
    <div className="p-6 max-w-7xl mx-auto w-full space-y-6">
      {/* Header */}
      <header className="flex items-center justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-3">
          <FileClock className="h-6 w-6 text-accent-glow" />
          <h1 className="text-2xl font-semibold">Borradores de cotizaciones</h1>
          {!isLoading && (
            <span className="text-slate-500 text-sm">
              ({totalCount} {totalCount === 1 ? 'borrador' : 'borradores'}
              {page > 1 ? ` en página ${page}` : ''})
            </span>
          )}
        </div>
      </header>

      {/* Tabla */}
      <DataTable>
        <DataTableHead>
          <tr>
            <th className="px-4 py-3 text-left">Folio</th>
            <th className="px-4 py-3 text-left">Cliente</th>
            <th className="px-4 py-3 text-right">Total</th>
            <th className="px-4 py-3 text-left">Última edición</th>
            <th className="px-4 py-3 text-right">Acciones</th>
          </tr>
        </DataTableHead>
        <DataTableBody>
          {isLoading ? (
            Array.from({ length: 6 }).map((_, i) => <SkeletonRow key={i} />)
          ) : items.length === 0 ? (
            <DataTableEmpty colSpan={5}>
              <div className="flex flex-col items-center gap-2 text-slate-500">
                <FileClock className="h-10 w-10 opacity-30" />
                <p>No hay borradores pendientes</p>
                <p className="text-xs">
                  Las cotizaciones guardadas sin enviar aparecerán aquí.
                </p>
              </div>
            </DataTableEmpty>
          ) : (
            items.map((item) => (
              <BorradorRow
                key={item.id}
                item={item}
                onDiscard={handleDiscard}
                isDiscarding={cancelar.isPending && cancelar.variables === item.id}
              />
            ))
          )}
        </DataTableBody>
      </DataTable>

      {/* Paginación */}
      {(hasPrev || hasMore) && (
        <div
          className={`flex items-center justify-between text-sm text-slate-600 dark:text-slate-400 ${isPlaceholderData ? 'opacity-50' : ''}`}
        >
          <Button
            variant="outline"
            size="sm"
            disabled={!hasPrev || isPlaceholderData}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            <ChevronLeft className="h-4 w-4 mr-1" />
            Anterior
          </Button>

          <span>
            Página {page}
            {hasMore ? ' — hay más registros' : ''}
          </span>

          <Button
            variant="outline"
            size="sm"
            disabled={!hasMore || isPlaceholderData}
            onClick={() => setPage((p) => p + 1)}
          >
            Siguiente
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
      )}
    </div>
  );
}

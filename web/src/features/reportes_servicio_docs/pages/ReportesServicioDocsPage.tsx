import { useState } from 'react';
import { ClipboardCheck, ChevronLeft, ChevronRight, CheckSquare, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Modal, ModalFooter } from '@/components/ui/modal';
import {
  DataTable,
  DataTableHead,
  DataTableBody,
  DataTableRow,
  DataTableEmpty,
} from '@/components/ui/data-table';
import { toast } from '@/lib/toast';
import {
  useReportesServicioDocs,
  useRegistrarRecepcionReporte,
} from '../hooks/useReportesServicioDocs';
import type { ReporteServicioDocItem } from '../types';
import { GenerarReporteServicioModal } from '../components/GenerarReporteServicioModal';

const PAGE_SIZE = 50;

function fmtFecha(iso: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('es-MX', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

function SkeletonRow() {
  return (
    <tr className="border-b border-slate-200 dark:border-slate-800">
      {Array.from({ length: 6 }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded animate-pulse" />
        </td>
      ))}
    </tr>
  );
}

// ---------------------------------------------------------------------------
// Modal: Registrar Recepción
// ---------------------------------------------------------------------------

interface RecepcionModalProps {
  reporteId: number;
  folio: string;
  onClose: () => void;
}

function RecepcionModal({ reporteId, folio, onClose }: RecepcionModalProps) {
  const [nombre, setNombre] = useState('');
  const registrar = useRegistrarRecepcionReporte();

  function handleSubmit() {
    if (!nombre.trim()) return;
    registrar.mutate(
      { id: reporteId, cliente_recibe_nombre: nombre.trim() },
      {
        onSuccess: () => {
          toast({ kind: 'success', title: `Recepción registrada para ${folio}` });
          onClose();
        },
        onError: (err) => {
          const detail = (err as { detail?: string }).detail ?? 'Error al registrar recepción';
          toast({ kind: 'error', title: detail });
        },
      },
    );
  }

  return (
    <Modal title={`Registrar recepción — ${folio}`} onClose={onClose} size="sm">
      <div className="space-y-3">
        <div>
          <label className="block text-xs text-slate-600 dark:text-slate-400 mb-1">
            Recibido por <span className="text-rose-600 dark:text-rose-400">*</span>
          </label>
          <Input
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            placeholder="Nombre de quien recibe en cliente"
            autoFocus
          />
        </div>
      </div>
      <ModalFooter>
        <Button variant="ghost" size="sm" onClick={onClose} disabled={registrar.isPending}>
          Cancelar
        </Button>
        <Button size="sm" onClick={handleSubmit} disabled={registrar.isPending || !nombre.trim()}>
          {registrar.isPending ? 'Guardando…' : 'Confirmar recepción'}
        </Button>
      </ModalFooter>
    </Modal>
  );
}

// ---------------------------------------------------------------------------
// Fila
// ---------------------------------------------------------------------------

interface RowProps {
  item: ReporteServicioDocItem;
  onRecepcion: (id: number, folio: string) => void;
}

function ReporteRow({ item, onRecepcion }: RowProps) {
  const recibido = item.recibido_at !== null;

  return (
    <DataTableRow>
      <td className="px-4 py-3 font-mono text-xs text-accent-glow">{item.folio ?? '—'}</td>
      <td className="px-4 py-3">
        {item.orden_venta_folio ? (
          <a
            href={`/ventas/cotizador?edit=${item.orden_venta_id}`}
            className="text-accent-glow hover:underline text-xs font-mono"
          >
            {item.orden_venta_folio}
          </a>
        ) : (
          <span className="text-slate-500 italic text-xs">—</span>
        )}
      </td>
      <td className="px-4 py-3 text-slate-700 dark:text-slate-300 text-sm">
        {item.cliente_nombre ?? <span className="text-slate-500 italic">—</span>}
      </td>
      <td className="px-4 py-3 text-slate-600 dark:text-slate-400 text-xs">
        {fmtFecha(item.fecha_reporte)}
      </td>
      <td className="px-4 py-3 text-slate-700 dark:text-slate-300 text-sm">
        {item.tecnico_nombre ?? <span className="text-slate-500 italic">—</span>}
      </td>
      <td className="px-4 py-3">
        <Badge variant={recibido ? 'emerald' : 'amber'}>
          {recibido ? 'RECIBIDO' : 'PENDIENTE'}
        </Badge>
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-2 justify-end">
          <Button
            size="sm"
            variant="outline"
            title="Descargar PDF"
            onClick={() => window.open(`/api/reportes-servicio-docs/${item.id}/pdf`, '_blank', 'noreferrer')}
          >
            <Download className="h-3.5 w-3.5 mr-1" />
            PDF
          </Button>
          {!recibido && item.folio && (
            <Button
              size="sm"
              variant="outline"
              title="Registrar recepción"
              onClick={() => onRecepcion(item.id, item.folio!)}
              className="text-emerald-600 border-emerald-300 hover:bg-emerald-50 hover:text-emerald-700 dark:text-emerald-400 dark:border-emerald-900 dark:hover:bg-emerald-950 dark:hover:text-emerald-300"
            >
              <CheckSquare className="h-3.5 w-3.5 mr-1" />
              Recibir
            </Button>
          )}
        </div>
      </td>
    </DataTableRow>
  );
}

// ---------------------------------------------------------------------------
// Página principal
// ---------------------------------------------------------------------------

export function ReportesServicioDocsPage() {
  const [page, setPage] = useState(1);
  const [recepcionTarget, setRecepcionTarget] = useState<{ id: number; folio: string } | null>(null);

  const { data, isLoading, isPlaceholderData } = useReportesServicioDocs(page);

  const items = data?.items ?? [];
  const hasMore = items.length === PAGE_SIZE;
  const hasPrev = page > 1;

  return (
    <div className="p-6 max-w-7xl mx-auto w-full space-y-6">
      <header className="flex items-center justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-3">
          <ClipboardCheck className="h-6 w-6 text-accent-glow" />
          <h1 className="text-2xl font-semibold">Reportes de servicio</h1>
          {!isLoading && (
            <span className="text-slate-500 text-sm">
              ({items.length} {items.length === 1 ? 'reporte' : 'reportes'}
              {page > 1 ? ` en página ${page}` : ''})
            </span>
          )}
        </div>
        <Button
          size="sm"
          disabled
          title="Genera el reporte desde el historial de cotizaciones (tab Historial del Cotizador)"
        >
          + Nuevo reporte
        </Button>
      </header>

      <DataTable>
        <DataTableHead>
          <tr>
            <th className="px-4 py-3 text-left">Folio</th>
            <th className="px-4 py-3 text-left">Orden venta</th>
            <th className="px-4 py-3 text-left">Cliente</th>
            <th className="px-4 py-3 text-left">Fecha</th>
            <th className="px-4 py-3 text-left">Técnico</th>
            <th className="px-4 py-3 text-left">Estatus</th>
            <th className="px-4 py-3 text-right">Acciones</th>
          </tr>
        </DataTableHead>
        <DataTableBody>
          {isLoading ? (
            Array.from({ length: 6 }).map((_, i) => <SkeletonRow key={i} />)
          ) : items.length === 0 ? (
            <DataTableEmpty colSpan={7}>
              <div className="flex flex-col items-center gap-2 text-slate-500">
                <ClipboardCheck className="h-10 w-10 opacity-30" />
                <p>No hay reportes de servicio registrados</p>
                <p className="text-xs">
                  Los reportes se generan desde el Historial del Cotizador, en
                  cotizaciones con líneas de servicio.
                </p>
              </div>
            </DataTableEmpty>
          ) : (
            items.map((item) => (
              <ReporteRow
                key={item.id}
                item={item}
                onRecepcion={(id, folio) => setRecepcionTarget({ id, folio })}
              />
            ))
          )}
        </DataTableBody>
      </DataTable>

      {(hasPrev || hasMore) && (
        <div
          className={`flex items-center justify-between text-sm text-slate-600 dark:text-slate-400 ${
            isPlaceholderData ? 'opacity-50' : ''
          }`}
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

      {recepcionTarget && (
        <RecepcionModal
          reporteId={recepcionTarget.id}
          folio={recepcionTarget.folio}
          onClose={() => setRecepcionTarget(null)}
        />
      )}

      {/* Modal global escucha window event para generar desde Historial */}
      <GenerarReporteServicioModal />
    </div>
  );
}

import { useMemo, useState } from 'react';
import { confirm } from '@/lib/confirm';
import { Receipt, Pencil, Trash2 } from 'lucide-react';
import { useGastos, useCrearGasto, useEditarGasto, useEliminarGasto } from '../hooks/useGastos';
import { toast } from '@/lib/toast';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import {
  DataTable,
  DataTableHead,
  DataTableBody,
  DataTableRow,
  DataTableEmpty,
} from '@/components/ui/data-table';
import { GastoFormModal } from '../components/GastoFormModal';
import type { Gasto, GastoCreate } from '../types';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fmtMonto(monto: number, moneda: string): string {
  return `${moneda} $${monto.toLocaleString('es-MX', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function fmtFecha(iso: string): string {
  return new Date(iso).toLocaleDateString('es-MX', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

// ---------------------------------------------------------------------------
// Skeleton
// ---------------------------------------------------------------------------

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
// Fila de gasto
// ---------------------------------------------------------------------------

interface RowProps {
  item: Gasto;
  onEdit: (g: Gasto) => void;
  onDelete: (g: Gasto) => void;
  isDeleting: boolean;
}

function GastoRow({ item, onEdit, onDelete, isDeleting }: RowProps) {
  return (
    <DataTableRow>
      <td className="px-4 py-3 text-slate-600 dark:text-slate-400 text-xs">{fmtFecha(item.fecha)}</td>
      <td className="px-4 py-3 text-slate-800 dark:text-slate-200 text-sm">
        {item.descripcion ?? <span className="text-slate-500 italic">—</span>}
      </td>
      <td className="px-4 py-3">
        <Badge variant="default">{item.categoria}</Badge>
      </td>
      <td className="px-4 py-3 text-right tabular-nums text-slate-800 dark:text-slate-200 font-medium">
        {fmtMonto(item.monto, item.moneda)}
      </td>
      <td className="px-4 py-3 text-slate-500 text-xs">
        {item.usuario ?? '—'}
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-2 justify-end">
          <Button
            size="sm"
            variant="secondary"
            title="Editar gasto"
            onClick={() => onEdit(item)}
          >
            <Pencil className="h-3.5 w-3.5" />
          </Button>
          <Button
            size="sm"
            variant="outline"
            title="Eliminar gasto"
            disabled={isDeleting}
            onClick={() => onDelete(item)}
            className="text-rose-600 border-rose-300 hover:bg-rose-50 hover:text-rose-700 dark:text-rose-400 dark:border-rose-900 dark:hover:bg-rose-950 dark:hover:text-rose-300"
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

export function GastosPage() {
  const [busqueda, setBusqueda] = useState('');
  const [filtroCategoria, setFiltroCategoria] = useState('');
  const [fechaDesde, setFechaDesde] = useState('');
  const [fechaHasta, setFechaHasta] = useState('');

  const [modalMode, setModalMode] = useState<'create' | 'edit' | null>(null);
  const [editTarget, setEditTarget] = useState<Gasto | null>(null);

  const { data: gastos = [], isLoading } = useGastos();
  const crear = useCrearGasto();
  const editar = useEditarGasto();
  const eliminar = useEliminarGasto();

  // Categorías únicas derivadas de la lista
  const categorias = useMemo(
    () => Array.from(new Set(gastos.map((g) => g.categoria))).sort(),
    [gastos],
  );

  // Filtros
  const filtered = useMemo(() => {
    let list = gastos;
    if (busqueda.trim()) {
      const q = busqueda.toLowerCase();
      list = list.filter(
        (g) =>
          g.descripcion?.toLowerCase().includes(q) ||
          g.categoria.toLowerCase().includes(q),
      );
    }
    if (filtroCategoria) {
      list = list.filter((g) => g.categoria === filtroCategoria);
    }
    if (fechaDesde) {
      list = list.filter((g) => g.fecha.slice(0, 10) >= fechaDesde);
    }
    if (fechaHasta) {
      list = list.filter((g) => g.fecha.slice(0, 10) <= fechaHasta);
    }
    return list;
  }, [gastos, busqueda, filtroCategoria, fechaDesde, fechaHasta]);

  // Total de los gastos visibles (solo MXN para simplificar; USD se muestra aparte)
  const totalMXN = useMemo(
    () => filtered.filter((g) => g.moneda === 'MXN').reduce((acc, g) => acc + Number(g.monto), 0),
    [filtered],
  );
  const totalUSD = useMemo(
    () => filtered.filter((g) => g.moneda === 'USD').reduce((acc, g) => acc + Number(g.monto), 0),
    [filtered],
  );

  function handleSave(data: GastoCreate) {
    if (modalMode === 'create') {
      crear.mutate(data, {
        onSuccess: () => {
          toast({ kind: 'success', title: 'Gasto registrado' });
          setModalMode(null);
        },
        onError: (err) => {
          const detail = (err as { detail?: string }).detail ?? 'Error al registrar el gasto';
          toast({ kind: 'error', title: detail });
        },
      });
    } else if (modalMode === 'edit' && editTarget) {
      editar.mutate(
        { id: editTarget.id, payload: data },
        {
          onSuccess: () => {
            toast({ kind: 'success', title: 'Gasto actualizado' });
            setModalMode(null);
            setEditTarget(null);
          },
          onError: (err) => {
            const detail = (err as { detail?: string }).detail ?? 'Error al actualizar el gasto';
            toast({ kind: 'error', title: detail });
          },
        },
      );
    }
  }

  async function handleDelete(gasto: Gasto) {
    if (!(await confirm({ mensaje: `¿Eliminar el gasto "${gasto.descripcion ?? gasto.categoria}"? Esta acción no se puede deshacer.`, tono: 'danger' }))) return;
    eliminar.mutate(gasto.id, {
      onSuccess: () => toast({ kind: 'success', title: 'Gasto eliminado' }),
      onError: (err) => {
        const status = (err as { status?: number }).status;
        if (status === 403) {
          toast({ kind: 'error', title: 'No tienes permiso para eliminar gastos' });
        } else {
          const detail = (err as { detail?: string }).detail ?? 'Error al eliminar el gasto';
          toast({ kind: 'error', title: detail });
        }
      },
    });
  }

  function openEdit(g: Gasto) {
    setEditTarget(g);
    setModalMode('edit');
  }

  function closeModal() {
    setModalMode(null);
    setEditTarget(null);
  }

  const busy = crear.isPending || editar.isPending;

  return (
    <div className="p-6 max-w-7xl mx-auto w-full space-y-6">
      {/* Header */}
      <header className="flex items-center justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-3">
          <Receipt className="h-6 w-6 text-accent-glow" />
          <h1 className="text-2xl font-semibold">Gastos</h1>
          {!isLoading && (
            <span className="text-slate-500 text-sm">
              ({filtered.length} {filtered.length === 1 ? 'gasto' : 'gastos'})
            </span>
          )}
        </div>
        <Button size="sm" onClick={() => setModalMode('create')}>
          + Nuevo gasto
        </Button>
      </header>

      {/* Filtros */}
      <div className="flex flex-wrap gap-3">
        <Input
          className="max-w-xs"
          placeholder="Buscar concepto o categoría…"
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
        />
        <Select
          className="max-w-[180px]"
          value={filtroCategoria}
          onChange={(e) => setFiltroCategoria(e.target.value)}
        >
          <option value="">Todas las categorías</option>
          {categorias.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </Select>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-600 dark:text-slate-400">Desde</span>
          <Input
            type="date"
            className="max-w-[150px]"
            value={fechaDesde}
            onChange={(e) => setFechaDesde(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-600 dark:text-slate-400">Hasta</span>
          <Input
            type="date"
            className="max-w-[150px]"
            value={fechaHasta}
            onChange={(e) => setFechaHasta(e.target.value)}
          />
        </div>
      </div>

      {/* Tabla */}
      <DataTable>
        <DataTableHead>
          <tr>
            <th className="px-4 py-3 text-left">Fecha</th>
            <th className="px-4 py-3 text-left">Concepto</th>
            <th className="px-4 py-3 text-left">Categoría</th>
            <th className="px-4 py-3 text-right">Monto</th>
            <th className="px-4 py-3 text-left">Registrado por</th>
            <th className="px-4 py-3 text-right">Acciones</th>
          </tr>
        </DataTableHead>
        <DataTableBody>
          {isLoading ? (
            Array.from({ length: 6 }).map((_, i) => <SkeletonRow key={i} />)
          ) : filtered.length === 0 ? (
            <DataTableEmpty colSpan={6}>
              <div className="flex flex-col items-center gap-2 text-slate-500">
                <Receipt className="h-10 w-10 opacity-30" />
                <p>{gastos.length === 0 ? 'No hay gastos registrados' : 'Sin resultados para estos filtros'}</p>
              </div>
            </DataTableEmpty>
          ) : (
            filtered.map((item) => (
              <GastoRow
                key={item.id}
                item={item}
                onEdit={openEdit}
                onDelete={handleDelete}
                isDeleting={eliminar.isPending && eliminar.variables === item.id}
              />
            ))
          )}
        </DataTableBody>
      </DataTable>

      {/* Total al pie */}
      {filtered.length > 0 && (
        <footer className="flex justify-end gap-6 text-sm border-t border-slate-200 dark:border-slate-800 pt-4">
          {totalMXN > 0 && (
            <div className="text-right">
              <span className="text-slate-600 dark:text-slate-400 text-xs block">Total MXN ({filtered.filter((g) => g.moneda === 'MXN').length} gastos)</span>
              <span className="font-semibold text-slate-900 dark:text-slate-100">
                MXN ${totalMXN.toLocaleString('es-MX', { minimumFractionDigits: 2 })}
              </span>
            </div>
          )}
          {totalUSD > 0 && (
            <div className="text-right">
              <span className="text-slate-600 dark:text-slate-400 text-xs block">Total USD ({filtered.filter((g) => g.moneda === 'USD').length} gastos)</span>
              <span className="font-semibold text-slate-900 dark:text-slate-100">
                USD ${totalUSD.toLocaleString('es-MX', { minimumFractionDigits: 2 })}
              </span>
            </div>
          )}
        </footer>
      )}

      {/* Modal create/edit */}
      {modalMode && (
        <GastoFormModal
          mode={modalMode}
          gasto={modalMode === 'edit' ? editTarget ?? undefined : undefined}
          categorias={categorias}
          onSave={handleSave}
          onClose={closeModal}
          busy={busy}
        />
      )}
    </div>
  );
}

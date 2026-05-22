import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Package, Plus, Pencil, Sliders, Trash2 } from 'lucide-react';
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
import { useProductos } from '../hooks/useProductos';
import { useMarcas } from '../hooks/useMarcas';
import { useProveedores } from '../hooks/useProveedores';
import { AjusteStockModal } from '../components/AjusteStockModal';
import { ProductoFormModal } from '../components/ProductoFormModal';
import type { Producto } from '../types';

const SELECT_CLS = 'h-10 rounded-md border border-slate-700 bg-slate-900 px-2 text-sm';

function fmtMoney(n: number | undefined | null, moneda?: string) {
  if (n == null) return '—';
  return `${moneda ?? ''} $${Number(n).toLocaleString('es-MX', { minimumFractionDigits: 2 })}`;
}

function stockBadge(p: Producto) {
  if (p.es_servicio) return <Badge variant="slate">Servicio</Badge>;
  if (p.stock_actual < p.stock_minimo) {
    return <Badge variant="rose">{p.stock_actual}</Badge>;
  }
  if (p.stock_actual === p.stock_minimo) {
    return <Badge variant="amber">{p.stock_actual}</Badge>;
  }
  return <Badge variant="emerald">{p.stock_actual}</Badge>;
}

export function InventarioPage() {
  const [filtroQ, setFiltroQ] = useState('');
  const [filtroMarca, setFiltroMarca] = useState('');
  const [filtroCategoria, setFiltroCategoria] = useState('');
  const [soloBajoStock, setSoloBajoStock] = useState(false);

  const [modalNuevo, setModalNuevo] = useState(false);
  const [modalEditar, setModalEditar] = useState<Producto | null>(null);
  const [modalAjuste, setModalAjuste] = useState<Producto | null>(null);

  const { data: productos = [], isLoading, error } = useProductos();
  const { data: marcas = [] } = useMarcas();
  const { data: proveedores = [] } = useProveedores();
  const user = useAuth((s) => s.user);
  const isAdmin = user?.rol_label === 'ADMINISTRADOR' || user?.rol === 'ADMIN';

  const qc = useQueryClient();

  // 401 → login
  useEffect(() => {
    const status = (error as { status?: number } | undefined)?.status;
    if (status === 401) window.location.href = '/spa/login';
  }, [error]);

  // Categorías únicas derivadas del listado
  const categorias = useMemo(() => {
    const cats = new Set<string>();
    productos.forEach((p) => { if (p.categoria) cats.add(p.categoria); });
    return Array.from(cats).sort();
  }, [productos]);

  // Filtros client-side
  const filtrados = useMemo(() => {
    const needle = filtroQ.trim().toLowerCase();
    return productos.filter((p) => {
      if (filtroMarca && String(p.marca_id) !== filtroMarca) return false;
      if (filtroCategoria && p.categoria !== filtroCategoria) return false;
      if (soloBajoStock && (p.es_servicio || p.stock_actual >= p.stock_minimo)) return false;
      if (needle) {
        const hay = [p.sku, p.sku_comercial, p.nombre, p.marca]
          .filter(Boolean)
          .join(' ')
          .toLowerCase();
        if (!hay.includes(needle)) return false;
      }
      return true;
    });
  }, [productos, filtroQ, filtroMarca, filtroCategoria, soloBajoStock]);

  // Delete mutation
  const deleteMut = useMutation<void, { status?: number; detail?: string }, number>({
    mutationFn: (id) => api.delete<void>(`/api/productos/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['productos'] });
      toast({ kind: 'success', title: 'Producto eliminado' });
    },
    onError: (e) => {
      if (e.status === 401) { window.location.href = '/spa/login'; return; }
      if (e.status === 403) {
        toast({ kind: 'error', title: 'Solo admin', description: 'Se requiere rol administrador para eliminar.' });
        return;
      }
      toast({ kind: 'error', title: 'No se pudo eliminar', description: e.detail });
    },
  });

  function onDelete(p: Producto) {
    if (!window.confirm(`¿Eliminar "${p.nombre}"? Esta acción no se puede deshacer.`)) return;
    deleteMut.mutate(p.id);
  }

  function clearFiltros() {
    setFiltroQ('');
    setFiltroMarca('');
    setFiltroCategoria('');
    setSoloBajoStock(false);
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-4">
      {/* Header */}
      <header className="flex items-center justify-between gap-2 flex-wrap">
        <h1 className="text-2xl font-semibold flex items-center gap-2">
          <Package className="h-5 w-5 text-cyan-400" /> Inventario
        </h1>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">{filtrados.length} producto(s)</span>
          <Button size="sm" onClick={() => setModalNuevo(true)}>
            <Plus className="h-4 w-4 mr-1" /> Nuevo producto
          </Button>
        </div>
      </header>

      {/* Filtros */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 flex flex-wrap items-center gap-2">
        <Input
          value={filtroQ}
          onChange={(e) => setFiltroQ(e.target.value)}
          placeholder="Buscar SKU, nombre, marca…"
          className="flex-1 min-w-[200px]"
        />
        <select
          value={filtroMarca}
          onChange={(e) => setFiltroMarca(e.target.value)}
          className={SELECT_CLS}
        >
          <option value="">Todas las marcas</option>
          {marcas.map((m) => (
            <option key={m.id} value={String(m.id)}>{m.nombre}</option>
          ))}
        </select>
        <select
          value={filtroCategoria}
          onChange={(e) => setFiltroCategoria(e.target.value)}
          className={SELECT_CLS}
        >
          <option value="">Todas las categorías</option>
          {categorias.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
        <label className="flex items-center gap-1.5 text-sm text-slate-300 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={soloBajoStock}
            onChange={(e) => setSoloBajoStock(e.target.checked)}
            className="rounded border-slate-600 bg-slate-800"
          />
          Solo bajo stock
        </label>
        <Button variant="ghost" size="sm" onClick={clearFiltros}>
          Limpiar
        </Button>
      </div>

      {/* Tabla */}
      <DataTable>
        <DataTableHead>
          <tr>
            <th className="p-3 text-left">SKU</th>
            <th className="p-3 text-left">SKU comercial</th>
            <th className="p-3 text-left">Nombre</th>
            <th className="p-3 text-left">Marca</th>
            <th className="p-3 text-left">Categoría</th>
            <th className="p-3 text-right">Stock</th>
            {isAdmin && <th className="p-3 text-right">Costo</th>}
            <th className="p-3 text-right">Precio público</th>
            <th className="p-3 text-right">Acciones</th>
          </tr>
        </DataTableHead>
        <DataTableBody>
          {isLoading && (
            <DataTableEmpty colSpan={isAdmin ? 9 : 8}>
              Cargando inventario…
            </DataTableEmpty>
          )}
          {!isLoading && filtrados.length === 0 && (
            <DataTableEmpty colSpan={isAdmin ? 9 : 8}>
              <Package className="h-8 w-8 mx-auto text-slate-700 mb-2" />
              Sin productos que coincidan con los filtros
            </DataTableEmpty>
          )}
          {filtrados.map((p) => (
            <DataTableRow key={p.id}>
              <td className="p-3 font-mono text-xs text-slate-400">{p.sku ?? '—'}</td>
              <td className="p-3 font-mono text-xs text-slate-400">{p.sku_comercial ?? '—'}</td>
              <td className="p-3 max-w-xs">
                <div className="truncate text-slate-200 font-medium" title={p.nombre}>
                  {p.nombre}
                </div>
              </td>
              <td className="p-3 text-xs text-slate-300">{p.marca ?? '—'}</td>
              <td className="p-3 text-xs text-slate-300">{p.categoria ?? '—'}</td>
              <td className="p-3 text-right">{stockBadge(p)}</td>
              {isAdmin && (
                <td className="p-3 text-right font-mono text-xs text-slate-300">
                  {fmtMoney(p.costo_compra, p.moneda_compra)}
                </td>
              )}
              <td className="p-3 text-right font-mono text-xs text-slate-300">
                {fmtMoney(p.precio_publico)}
              </td>
              <td className="p-3 text-right whitespace-nowrap">
                <button
                  onClick={() => setModalEditar(p)}
                  title="Editar"
                  className="text-slate-300 hover:text-slate-100 px-1"
                >
                  <Pencil className="h-4 w-4 inline" />
                </button>
                {!p.es_servicio && (
                  <button
                    onClick={() => setModalAjuste(p)}
                    title="Ajustar stock"
                    className="text-cyan-400 hover:text-cyan-300 px-1"
                  >
                    <Sliders className="h-4 w-4 inline" />
                  </button>
                )}
                {isAdmin && (
                  <button
                    onClick={() => onDelete(p)}
                    title="Eliminar"
                    className="text-rose-400 hover:text-rose-300 px-1"
                    disabled={deleteMut.isPending}
                  >
                    <Trash2 className="h-4 w-4 inline" />
                  </button>
                )}
              </td>
            </DataTableRow>
          ))}
        </DataTableBody>
      </DataTable>

      {/* Modal nuevo producto */}
      {modalNuevo && (
        <ProductoFormModal
          marcas={marcas}
          proveedores={proveedores}
          onClose={() => setModalNuevo(false)}
        />
      )}

      {/* Modal editar producto */}
      {modalEditar && (
        <ProductoFormModal
          producto={modalEditar}
          marcas={marcas}
          proveedores={proveedores}
          onClose={() => setModalEditar(null)}
        />
      )}

      {/* Modal ajuste de stock */}
      {modalAjuste && (
        <AjusteStockModal
          producto={modalAjuste}
          onClose={() => setModalAjuste(null)}
        />
      )}
    </div>
  );
}

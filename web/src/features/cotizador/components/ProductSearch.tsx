import { useState, useEffect, useRef } from 'react';
import { Search, Package, Sparkles } from 'lucide-react';
import { Input } from '@/components/ui/input';
import type { ApiError } from '@/lib/api';
import { useProductosSearch } from '../hooks/useProductosSearch';
import { fetchAutoUtilidad } from '../hooks/useAutoUtilidad';
import { useCotizador } from '../store';
import type { Producto } from '../types';
import { CatalogoFiltros } from './CatalogoFiltros';

export function ProductSearch() {
  const [q, setQ] = useState('');
  const [open, setOpen] = useState(false);
  // Phase 5 (Task 5.1): filtros para el scope de búsqueda.
  // `tipo` queda fijo en 'producto' en MVP porque el store no soporta
  // servicios todavía (CatalogoFiltros muestra la tab deshabilitada).
  const [tipo, setTipo] = useState<'producto' | 'servicio'>('producto');
  const [marcaId, setMarcaId] = useState<number | null>(null);
  const [marcaNombre, setMarcaNombre] = useState<string | null>(null);
  const [categoriaNombre, setCategoriaNombre] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const addProducto = useCotizador((s) => s.addProducto);
  const { data, isLoading, error } = useProductosSearch({
    q,
    tipo,
    marca_id: marcaId,
    marca_nombre: marcaNombre,
    categoria_nombre: categoriaNombre,
  });

  const items = data?.items ?? [];
  const cantidadParseada = data?.cantidad ?? null;

  // Auth error en la búsqueda → bounce a login.
  // CotizadorPage solo redirige por errores de useCotizacionLoader; el primary
  // variant de useProductosSearch ahora burbujea 401 y lo manejamos aquí.
  useEffect(() => {
    const status = (error as unknown as ApiError | undefined)?.status;
    if (status === 401) window.location.href = '/spa/login';
  }, [error]);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      const target = e.target as Node;
      if (!inputRef.current?.parentElement?.parentElement?.contains(target)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, [open]);

  async function onSelect(p: Producto) {
    const cliente_id = useCotizador.getState().cliente_id;
    const util = await fetchAutoUtilidad(cliente_id, p.id);
    addProducto(p, cantidadParseada ?? 1, util ?? undefined);
    setQ('');
    setOpen(false);
    setTimeout(() => inputRef.current?.focus(), 0);
  }

  function fmtCost(cost: number, moneda: string) {
    return `${moneda} $${cost.toLocaleString('es-MX', { minimumFractionDigits: 2 })}`;
  }

  function stockChip(stock: number) {
    if (stock > 0) return <span className="text-[10px] bg-emerald-900/30 text-emerald-300 px-1.5 py-0.5 rounded">{stock} en stock</span>;
    if (stock === 0) return <span className="text-[10px] bg-amber-900/30 text-amber-300 px-1.5 py-0.5 rounded">Sin stock</span>;
    return <span className="text-[10px] bg-rose-900/30 text-rose-300 px-1.5 py-0.5 rounded">Stock negativo</span>;
  }

  return (
    <div className="relative">
      <CatalogoFiltros
        tipo={tipo}
        onTipoChange={setTipo}
        marcaId={marcaId}
        marcaNombre={marcaNombre}
        onMarcaChange={(id, nombre) => {
          setMarcaId(id);
          setMarcaNombre(nombre);
        }}
        categoriaNombre={categoriaNombre}
        onCategoriaChange={setCategoriaNombre}
      />
      <div className="relative">
        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
        <Input
          ref={inputRef}
          value={q}
          onChange={(e) => { setQ(e.target.value); setOpen(true); }}
          onFocus={() => setOpen(true)}
          onKeyDown={(e) => { if (e.key === 'Escape') setOpen(false); }}
          placeholder='Buscar producto (ej. "5 GV2ME14" o "rodamiento")…'
          className="pl-8"
          data-cot-search
        />
        {cantidadParseada != null && q.trim() && (
          <div className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] bg-violet-900/30 text-violet-300 px-2 py-0.5 rounded font-bold pointer-events-none flex items-center gap-1">
            <Sparkles className="h-2.5 w-2.5" /> ×{cantidadParseada}
          </div>
        )}
      </div>
      {open && (
        <div className="absolute left-0 right-0 mt-1 max-h-80 overflow-y-auto bg-slate-900 border border-slate-700 rounded-md shadow-xl z-20">
          {(items.length > 0 || isLoading) && (
            <div className="sticky top-0 z-10 bg-slate-900/95 backdrop-blur border-b border-slate-800 px-3 py-1.5 text-[10px] uppercase tracking-wider text-slate-500 flex items-center justify-between">
              <span>{isLoading ? 'Buscando…' : `${items.length} resultado(s)`}</span>
              {cantidadParseada != null && <span className="text-violet-400">Cantidad detectada: {cantidadParseada}</span>}
            </div>
          )}
          {!isLoading && items.length === 0 && (
            <div className="px-3 py-4 text-xs text-slate-500 text-center">Sin coincidencias</div>
          )}
          {items.map(({ producto: p }) => (
            <button key={p.id} type="button" onClick={() => onSelect(p)}
              className="w-full text-left px-3 py-2 hover:bg-slate-800 transition border-b border-slate-800 last:border-b-0 flex items-center gap-3">
              <Package className="h-4 w-4 text-slate-500 shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-mono text-[11px] font-bold text-accent-glow">{p.sku_comercial || p.sku}</span>
                  {p.marca && <span className="text-[10px] text-slate-500">· {p.marca}</span>}
                  {stockChip(p.stock_actual)}
                </div>
                <div className="text-xs text-slate-200 truncate">{p.nombre}</div>
              </div>
              <div className="text-[11px] text-slate-400 font-mono whitespace-nowrap">
                {fmtCost(Number(p.costo_compra ?? 0), p.moneda_compra || 'MXN')}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

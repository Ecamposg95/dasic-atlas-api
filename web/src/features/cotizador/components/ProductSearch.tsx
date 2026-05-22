import { useState, useEffect, useRef } from 'react';
import { Search, Package } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { useProductosSearch } from '../hooks/useProductosSearch';
import { useCotizador } from '../store';
import type { Producto } from '../types';

export function ProductSearch() {
  const [q, setQ] = useState('');
  const [open, setOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const addProducto = useCotizador((s) => s.addProducto);
  const { data: productos, isLoading } = useProductosSearch(q);

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

  function onSelect(p: Producto) {
    addProducto(p, 1);
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
      <div className="relative">
        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
        <Input
          ref={inputRef}
          value={q}
          onChange={(e) => { setQ(e.target.value); setOpen(true); }}
          onFocus={() => setOpen(true)}
          onKeyDown={(e) => { if (e.key === 'Escape') setOpen(false); }}
          placeholder="Buscar producto (SKU, nombre, marca)…"
          className="pl-8"
        />
      </div>
      {open && (
        <div className="absolute left-0 right-0 mt-1 max-h-80 overflow-y-auto bg-slate-900 border border-slate-700 rounded-md shadow-xl z-20">
          {isLoading && <div className="px-3 py-4 text-xs text-slate-500 text-center">Buscando…</div>}
          {!isLoading && (productos?.length ?? 0) === 0 && (
            <div className="px-3 py-4 text-xs text-slate-500 text-center">Sin coincidencias</div>
          )}
          {(productos ?? []).map((p) => (
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

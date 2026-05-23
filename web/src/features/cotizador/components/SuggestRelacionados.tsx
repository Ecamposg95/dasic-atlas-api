import { useState } from 'react';
import { Plus, Sparkles } from 'lucide-react';
import { api } from '@/lib/api';
import { toast } from '@/lib/toast';
import { useRelacionados } from '../hooks/useRelacionados';
import { fetchAutoUtilidad } from '../hooks/useAutoUtilidad';
import { useCotizador } from '../store';
import type { Producto } from '../types';

export function SuggestRelacionados() {
  const [busyId, setBusyId] = useState<number | null>(null);
  const cart = useCotizador((s) => s.cart);
  const cliente_id = useCotizador((s) => s.cliente_id);
  const addProducto = useCotizador((s) => s.addProducto);
  // Solo catálogo (fantasmas no tienen producto_id, no participan en
  // sugerencias de "Suelen ir juntos" — el endpoint no las conoce).
  const ids = cart
    .map((c) => c.producto_id)
    .filter((id): id is number => id != null);
  const { data } = useRelacionados(ids);

  if (cart.length === 0) return null;
  const idsSet = new Set(ids);
  const items = (data ?? []).filter((p) => !idsSet.has(p.producto_id)).slice(0, 5);
  if (items.length === 0) return null;

  async function onAdd(producto_id: number) {
    setBusyId(producto_id);
    try {
      // El endpoint relacionados sólo devuelve {sku, nombre, marca, stock_actual},
      // no incluye costo/moneda — fetch del producto completo antes de agregar.
      const prod = await api.get<Producto>(`/api/productos/${producto_id}`);
      const util = await fetchAutoUtilidad(cliente_id, producto_id);
      addProducto(prod, 1, util ?? undefined);
    } catch {
      toast({ kind: 'error', title: 'No se pudo agregar', description: 'El producto ya no existe en el catálogo.' });
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 mt-3">
      <div className="flex items-center gap-2 text-[10px] uppercase tracking-wider font-bold text-slate-400 mb-2">
        <Sparkles className="h-3 w-3 text-violet-400" /> Suelen ir juntos
      </div>
      <div className="flex gap-2 flex-wrap">
        {items.map((p) => (
          <button
            key={p.producto_id}
            type="button"
            disabled={busyId === p.producto_id}
            onClick={() => onAdd(p.producto_id)}
            className="text-xs px-2 py-1 rounded border border-slate-700 hover:border-accent-glow text-slate-300 hover:text-accent-glow flex items-center gap-1 transition disabled:opacity-50 disabled:cursor-wait"
            title={`Co-ocurrencia: ${p.co_apariciones} vez/veces`}
          >
            <Plus className="h-3 w-3" />
            <span className="font-mono">{p.sku || '—'}</span>
            <span className="text-slate-500 hidden md:inline">· {p.nombre.slice(0, 30)}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

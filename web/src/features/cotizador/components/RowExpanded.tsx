import { Input } from '@/components/ui/input';
import { useCotizador } from '../store';
import type { CartItem } from '../types';

export function RowExpanded({ item }: { item: CartItem }) {
  const moneda = useCotizador((s) => s.moneda);
  const updateLinea = useCotizador((s) => s.updateLinea);
  return (
    <tr className="bg-slate-900/50 border-b border-slate-800">
      <td colSpan={8} className="p-3">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-xs">
          <div>
            <label className="block text-[10px] uppercase tracking-wider text-slate-400 mb-1">
              Moneda origen
            </label>
            <select
              value={item.productCurrency}
              onChange={(e) =>
                updateLinea(item.uid, { productCurrency: e.target.value as 'MXN' | 'USD' })
              }
              className="w-full h-8 rounded border border-slate-700 bg-slate-900 px-2 text-xs"
            >
              <option value="MXN">MXN</option>
              <option value="USD">USD</option>
            </select>
            {item.productCurrency !== moneda && (
              <div className="text-[10px] text-amber-400 mt-1">Se aplica TC al guardar.</div>
            )}
          </div>
          <div>
            <label className="block text-[10px] uppercase tracking-wider text-slate-400 mb-1">
              Descuento %
            </label>
            <Input
              type="number"
              min="0"
              max="100"
              step="0.5"
              value={item.descuento}
              onChange={(e) =>
                updateLinea(item.uid, {
                  descuento: Math.min(100, Math.max(0, parseFloat(e.target.value) || 0)),
                })
              }
              className="h-8 text-xs"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-[10px] uppercase tracking-wider text-slate-400 mb-1">
              Nota / texto al cliente
            </label>
            <textarea
              value={item.observaciones_linea}
              onChange={(e) => updateLinea(item.uid, { observaciones_linea: e.target.value })}
              rows={2}
              className="w-full text-xs rounded border border-slate-700 bg-slate-900 px-2 py-1 focus:border-accent-glow outline-none resize-none"
            />
          </div>
        </div>
      </td>
    </tr>
  );
}

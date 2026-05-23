import { Truck, Coins } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { useCotizador } from '../store';
import { convertCostDOF } from '../lib/calc';
import type { CartItem } from '../types';

function fmt(n: number) {
  return n.toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function RowExpanded({ item }: { item: CartItem }) {
  const moneda = useCotizador((s) => s.moneda);
  const tc = useCotizador((s) => s.tc);
  const updateLinea = useCotizador((s) => s.updateLinea);

  const fuente =
    item.tipo_linea === 'producto_fantasma'
      ? 'capturado al crear el fantasma'
      : 'viene del catálogo del producto';

  // Costo OC (lo que Dasic le paga al proveedor): usa DOF puro (sin spread)
  // y aplica el descuento del proveedor sobre ese valor. Match exacto a
  // CotProveedor!I6 del Excel (G6 * (1 - descuento_prov)).
  // Nota: en el SPA actual `item.descuento` es el descuento al cliente, no
  // al proveedor — por ahora reusamos el mismo campo (TODO: separar
  // descuento_proveedor en una iteración futura).
  const costoOcOrigen = Number(item.cost) * (1 - Number(item.descuento) / 100);
  const costoOc = convertCostDOF(
    costoOcOrigen,
    item.productCurrency,
    moneda,
    tc,
  );

  return (
    <tr className="bg-slate-900/50 border-b border-slate-800">
      <td colSpan={8} className="p-3">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-xs">
          <div>
            <label className="block text-[10px] uppercase tracking-wider text-slate-400 mb-1 flex items-center gap-1">
              <Coins className="h-2.5 w-2.5" />
              Moneda origen
            </label>
            <div
              className="h-8 px-2 rounded border border-slate-700/60 bg-slate-950/50 flex items-center font-mono text-xs text-slate-300"
              title={fuente}
            >
              {item.productCurrency}
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">{fuente}</div>
            {item.productCurrency !== moneda && (
              <div className="text-[10px] text-amber-400 mt-0.5">
                Se aplica TC automáticamente.
              </div>
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
          <div>
            <label className="block text-[10px] uppercase tracking-wider text-slate-400 mb-1 flex items-center gap-1">
              <Truck className="h-2.5 w-2.5" />
              Costo OC (DOF)
            </label>
            <div
              className="h-8 px-2 rounded border border-slate-700/60 bg-slate-950/50 flex items-center justify-end text-xs font-mono text-slate-300"
              title="Costo a tipo de cambio DOF (sin spread) — lo que se le paga al proveedor cuando se genera la OC."
            >
              {moneda} ${fmt(costoOc)}
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">
              Sin spread · descuento aplicado
            </div>
          </div>
          <div>
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

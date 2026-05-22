import { useState } from 'react';
import { MoreVertical, Pen, Trash2 } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { useCotizador } from '../store';
import { lineImporte, convertCost } from '../lib/calc';
import type { CartItem } from '../types';

function fmt(n: number) {
  return n.toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function CartRow({ item }: { item: CartItem }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const moneda = useCotizador((s) => s.moneda);
  const tc = useCotizador((s) => s.tc);
  const updateLinea = useCotizador((s) => s.updateLinea);
  const removeLinea = useCotizador((s) => s.removeLinea);

  const costoConvertido = convertCost(item.cost, item.productCurrency, moneda, tc);
  const importe = lineImporte(item, moneda, tc);
  const esOverride =
    (item.sku_original != null && item.sku !== item.sku_original) ||
    (item.nom_original != null && item.nom !== item.nom_original) ||
    (item.cost_original != null && Number(item.cost) !== Number(item.cost_original));

  function openEditModal() {
    window.dispatchEvent(new CustomEvent('cot:edit-line', { detail: { uid: item.uid } }));
    setMenuOpen(false);
  }

  return (
    <tr className="border-b border-slate-800 hover:bg-slate-800/30 transition">
      <td className="p-3 align-top max-w-md">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-mono text-xs font-bold text-accent-glow">{item.sku}</span>
          {item.productCurrency !== moneda && (
            <span className="text-[10px] font-bold border border-amber-700/50 bg-amber-900/20 text-amber-300 px-1.5 py-0.5 rounded">
              {item.productCurrency} · TC {tc}
            </span>
          )}
          {esOverride && (
            <span className="text-[10px] font-bold bg-violet-900/30 text-violet-300 px-1.5 py-0.5 rounded uppercase">
              <Pen className="inline h-2.5 w-2.5 mr-0.5" /> Editado
            </span>
          )}
        </div>
        <div className="text-xs text-slate-300 mt-0.5">{item.nom}</div>
        <textarea
          value={item.observaciones_linea}
          onChange={(e) => updateLinea(item.uid, { observaciones_linea: e.target.value })}
          placeholder="Nota / productos similares (opcional)…"
          rows={1}
          className="mt-1 w-full text-[11px] bg-transparent border border-slate-800 rounded px-2 py-1 text-slate-400 focus:border-accent-glow outline-none resize-none"
        />
      </td>
      <td className="p-3 align-top text-center w-24">
        <Input
          type="number"
          min="1"
          value={item.qty}
          onChange={(e) => updateLinea(item.uid, { qty: Math.max(1, parseInt(e.target.value) || 1) })}
          className="h-8 text-center"
        />
      </td>
      <td className="p-3 align-top text-right font-mono text-sm text-slate-300 w-32">
        ${fmt(costoConvertido)}
      </td>
      <td className="p-3 align-top text-center w-20">
        <Input
          type="number"
          min="0"
          max="99"
          value={item.utilidad}
          onChange={(e) =>
            updateLinea(item.uid, {
              utilidad: Math.min(99, Math.max(0, parseFloat(e.target.value) || 0)),
            })
          }
          className="h-8 text-center"
        />
      </td>
      <td className="p-3 align-top text-center w-20">
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
          className="h-8 text-center"
        />
      </td>
      <td className="p-3 align-top text-center w-44">
        <div className="flex items-center gap-1">
          <Input
            type="number"
            placeholder="min"
            value={item.entrega_min ?? ''}
            onChange={(e) =>
              updateLinea(item.uid, {
                entrega_min: e.target.value === '' ? null : Math.max(0, parseInt(e.target.value) || 0),
              })
            }
            className="h-8 text-center w-14"
          />
          <span className="text-slate-500">–</span>
          <Input
            type="number"
            placeholder="max"
            value={item.entrega_max ?? ''}
            onChange={(e) =>
              updateLinea(item.uid, {
                entrega_max: e.target.value === '' ? null : Math.max(0, parseInt(e.target.value) || 0),
              })
            }
            className="h-8 text-center w-14"
          />
          <select
            value={item.entrega_unidad ?? ''}
            onChange={(e) => {
              const v = e.target.value;
              const u = v === 'dias' || v === 'semanas' ? v : null;
              updateLinea(item.uid, {
                entrega_unidad: u,
                ...(u == null ? { entrega_min: null, entrega_max: null } : {}),
              });
            }}
            className="h-8 text-xs rounded border border-slate-700 bg-slate-900 px-1"
          >
            <option value="">—</option>
            <option value="dias">días</option>
            <option value="semanas">sem.</option>
          </select>
        </div>
      </td>
      <td className="p-3 align-top text-right font-mono font-bold text-sm w-32">${fmt(importe)}</td>
      <td className="p-3 align-top text-center w-10 relative">
        <button
          type="button"
          onClick={() => setMenuOpen((v) => !v)}
          className="w-8 h-8 inline-flex items-center justify-center rounded-full text-slate-400 hover:text-slate-100 hover:bg-slate-700 transition"
          aria-label="Acciones de la línea"
        >
          <MoreVertical className="h-4 w-4" />
        </button>
        {menuOpen && (
          <>
            <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
            <div className="absolute right-1 top-9 z-20 bg-slate-900 border border-slate-700 rounded-lg shadow-xl py-1 min-w-[160px] text-left">
              <button
                type="button"
                onClick={openEditModal}
                className="w-full text-left text-xs px-3 py-2 hover:bg-slate-800 text-slate-200 flex items-center gap-2"
              >
                <Pen className="h-3 w-3" /> Editar línea
              </button>
              <button
                type="button"
                onClick={() => {
                  removeLinea(item.uid);
                  setMenuOpen(false);
                }}
                className="w-full text-left text-xs px-3 py-2 hover:bg-rose-900/30 text-rose-400 flex items-center gap-2"
              >
                <Trash2 className="h-3 w-3" /> Eliminar
              </button>
            </div>
          </>
        )}
      </td>
    </tr>
  );
}

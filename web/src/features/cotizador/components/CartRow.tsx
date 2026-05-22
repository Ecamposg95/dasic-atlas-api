import { useEffect, useRef, useState } from 'react';
import { MoreVertical, Pen, Trash2, ChevronDown, ChevronUp } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { useCotizador } from '../store';
import { lineImporte, convertCost } from '../lib/calc';
import { StockBadge } from './StockBadge';
import { EntregaChip } from './EntregaChip';
import { MargenChip } from './MargenChip';
import type { CartItem } from '../types';

function fmt(n: number) {
  return n.toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function CartRow({ item, justAdded }: { item: CartItem; justAdded: boolean }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const moneda = useCotizador((s) => s.moneda);
  const tc = useCotizador((s) => s.tc);
  const expandedUids = useCotizador((s) => s.expandedUids);
  const toggleExpand = useCotizador((s) => s.toggleExpand);
  const updateLinea = useCotizador((s) => s.updateLinea);
  const removeLinea = useCotizador((s) => s.removeLinea);
  const rowRef = useRef<HTMLTableRowElement>(null);
  const expanded = expandedUids.has(item.uid);

  const costoConvertido = convertCost(item.cost, item.productCurrency, moneda, tc);
  const importe = lineImporte(item, moneda, tc);
  const esOverride =
    (item.sku_original != null && item.sku !== item.sku_original) ||
    (item.nom_original != null && item.nom !== item.nom_original) ||
    (item.cost_original != null && Number(item.cost) !== Number(item.cost_original));

  useEffect(() => {
    if (justAdded && rowRef.current) {
      const el = rowRef.current;
      el.classList.add('cot-row-in');
      const t = setTimeout(() => el.classList.remove('cot-row-in'), 400);
      return () => clearTimeout(t);
    }
  }, [justAdded]);

  function openEditModal() {
    window.dispatchEvent(new CustomEvent('cot:edit-line', { detail: { uid: item.uid } }));
    setMenuOpen(false);
  }

  return (
    <tr
      ref={rowRef}
      className="border-b border-slate-800 hover:bg-slate-800/30 transition cursor-pointer"
      onClick={(e) => {
        // No expandir cuando el click es sobre un input/select/button/textarea/anchor.
        const target = e.target as HTMLElement;
        if (target.closest('input, select, button, textarea, a')) return;
        toggleExpand(item.uid);
      }}
    >
      <td className="p-2 align-top max-w-md">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="font-mono text-[11px] font-bold text-accent-glow">{item.sku}</span>
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
          <StockBadge stock={item.max} qty={item.qty} />
        </div>
        <div className="text-[11px] text-slate-300 mt-0.5">{item.nom}</div>
        <div className="flex items-center gap-1.5 mt-1 flex-wrap">
          <EntregaChip min={item.entrega_min} max={item.entrega_max} unidad={item.entrega_unidad} />
          <MargenChip utilidad={item.utilidad} />
          <span className="text-[10px] text-slate-500 flex items-center gap-0.5">
            {expanded ? <ChevronUp className="h-2.5 w-2.5" /> : <ChevronDown className="h-2.5 w-2.5" />}
            {expanded ? 'Cerrar' : 'Detalles'}
          </span>
        </div>
      </td>
      <td className="p-2 align-top text-center w-20">
        <Input
          type="number"
          min="1"
          value={item.qty}
          onChange={(e) =>
            updateLinea(item.uid, { qty: Math.max(1, parseInt(e.target.value) || 1) })
          }
          className="h-7 text-center text-xs px-1"
        />
      </td>
      <td className="p-2 align-top text-right font-mono text-xs text-slate-300 w-28">
        ${fmt(costoConvertido)}
      </td>
      <td className="p-2 align-top text-center w-16">
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
          className="h-7 text-center text-xs px-1"
        />
      </td>
      <td className="p-2 align-top text-center w-16">
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
          className="h-7 text-center text-xs px-1"
        />
      </td>
      <td className="p-2 align-top text-center w-40">
        <div className="flex items-center gap-1">
          <Input
            type="number"
            placeholder="min"
            value={item.entrega_min ?? ''}
            onChange={(e) =>
              updateLinea(item.uid, {
                entrega_min:
                  e.target.value === '' ? null : Math.max(0, parseInt(e.target.value) || 0),
              })
            }
            className="h-7 text-center text-xs px-1 w-12"
          />
          <span className="text-slate-500 text-xs">–</span>
          <Input
            type="number"
            placeholder="max"
            value={item.entrega_max ?? ''}
            onChange={(e) =>
              updateLinea(item.uid, {
                entrega_max:
                  e.target.value === '' ? null : Math.max(0, parseInt(e.target.value) || 0),
              })
            }
            className="h-7 text-center text-xs px-1 w-12"
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
            className="h-7 text-[11px] rounded border border-slate-700 bg-slate-900 px-1"
          >
            <option value="">—</option>
            <option value="dias">días</option>
            <option value="semanas">sem.</option>
          </select>
        </div>
      </td>
      <td className="p-2 align-top text-right font-mono font-bold text-xs w-28">${fmt(importe)}</td>
      <td className="p-2 align-top text-center w-8 relative">
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            setMenuOpen((v) => !v);
          }}
          className="w-7 h-7 inline-flex items-center justify-center rounded-full text-slate-400 hover:text-slate-100 hover:bg-slate-700 transition"
          aria-label="Acciones de la línea"
        >
          <MoreVertical className="h-3.5 w-3.5" />
        </button>
        {menuOpen && (
          <>
            <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
            <div className="absolute right-1 top-8 z-20 bg-slate-900 border border-slate-700 rounded-lg shadow-xl py-1 min-w-[150px] text-left">
              <button
                type="button"
                onClick={openEditModal}
                className="w-full text-left text-[11px] px-2 py-1.5 hover:bg-slate-800 text-slate-200 flex items-center gap-2"
              >
                <Pen className="h-3 w-3" /> Editar línea
              </button>
              <button
                type="button"
                onClick={() => {
                  removeLinea(item.uid);
                  setMenuOpen(false);
                }}
                className="w-full text-left text-[11px] px-2 py-1.5 hover:bg-rose-900/30 text-rose-400 flex items-center gap-2"
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

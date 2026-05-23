import { Fragment, useEffect, useMemo, useRef } from 'react';
import {
  AlertTriangle,
  ShoppingCart,
  Tag,
  Hash,
  DollarSign,
  Percent,
  Truck,
  Calculator,
  Minus,
} from 'lucide-react';
import { CartRow } from './CartRow';
import { RowExpanded } from './RowExpanded';
import { useCotizador } from '../store';

export function Cart() {
  const cart = useCotizador((s) => s.cart);
  const lineasNoSoportadas = useCotizador((s) => s.lineasNoSoportadas);
  const expandedUids = useCotizador((s) => s.expandedUids);
  const seenUids = useRef<Set<string>>(new Set());

  // Compute "new since last render" during render — synchronous so children
  // see the animation flag on the same frame their row appears.
  const justAdded = useMemo(() => {
    const added = new Set<string>();
    for (const item of cart) {
      if (!seenUids.current.has(item.uid)) added.add(item.uid);
    }
    return added;
  }, [cart]);

  // Update the seen-set in an effect, AFTER children have committed.
  // (We use a normal effect — useLayoutEffect not needed because animation is
  // CSS-driven and a single frame of delay before "remembering" is harmless.)
  useEffect(() => {
    const next = new Set<string>();
    cart.forEach((c) => next.add(c.uid));
    seenUids.current = next;
  }, [cart]);

  return (
    <div className="space-y-2">
      {lineasNoSoportadas.length > 0 && (
        <div className="bg-amber-900/20 border border-amber-700/50 text-amber-200 rounded-xl p-2 text-xs flex items-start gap-2">
          <AlertTriangle className="h-3.5 w-3.5 mt-0.5 shrink-0 text-amber-400" />
          <div>
            <div className="font-semibold mb-1">
              Cotización con {lineasNoSoportadas.length} línea(s) de servicio
            </div>
            <p className="text-[11px] text-amber-300">
              Servicios capturados en el cotizador clásico se ocultan aquí para
              evitar borrarlos al guardar. Para editar la cotización con sus
              servicios, ve a{' '}
              <a
                href={`/ventas/cotizador?edit=${useCotizador.getState().editingId}`}
                className="underline"
              >
                cotizador clásico
              </a>
              . El botón Guardar está deshabilitado mientras esto sea visible.
            </p>
            <ul className="text-[11px] mt-1 list-disc list-inside text-amber-300/80">
              {lineasNoSoportadas.slice(0, 5).map((l) => (
                <li key={l.detalle_id}>
                  {l.descripcion} (x{l.cantidad})
                </li>
              ))}
              {lineasNoSoportadas.length > 5 && (
                <li>… y {lineasNoSoportadas.length - 5} más</li>
              )}
            </ul>
          </div>
        </div>
      )}

      {cart.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 border-dashed rounded-xl p-8 text-center">
          <ShoppingCart className="mx-auto h-7 w-7 text-slate-600 mb-2" />
          <div className="text-xs font-medium text-slate-300">El carrito está vacío</div>
          <p className="text-[11px] text-slate-500 mt-1">
            Busca productos arriba y agrégalos para empezar.
          </p>
        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
          <table className="w-full text-xs">
            <thead className="bg-slate-800/50 text-[10px] text-slate-400 uppercase tracking-[0.15em] sticky top-0 z-10">
              <tr>
                <th className="p-2 text-left">
                  <span className="inline-flex items-center gap-1">
                    <Tag className="h-3 w-3 text-slate-500" /> SKU / Descripción
                  </span>
                </th>
                <th className="p-2 text-center w-20">
                  <span className="inline-flex items-center gap-1">
                    <Hash className="h-3 w-3 text-slate-500" /> Cant
                  </span>
                </th>
                <th className="p-2 text-right w-28">
                  <span className="inline-flex items-center gap-1 justify-end">
                    <DollarSign className="h-3 w-3 text-slate-500" /> Costo
                  </span>
                </th>
                <th className="p-2 text-center w-16">
                  <span className="inline-flex items-center gap-1">
                    <Percent className="h-3 w-3 text-slate-500" /> Util
                  </span>
                </th>
                <th className="p-2 text-center w-16">
                  <span className="inline-flex items-center gap-1">
                    <Minus className="h-3 w-3 text-slate-500" /> Desc
                  </span>
                </th>
                <th className="p-2 text-center w-40">
                  <span className="inline-flex items-center gap-1">
                    <Truck className="h-3 w-3 text-slate-500" /> Entrega
                  </span>
                </th>
                <th className="p-2 text-right w-28">
                  <span className="inline-flex items-center gap-1 justify-end">
                    <Calculator className="h-3 w-3 text-slate-500" /> Importe
                  </span>
                </th>
                <th className="p-2 text-center w-8"></th>
              </tr>
            </thead>
            <tbody>
              {cart.map((item) => (
                <Fragment key={item.uid}>
                  <CartRow item={item} justAdded={justAdded.has(item.uid)} />
                  {expandedUids.has(item.uid) && <RowExpanded item={item} />}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

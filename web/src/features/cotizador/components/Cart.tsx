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
              Cotización con {lineasNoSoportadas.length} línea(s) no soportadas en este editor
            </div>
            <p className="text-[11px] text-amber-300">
              Líneas con formato legacy que no se pueden hidratar al cart se
              ocultan aquí para evitar borrarlas al guardar. Si necesitas
              editarlas, abre la cotización en el cotizador clásico:{' '}
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
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 border-dashed rounded-xl p-8 text-center">
          <ShoppingCart className="mx-auto h-7 w-7 text-slate-600 mb-2" />
          <div className="text-xs font-medium text-slate-700 dark:text-slate-300">El carrito está vacío</div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            Busca productos arriba y agrégalos para empezar.
          </p>
        </div>
      ) : (
        // US-004: overflow-x-auto + min-w en la tabla → en laptops chicas la
        // tabla scrollea horizontalmente en vez de aplastar/cortar columnas.
        // US-003: base text-[13px] (antes text-xs) para mejor legibilidad.
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-x-auto">
          <table className="w-full text-[13px] min-w-[680px]">
            <thead className="bg-slate-100 dark:bg-slate-800/50 text-[11px] text-slate-600 dark:text-slate-400 uppercase tracking-[0.15em] sticky top-0 z-10">
              <tr>
                <th className="p-2.5 text-left">
                  <span className="inline-flex items-center gap-1">
                    <Tag className="h-3 w-3 text-slate-500 dark:text-slate-400" /> SKU / Descripción
                  </span>
                </th>
                <th className="p-2.5 text-center w-20">
                  <span className="inline-flex items-center gap-1">
                    <Hash className="h-3 w-3 text-slate-500 dark:text-slate-400" /> Cant
                  </span>
                </th>
                <th className="p-2.5 text-right w-28">
                  <span className="inline-flex items-center gap-1 justify-end">
                    <DollarSign className="h-3 w-3 text-slate-500 dark:text-slate-400" /> Costo
                  </span>
                </th>
                <th className="p-2.5 text-center w-16">
                  <span className="inline-flex items-center gap-1">
                    <Percent className="h-3 w-3 text-slate-500 dark:text-slate-400" /> Util
                  </span>
                </th>
                <th className="p-2.5 text-center w-16">
                  <span className="inline-flex items-center gap-1">
                    <Minus className="h-3 w-3 text-slate-500 dark:text-slate-400" /> Desc
                  </span>
                </th>
                <th className="p-2.5 text-center w-40">
                  <span className="inline-flex items-center gap-1">
                    <Truck className="h-3 w-3 text-slate-500 dark:text-slate-400" /> Entrega
                  </span>
                </th>
                <th className="p-2.5 text-right w-28">
                  <span className="inline-flex items-center gap-1 justify-end">
                    <Calculator className="h-3 w-3 text-slate-500 dark:text-slate-400" /> Importe
                  </span>
                </th>
                <th className="p-2.5 text-center w-8"></th>
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

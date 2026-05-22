import { Fragment, useEffect, useMemo, useRef } from 'react';
import { AlertTriangle, ShoppingCart } from 'lucide-react';
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
    <div className="space-y-3">
      {lineasNoSoportadas.length > 0 && (
        <div className="bg-amber-900/20 border border-amber-700/50 text-amber-200 rounded-xl p-3 text-sm flex items-start gap-2">
          <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0 text-amber-400" />
          <div>
            <div className="font-semibold mb-1">
              Cotización con {lineasNoSoportadas.length} línea(s) ad-hoc no soportadas en este editor
            </div>
            <p className="text-xs text-amber-300">
              Fantasmas o servicios capturados en el cotizador clásico se ocultan aquí para evitar
              borrarlos al guardar. Para editar esta cotización con sus líneas ad-hoc, ve a{' '}
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
        <div className="bg-slate-900 border border-slate-800 border-dashed rounded-xl p-12 text-center">
          <ShoppingCart className="mx-auto h-8 w-8 text-slate-600 mb-2" />
          <div className="text-sm font-medium text-slate-300">El carrito está vacío</div>
          <p className="text-xs text-slate-500 mt-1">
            Busca productos arriba y agrégalos para empezar.
          </p>
        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-800/50 text-[10px] text-slate-400 uppercase tracking-wider sticky top-0 z-10">
              <tr>
                <th className="p-3 text-left">SKU / Descripción</th>
                <th className="p-3 text-center w-24">Cant</th>
                <th className="p-3 text-right w-32">Costo</th>
                <th className="p-3 text-center w-20">Util %</th>
                <th className="p-3 text-center w-20">Desc %</th>
                <th className="p-3 text-center w-44">Entrega</th>
                <th className="p-3 text-right w-32">Importe</th>
                <th className="p-3 text-center w-10"></th>
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

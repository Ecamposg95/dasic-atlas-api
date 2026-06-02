import { useEffect, useMemo, useState } from 'react';
import { X, Truck, AlertTriangle, Package } from 'lucide-react';
import { useCotizador } from '../store';
import { useProveedores } from '../hooks/useProveedores';
import { agruparOCs, type GrupoOC, type SubtotalPorMoneda } from '../lib/previewOC';

function fmtMoney(n: number, m: string) {
  return `${m} $${Number(n || 0).toLocaleString('es-MX', { minimumFractionDigits: 2 })}`;
}

function SubtotalesLine({ subtotales }: { subtotales: SubtotalPorMoneda[] }) {
  if (subtotales.length === 0) return <span className="text-slate-500 dark:text-slate-400">—</span>;
  return (
    <span className="font-mono text-sm text-accent-glow">
      {subtotales.map((s, i) => (
        <span key={s.moneda}>
          {i > 0 && <span className="text-slate-500 dark:text-slate-400"> · </span>}
          {fmtMoney(s.monto, s.moneda)}
        </span>
      ))}
    </span>
  );
}

/**
 * Drawer lateral derecho: muestra el desglose de OCs que NACERÁN al guardar
 * la cotización. Todo client-side: no llama al backend, proyecta desde el
 * cart actual usando `agruparOCs`.
 *
 * Se abre por `window.dispatchEvent(new CustomEvent('cot:open-preview-oc'))`.
 * Patrón visual idéntico a `DrawerBorradores`.
 */
export function PreviewOCDrawer() {
  const [open, setOpen] = useState(false);
  const cart = useCotizador((s) => s.cart);
  const { data: proveedores } = useProveedores();

  useEffect(() => {
    function onOpen() {
      setOpen(true);
    }
    window.addEventListener('cot:open-preview-oc', onOpen);
    return () => window.removeEventListener('cot:open-preview-oc', onOpen);
  }, []);

  const grupos = useMemo<GrupoOC[]>(() => agruparOCs(cart), [cart]);

  if (!open) return null;

  const provMap = new Map((proveedores ?? []).map((p) => [p.id, p.nombre_empresa]));
  const gruposConProv = grupos.filter((g) => g.proveedor_id != null);
  const grupoSinProv = grupos.find((g) => g.proveedor_id == null) ?? null;
  const isEmpty = cart.length === 0;

  return (
    <>
      <div
        className="fixed inset-0 z-40 bg-slate-100 dark:bg-slate-950/60"
        onClick={() => setOpen(false)}
      />
      <aside className="fixed right-0 top-0 bottom-0 z-50 w-full max-w-md bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col">
        <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-800">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Truck className="h-4 w-4 text-accent-glow" /> Preview OCs
          </h3>
          <button
            type="button"
            onClick={() => setOpen(false)}
            className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {isEmpty && (
            <div className="text-xs text-slate-500 dark:text-slate-400 text-center p-6 flex flex-col items-center gap-2">
              <Package className="h-8 w-8 text-slate-300 dark:text-slate-700" />
              <span>Agrega productos al carrito para ver el preview de OCs.</span>
            </div>
          )}

          {!isEmpty && (
            <>
              <div className="text-[11px] text-slate-500 dark:text-slate-400">
                Proyección al guardar la cotización: {gruposConProv.length} OC(s)
                {grupoSinProv ? ` · ${grupoSinProv.items.length} línea(s) sin proveedor` : ''}
              </div>

              {gruposConProv.map((g) => {
                const nombre =
                  g.proveedor_id != null
                    ? provMap.get(g.proveedor_id) ?? `Proveedor #${g.proveedor_id}`
                    : '—';
                return (
                  <div
                    key={g.proveedor_id ?? 'sin'}
                    className="bg-slate-100 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg p-3"
                  >
                    <div className="flex items-center justify-between mb-2 gap-2">
                      <div className="min-w-0 flex-1">
                        <div className="font-semibold text-sm truncate">{nombre}</div>
                        <div className="text-[10px] text-slate-500 dark:text-slate-400">
                          {g.items.length} línea(s)
                        </div>
                      </div>
                      <div className="text-right shrink-0">
                        <div className="text-[10px] text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                          Total
                        </div>
                        <SubtotalesLine subtotales={g.subtotales} />
                      </div>
                    </div>
                    <ul className="space-y-1 text-xs">
                      {g.items.map((it) => (
                        <li key={it.uid} className="flex items-baseline gap-2">
                          <span className="text-slate-500 dark:text-slate-400">•</span>
                          <span className="font-mono text-cyan-400 shrink-0">
                            {it.sku}
                          </span>
                          <span className="text-slate-600 dark:text-slate-400 shrink-0">×{it.qty}</span>
                          <span className="text-slate-700 dark:text-slate-300 truncate flex-1">
                            {it.nom}
                          </span>
                          <span className="font-mono text-slate-600 dark:text-slate-400 shrink-0">
                            {fmtMoney(it.cost, it.moneda)}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                );
              })}

              {grupoSinProv && (
                <div className="bg-amber-900/10 border border-amber-700/50 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-2 text-amber-300 font-semibold text-sm">
                    <AlertTriangle className="h-4 w-4" />
                    Sin proveedor ({grupoSinProv.items.length} línea
                    {grupoSinProv.items.length === 1 ? '' : 's'})
                  </div>
                  <ul className="space-y-1 text-xs text-amber-200/80">
                    {grupoSinProv.items.map((it) => (
                      <li key={it.uid} className="flex items-baseline gap-2">
                        <span className="text-amber-500/60">•</span>
                        <span className="font-mono text-amber-300 shrink-0">
                          {it.sku}
                        </span>
                        <span className="text-amber-300/70 shrink-0">×{it.qty}</span>
                        <span className="truncate flex-1">{it.nom}</span>
                      </li>
                    ))}
                  </ul>
                  <p className="text-[11px] text-amber-300/70 mt-2">
                    Asigna proveedor para que estas líneas generen OC.
                    {' '}
                    {grupoSinProv.items.some((i) => i.tipo_linea === 'producto_catalogo') && (
                      <span>
                        Productos del catálogo se heredan de
                        {' '}<code>proveedor_principal_id</code>.
                      </span>
                    )}
                  </p>
                </div>
              )}

              {gruposConProv.length === 0 && !grupoSinProv && (
                <div className="text-xs text-slate-500 dark:text-slate-400 text-center p-4">
                  No hay líneas para agrupar.
                </div>
              )}
            </>
          )}
        </div>

        <div className="p-3 border-t border-slate-200 dark:border-slate-800 text-[10px] text-slate-500 dark:text-slate-400 leading-relaxed">
          Subtotales por proveedor en moneda nativa de cada línea (sin TC, sin
          utilidad, sin descuento). El backend genera las OCs reales al usar
          "Sugerir OC" después de guardar.
        </div>
      </aside>
    </>
  );
}

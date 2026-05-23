import { useEffect, useState } from 'react';
import { Ghost, X, Building2, DollarSign, Hash, Percent } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { useCotizador } from '../store';
import { ProveedorPicker } from './ProveedorPicker';
import type { Moneda } from '../types';

/**
 * Modal para agregar una línea fantasma al cart. Escucha el evento
 * `cot:open-add-fantasma` (opcional payload `{ initialDescripcion: string }`)
 * — dispatcheado desde:
 *   - El botón "+ Fantasma" junto al ProductSearch
 *   - El estado vacío del ProductSearch ("Agregar como fantasma con este texto")
 *
 * Al guardar, llama a `store.addLineaAdhoc()` y cierra. No persiste al
 * backend aquí — la línea queda en el cart y se persiste con el flow normal
 * de Guardar cotización.
 */
export function AgregarFantasmaModal() {
  const [open, setOpen] = useState(false);
  const [descripcion, setDescripcion] = useState('');
  const [skuLibre, setSkuLibre] = useState('');
  const [costo, setCosto] = useState('0');
  const [moneda, setMoneda] = useState<Moneda>('MXN');
  const [proveedorId, setProveedorId] = useState<number | null>(null);
  const [utilidad, setUtilidad] = useState('30');
  const [qty, setQty] = useState('1');
  const [err, setErr] = useState<string | null>(null);

  const addLineaAdhoc = useCotizador((s) => s.addLineaAdhoc);
  const monedaCot = useCotizador((s) => s.moneda);

  useEffect(() => {
    function onOpen(e: Event) {
      const ce = e as CustomEvent<{ initialDescripcion?: string }>;
      setDescripcion(ce.detail?.initialDescripcion ?? '');
      setSkuLibre('');
      setCosto('0');
      setMoneda(monedaCot); // default = moneda de la cotización
      setProveedorId(null);
      setUtilidad('30');
      setQty('1');
      setErr(null);
      setOpen(true);
    }
    function onEsc(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false);
    }
    window.addEventListener('cot:open-add-fantasma', onOpen);
    document.addEventListener('keydown', onEsc);
    return () => {
      window.removeEventListener('cot:open-add-fantasma', onOpen);
      document.removeEventListener('keydown', onEsc);
    };
  }, [monedaCot]);

  function onSave() {
    setErr(null);
    const desc = descripcion.trim();
    if (!desc) { setErr('La descripción es obligatoria.'); return; }
    const c = parseFloat(costo);
    if (!Number.isFinite(c) || c <= 0) { setErr('El costo debe ser mayor a 0.'); return; }
    const q = parseInt(qty, 10);
    if (!Number.isFinite(q) || q <= 0) { setErr('La cantidad debe ser mayor a 0.'); return; }
    const u = parseFloat(utilidad);

    addLineaAdhoc({
      descripcion: desc,
      sku_libre: skuLibre.trim() || undefined,
      costo: c,
      moneda,
      proveedor_sugerido_id: proveedorId,
      utilidad: Number.isFinite(u) ? Math.max(0, Math.min(99, u)) : 30,
      qty: q,
    });
    setOpen(false);
  }

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 bg-slate-950/80 flex items-center justify-center p-4"
      onClick={(e) => { if (e.target === e.currentTarget) setOpen(false); }}
    >
      <div className="bg-slate-900 border border-amber-700/50 rounded-xl shadow-2xl max-w-xl w-full p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Ghost className="h-4 w-4 text-amber-400" />
            Agregar producto fantasma
          </h3>
          <button type="button" onClick={() => setOpen(false)} className="text-slate-400 hover:text-slate-100">
            <X className="h-4 w-4" />
          </button>
        </div>

        <p className="text-[11px] text-amber-300/80 mb-4 bg-amber-900/10 border border-amber-700/30 rounded p-2">
          Producto que no está en el catálogo (todavía). Al guardar la cotización,
          se apila en el pool de fantasmas y queda disponible para generar OC al
          proveedor que asignes aquí. Más tarde se puede "promover" a producto
          del catálogo desde el módulo Fantasmas.
        </p>

        <div className="space-y-3">
          <div>
            <label className="block text-[10px] uppercase tracking-wider text-slate-400 mb-1">
              Descripción <span className="text-rose-400">*</span>
            </label>
            <textarea
              value={descripcion}
              onChange={(e) => setDescripcion(e.target.value)}
              rows={2}
              placeholder='Ej. "Sensor inductivo M12 24VDC PNP NA marca Balluff"'
              autoFocus
              className="w-full text-sm rounded border border-slate-700 bg-slate-900 px-3 py-2 focus:border-accent-glow outline-none resize-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[10px] uppercase tracking-wider text-slate-400 mb-1 flex items-center gap-1">
                <Hash className="h-2.5 w-2.5" /> SKU libre <span className="text-slate-600 normal-case">(opcional)</span>
              </label>
              <Input
                value={skuLibre}
                onChange={(e) => setSkuLibre(e.target.value)}
                placeholder="Catalog # del proveedor"
                className="h-8 text-xs font-mono"
              />
            </div>
            <div>
              <label className="block text-[10px] uppercase tracking-wider text-slate-400 mb-1">
                Cantidad <span className="text-rose-400">*</span>
              </label>
              <Input
                type="number"
                min="1"
                value={qty}
                onChange={(e) => setQty(e.target.value)}
                className="h-8 text-xs text-right"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-[10px] uppercase tracking-wider text-slate-400 mb-1 flex items-center gap-1">
                <DollarSign className="h-2.5 w-2.5" /> Costo unit. <span className="text-rose-400">*</span>
              </label>
              <Input
                type="number"
                step="0.01"
                min="0"
                value={costo}
                onChange={(e) => setCosto(e.target.value)}
                className="h-8 text-xs text-right font-mono"
              />
            </div>
            <div>
              <label className="block text-[10px] uppercase tracking-wider text-slate-400 mb-1">Moneda costo</label>
              <select
                value={moneda}
                onChange={(e) => setMoneda(e.target.value as Moneda)}
                className="w-full h-8 rounded border border-slate-700 bg-slate-900 px-2 text-xs"
              >
                <option value="MXN">MXN</option>
                <option value="USD">USD</option>
              </select>
            </div>
            <div>
              <label className="block text-[10px] uppercase tracking-wider text-slate-400 mb-1 flex items-center gap-1">
                <Percent className="h-2.5 w-2.5" /> Utilidad %
              </label>
              <Input
                type="number"
                min="0"
                max="99"
                value={utilidad}
                onChange={(e) => setUtilidad(e.target.value)}
                className="h-8 text-xs text-right"
              />
            </div>
          </div>

          <div>
            <label className="block text-[10px] uppercase tracking-wider text-slate-400 mb-1 flex items-center gap-1">
              <Building2 className="h-2.5 w-2.5" />
              Proveedor sugerido <span className="text-slate-600 normal-case">(opcional pero recomendado)</span>
            </label>
            <ProveedorPicker value={proveedorId} onChange={setProveedorId} />
            <div className="text-[10px] text-slate-500 mt-1">
              Sin proveedor, esta línea quedará en el bucket "sin proveedor" al generar OCs.
            </div>
          </div>
        </div>

        {err && (
          <div className="mt-3 text-xs bg-rose-900/30 border border-rose-700/50 rounded px-3 py-2 text-rose-300">
            {err}
          </div>
        )}

        <div className="flex justify-end gap-2 pt-4 mt-4 border-t border-slate-800">
          <Button variant="ghost" size="sm" onClick={() => setOpen(false)}>Cancelar</Button>
          <Button size="sm" onClick={onSave} className="bg-amber-600 hover:bg-amber-700 text-white">
            <Ghost className="h-3 w-3 mr-1" /> Agregar al carrito
          </Button>
        </div>
      </div>
    </div>
  );
}

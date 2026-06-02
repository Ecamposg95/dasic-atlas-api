import { useCotizador } from '../store';
import { lineImporte, convertCostDOF, resolveDirectionalTcs } from '../lib/calc';
import { DocumentRow } from '@/components/document/DocumentRow';
import type { DocRowVM, DocRowCaps, DocRowCallbacks, DocLineTipo } from '@/components/document/types';
import type { CartItem } from '../types';

export const QUOTE_CAPS: DocRowCaps = {
  showCosto: true,
  showUtilidad: true,
  showDescuento: true,
  showEntrega: true,
  showImporte: true,
  editableQty: true,
};

function tipoVM(t: CartItem['tipo_linea']): DocLineTipo {
  if (t === 'producto_fantasma') return 'producto_fantasma';
  if (t === 'servicio_catalogo') return 'servicio_catalogo';
  return 'producto';
}

export function CartRow({ item, justAdded }: { item: CartItem; justAdded: boolean }) {
  const moneda = useCotizador((s) => s.moneda);
  const tc = useCotizador((s) => s.tc);
  const tcMnAUsd = useCotizador((s) => s.tc_mn_a_usd);
  const tcUsdAMn = useCotizador((s) => s.tc_usd_a_mn);
  const toleranciaTc = useCotizador((s) => s.tolerancia_tc);
  const expandedUids = useCotizador((s) => s.expandedUids);
  const toggleExpand = useCotizador((s) => s.toggleExpand);
  const updateLinea = useCotizador((s) => s.updateLinea);
  const removeLinea = useCotizador((s) => s.removeLinea);

  const tcs = resolveDirectionalTcs(tc, tcMnAUsd, tcUsdAMn, toleranciaTc);
  const costoOcOrigen = Number(item.cost) * (1 - Number(item.descuento_proveedor || 0) / 100);
  const costoOc = convertCostDOF(costoOcOrigen, item.productCurrency, moneda, tc);
  const importe = lineImporte(item, moneda, tcs);
  const esOverride =
    (item.sku_original != null && item.sku !== item.sku_original) ||
    (item.nom_original != null && item.nom !== item.nom_original) ||
    (item.cost_original != null && Number(item.cost) !== Number(item.cost_original));
  const esCatalogo = item.tipo_linea === 'producto_catalogo';

  const vm: DocRowVM = {
    uid: item.uid,
    tipo: tipoVM(item.tipo_linea),
    sku: item.sku,
    nom: item.nom,
    productCurrency: item.productCurrency,
    monedaDocumento: moneda,
    toleranciaTc,
    esOverride,
    stockMax: esCatalogo ? item.max : null,
    qty: item.qty,
    qtyMax: null,
    costOrigen: Number(item.cost),
    costoOc,
    utilidad: item.utilidad,
    descuento: item.descuento,
    entrega_min: item.entrega_min,
    entrega_max: item.entrega_max,
    entrega_unidad: item.entrega_unidad as 'dias' | 'semanas' | null,
    importe,
    expanded: expandedUids.has(item.uid),
  };

  const cb: DocRowCallbacks = {
    onQty: (uid, qty) => updateLinea(uid, { qty }),
    onUtilidad: (uid, v) => updateLinea(uid, { utilidad: v }),
    onDescuento: (uid, v) => updateLinea(uid, { descuento: v }),
    onEntrega: (uid, patch) => updateLinea(uid, patch),
    onRemove: (uid) => removeLinea(uid),
    onEdit: (uid) => window.dispatchEvent(new CustomEvent('cot:edit-line', { detail: { uid } })),
    onToggleExpand: (uid) => toggleExpand(uid),
  };

  return <DocumentRow vm={vm} caps={QUOTE_CAPS} cb={cb} justAdded={justAdded} />;
}

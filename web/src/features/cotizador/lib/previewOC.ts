/**
 * previewOC.ts — Proyección client-side del cart hacia "qué OCs nacerán".
 *
 * El backend `/api/ventas/{id}/sugerir-oc` solo opera contra una cot
 * ya guardada. Para que el usuario vea el desglose por proveedor DURANTE
 * la captura, replicamos la agrupación localmente:
 *
 *   1. Cada CartItem trae `proveedor_sugerido_id` (catálogo lo hereda de
 *      `Producto.proveedor_principal_id`, fantasma del modal Agregar
 *      fantasma).
 *   2. Agrupamos por proveedor_id (o `null` → "sin proveedor").
 *   3. Subtotal por bucket = sum(cost * qty) en la moneda NATIVA de cada
 *      línea, análogo a `computeTotalsPorMoneda` pero por proveedor.
 *      No mezclamos divisas: si un proveedor tiene MXN y USD, salen 2
 *      subtotales separados.
 *
 * Sin descuento ni utilidad: la OC se le paga al proveedor por costo neto,
 * no por el precio que el cliente ve.
 */

import type { CartItem, Moneda } from '../types';

export type ItemPreviewOC = {
  uid: string;
  sku: string;
  nom: string;
  qty: number;
  cost: number;
  moneda: Moneda;
  tipo_linea: 'producto_catalogo' | 'producto_fantasma';
};

export type SubtotalPorMoneda = {
  moneda: Moneda;
  monto: number;
};

export type GrupoOC = {
  // null cuando la línea no tiene proveedor sugerido → bucket especial.
  proveedor_id: number | null;
  items: ItemPreviewOC[];
  // Hasta 2 entradas (MXN, USD). Si el bucket es de un solo proveedor
  // pero combina divisas, se muestran ambas.
  subtotales: SubtotalPorMoneda[];
};

function toItemPreview(it: CartItem): ItemPreviewOC {
  // Caller (`agruparOCs`) ya filtra servicio_catalogo antes de llegar aquí,
  // así que el cast es seguro. Si en el futuro se llamara con un servicio,
  // el assert estrecharía mal — defensa: si llega servicio, lo mapeamos a
  // fantasma (no debería pasar visualmente).
  const tl =
    it.tipo_linea === 'producto_fantasma' ? ('producto_fantasma' as const) : ('producto_catalogo' as const);
  return {
    uid: it.uid,
    sku: it.sku || '—',
    nom: it.nom || '—',
    qty: Number(it.qty) || 0,
    cost: Number(it.cost) || 0,
    moneda: it.productCurrency,
    tipo_linea: tl,
  };
}

function computeSubtotales(items: ItemPreviewOC[]): SubtotalPorMoneda[] {
  let mxn = 0;
  let usd = 0;
  for (const it of items) {
    const monto = it.cost * it.qty;
    if (it.moneda === 'USD') usd += monto;
    else mxn += monto;
  }
  const out: SubtotalPorMoneda[] = [];
  if (mxn > 0) out.push({ moneda: 'MXN', monto: mxn });
  if (usd > 0) out.push({ moneda: 'USD', monto: usd });
  return out;
}

/**
 * Agrupa el cart por proveedor sugerido. Mantiene un bucket aparte para
 * líneas sin proveedor (proveedor_id === null). Preserva el orden de
 * inserción del cart dentro de cada bucket.
 *
 * El bucket "sin proveedor" siempre va al final del array (cuando existe)
 * para que el ojo del usuario vaya primero a lo accionable.
 */
export function agruparOCs(cart: CartItem[]): GrupoOC[] {
  const grupos = new Map<string, GrupoOC>();

  for (const it of cart) {
    // Servicios del catálogo no generan OC al proveedor — son trabajo interno.
    // Si se incluyeran, caerían en el bucket "sin proveedor" y confundirían al
    // usuario haciéndole creer que faltan datos.
    if (it.tipo_linea === 'servicio_catalogo') continue;
    const pid = it.proveedor_sugerido_id ?? null;
    const key = pid == null ? '__sin__' : String(pid);
    let g = grupos.get(key);
    if (!g) {
      g = { proveedor_id: pid, items: [], subtotales: [] };
      grupos.set(key, g);
    }
    g.items.push(toItemPreview(it));
  }

  for (const g of grupos.values()) {
    g.subtotales = computeSubtotales(g.items);
  }

  const conProveedor: GrupoOC[] = [];
  let sinProveedor: GrupoOC | null = null;
  for (const g of grupos.values()) {
    if (g.proveedor_id == null) sinProveedor = g;
    else conProveedor.push(g);
  }
  if (sinProveedor) conProveedor.push(sinProveedor);
  return conProveedor;
}

// Builds the POST /api/ventas and PUT /api/ventas/{id} payload from Zustand
// store state. Pure function — no side effects, no network calls.

import type { CartItem, OrdenVentaCreate } from '../types';

export type CotizadorSnapshot = {
  cliente_id: number | null;
  moneda: 'MXN' | 'USD';
  tc: number;
  fecha_creacion: string | null;     // 'YYYY-MM-DD'
  fecha_vencimiento: string | null;
  observaciones: string;
  terminos_condiciones: string;
  cart: CartItem[];
};

// Internal helpers — not exported.

function hayOverrideSku(it: CartItem): boolean {
  return it.sku_original != null && it.sku !== it.sku_original;
}

function hayOverrideNom(it: CartItem): boolean {
  return it.nom_original != null && it.nom !== it.nom_original;
}

function hayOverrideCosto(it: CartItem): boolean {
  return Number(it.cost) !== Number(it.cost_original);
}

export function buildSavePayload(s: CotizadorSnapshot): OrdenVentaCreate {
  return {
    cliente_id: s.cliente_id,
    moneda: s.moneda,
    tipo_cambio: s.tc,
    fecha_creacion: s.fecha_creacion ? `${s.fecha_creacion}T00:00:00` : null,
    fecha_vencimiento: s.fecha_vencimiento ? `${s.fecha_vencimiento}T00:00:00` : null,
    observaciones: s.observaciones || null,
    terminos_condiciones: s.terminos_condiciones || null,
    tipo: 'cotizacion',
    detalles: s.cart.map((i) => ({
      producto_id: i.producto_id,
      servicio_id: null,
      cantidad: i.qty,
      utilidad: i.utilidad,
      descuento: i.descuento,
      moneda_origen: i.productCurrency,
      sku_libre: hayOverrideSku(i) ? i.sku : null,
      descripcion_libre: hayOverrideNom(i) ? i.nom : null,
      costo_unitario: hayOverrideCosto(i) ? i.cost : null,
      tipo_linea: 'producto_catalogo' as const,
      proveedor_sugerido_id: null,
      entrega_min: i.entrega_min,
      entrega_max: i.entrega_max,
      entrega_unidad: i.entrega_unidad,
      observaciones_linea: i.observaciones_linea || null,
    })),
  };
}

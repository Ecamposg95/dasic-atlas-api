// Builds the POST /api/ventas and PUT /api/ventas/{id} payload from Zustand
// store state. Pure function — no side effects, no network calls.

import type { CartItem, OrdenVentaCreate } from '../types';

export type CotizadorSnapshot = {
  cliente_id: number | null;
  moneda: 'MXN' | 'USD';
  tc: number;                               // DOF (TC oficial Banxico)
  tc_mn_a_usd: number | null;               // override MN→USD, null = backend deriva DOF-1
  tc_usd_a_mn: number | null;               // override USD→MN, null = backend deriva DOF+1
  fecha_creacion: string | null;     // 'YYYY-MM-DD'
  fecha_vencimiento: string | null;
  observaciones: string;
  terminos_condiciones: string;
  pdf_concepto_unificado: string;
  pdf_concepto_enabled: boolean;
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
    tc_mn_a_usd: s.tc_mn_a_usd,
    tc_usd_a_mn: s.tc_usd_a_mn,
    fecha_creacion: s.fecha_creacion ? `${s.fecha_creacion}T00:00:00` : null,
    fecha_vencimiento: s.fecha_vencimiento ? `${s.fecha_vencimiento}T00:00:00` : null,
    observaciones: s.observaciones || null,
    terminos_condiciones: s.terminos_condiciones || null,
    tipo: 'cotizacion',
    // Sólo persistimos el texto si la opción está habilitada; si no, mandamos
    // null para que el backend (cuando lo soporte) sepa que es un toggle off.
    pdf_concepto_unificado: s.pdf_concepto_enabled
      ? (s.pdf_concepto_unificado || null)
      : null,
    pdf_concepto_enabled: s.pdf_concepto_enabled,
    detalles: s.cart.map((i) => {
      if (i.tipo_linea === 'producto_fantasma') {
        // Fantasmas: producto_id NULL, sku/descripcion/costo SIEMPRE explícitos
        // (no hay catálogo del cual derivarlos). proveedor_sugerido_id va
        // adelante para que la línea cuente en sugerir-oc.
        return {
          producto_id: null,
          servicio_id: null,
          cantidad: i.qty,
          utilidad: i.utilidad,
          descuento: i.descuento,
          moneda_origen: i.productCurrency,
          sku_libre: i.sku && i.sku !== '—' ? i.sku : null,
          descripcion_libre: i.nom,
          costo_unitario: i.cost,
          tipo_linea: 'producto_fantasma' as const,
          proveedor_sugerido_id: i.proveedor_sugerido_id ?? null,
          entrega_min: i.entrega_min,
          entrega_max: i.entrega_max,
          entrega_unidad: i.entrega_unidad,
          observaciones_linea: i.observaciones_linea || null,
        };
      }
      // Catálogo (default): producto_id set, libres solo si override.
      return {
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
      };
    }),
  };
}

/**
 * calc.ts — Pricing utilities for the cotizador live preview.
 *
 * Modelo TC Excel V_03 (2026-05-23): hay 2 TCs efectivos por dirección,
 * más el DOF (oficial Banxico) que se usa solo para la OC al proveedor.
 *
 *   - tc_dof:       TC oficial Banxico (lo que llena el usuario)
 *   - tc_mn_a_usd:  TC efectivo cuando convertir MN → USD (default DOF - 1)
 *   - tc_usd_a_mn:  TC efectivo cuando convertir USD → MN (default DOF + 1)
 *
 * El spread de ±1 peso cubre riesgo cambiario entre cotización y cobro:
 * Dasic captura un margen implícito sobre el TC además de la utilidad
 * explícita por línea. Match exacto a `CotProveedor!F6` del Excel.
 *
 * Pure functions que reflejan el backend's `_convert_cost_to_quote_currency`.
 */

import type { CartItem, Moneda } from '../types';

export type TcSet = {
  tc_dof: number;        // DOF (Banxico oficial)
  tc_mn_a_usd: number;   // efectivo para conversión MN → USD
  tc_usd_a_mn: number;   // efectivo para conversión USD → MN
};

/**
 * Conversión de costo del proveedor a la divisa de cotización.
 *
 * Usa los TCs DIRECCIONALES (no el DOF), porque la cotización al cliente
 * incluye el spread como colchón. Para "Costo OC" (lo que se le paga al
 * proveedor) usa `convertCostDOF` en su lugar.
 *
 * Reglas:
 *   - Mismo origen y destino → sin conversión
 *   - USD → MXN: costo * tc_usd_a_mn (default DOF + 1)
 *   - MXN → USD: costo / tc_mn_a_usd (default DOF - 1; guarded vs ≤ 0)
 */
export function convertCost(
  costo: number,
  monedaOrigen: Moneda,
  monedaCotizacion: Moneda,
  tcs: TcSet,
): number {
  if (monedaOrigen === monedaCotizacion) return costo;
  if (monedaOrigen === 'USD' && monedaCotizacion === 'MXN') {
    return costo * tcs.tc_usd_a_mn;
  }
  if (monedaOrigen === 'MXN' && monedaCotizacion === 'USD') {
    if (tcs.tc_mn_a_usd <= 0) return costo;
    return costo / tcs.tc_mn_a_usd;
  }
  return costo;
}

/**
 * Conversión usando DOF puro (sin spread). Se usa para mostrar "Costo OC"
 * por línea — lo que Dasic le va a pagar al proveedor cuando se emita la
 * orden de compra. Match exacto a `CotProveedor!G6` del Excel.
 */
export function convertCostDOF(
  costo: number,
  monedaOrigen: Moneda,
  monedaCotizacion: Moneda,
  tc_dof: number,
): number {
  if (monedaOrigen === monedaCotizacion) return costo;
  if (monedaOrigen === 'USD' && monedaCotizacion === 'MXN') {
    return costo * tc_dof;
  }
  if (monedaOrigen === 'MXN' && monedaCotizacion === 'USD') {
    if (tc_dof <= 0) return costo;
    return costo / tc_dof;
  }
  return costo;
}

/**
 * Línea importe (precio extendido) usando los TCs direccionales — es lo
 * que cobra al cliente.
 *
 *   precio_unit_bruto = costo_convertido × (1 + utilidad / 100)
 *   importe           = precio_unit_bruto × qty × (1 − descuento / 100)
 */
export function lineImporte(
  item: CartItem,
  monedaCotizacion: Moneda,
  tcs: TcSet,
): number {
  const costoConvertido = convertCost(
    Number(item.cost),
    item.productCurrency,
    monedaCotizacion,
    tcs,
  );
  const precioUnitBruto = costoConvertido * (1 + Number(item.utilidad) / 100);
  return precioUnitBruto * Number(item.qty) * (1 - Number(item.descuento) / 100);
}

export type Totals = { subtotal: number; iva: number; total: number };

export function computeTotals(
  cart: CartItem[],
  monedaCotizacion: Moneda,
  tcs: TcSet,
  ivaRate: number,
): Totals {
  const subtotal = cart.reduce(
    (acc, item) => acc + lineImporte(item, monedaCotizacion, tcs),
    0,
  );
  const iva = subtotal * ivaRate;
  const total = subtotal + iva;
  return { subtotal, iva, total };
}

/**
 * Subtotales por moneda NATIVA — antes de IVA y SIN conversión por TC.
 *
 * Útil para que el usuario vea "esta cot tiene X líneas USD por $Y antes
 * de convertir y Z líneas MXN por $W". El importe nativo por línea es:
 *
 *   importe_nativo = cost × qty × (1 + utilidad/100) × (1 − descuento/100)
 *
 * NO se aplica TC porque el objetivo es mostrar lo que el cliente cobra
 * (o paga al proveedor) en la moneda original de cada línea, sin que el
 * spread direccional distorsione el número.
 */
export type TotalsPorMoneda = {
  mxn: number;
  usd: number;
  mxn_count: number;
  usd_count: number;
};

export function computeTotalsPorMoneda(cart: CartItem[]): TotalsPorMoneda {
  let mxn = 0;
  let usd = 0;
  let mxn_count = 0;
  let usd_count = 0;
  for (const item of cart) {
    const importeNativo =
      Number(item.cost) *
      Number(item.qty) *
      (1 + Number(item.utilidad) / 100) *
      (1 - Number(item.descuento) / 100);
    if (item.productCurrency === 'USD') {
      usd += importeNativo;
      usd_count += 1;
    } else {
      mxn += importeNativo;
      mxn_count += 1;
    }
  }
  return { mxn, usd, mxn_count, usd_count };
}

/**
 * Resuelve los 2 TCs direccionales a partir del DOF si no vienen seteados.
 * Mismo comportamiento que el helper backend `_resolve_directional_tcs`.
 */
export function resolveDirectionalTcs(
  tc_dof: number,
  tc_mn_a_usd: number | null,
  tc_usd_a_mn: number | null,
): TcSet {
  return {
    tc_dof,
    tc_mn_a_usd:
      tc_mn_a_usd != null && tc_mn_a_usd > 0
        ? tc_mn_a_usd
        : Math.max(tc_dof - 1, 0.000001),
    tc_usd_a_mn:
      tc_usd_a_mn != null && tc_usd_a_mn > 0 ? tc_usd_a_mn : tc_dof + 1,
  };
}

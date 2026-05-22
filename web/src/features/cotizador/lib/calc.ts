/**
 * calc.ts — Pricing utilities for the cotizador live preview.
 *
 * Pure functions that mirror the backend's cost-conversion and line-total
 * logic (app/routers/ventas.py::_convert_cost_to_quote_currency).
 * No React, no async, no side effects.
 */

import type { CartItem, Moneda } from '../types';

/**
 * Convert a product cost from its native currency to the quote's currency.
 *
 * Rules:
 *   - Same currency → return cost unchanged.
 *   - USD → MXN: multiply by tc.
 *   - MXN → USD: divide by tc (guard against tc ≤ 0 to avoid Infinity/NaN).
 *   - Any other combination → return cost unchanged (defensive fallback).
 */
export function convertCost(
  costo: number,
  monedaOrigen: Moneda,
  monedaCotizacion: Moneda,
  tc: number,
): number {
  if (monedaOrigen === monedaCotizacion) {
    return costo;
  }
  if (monedaOrigen === 'USD' && monedaCotizacion === 'MXN') {
    return costo * tc;
  }
  if (monedaOrigen === 'MXN' && monedaCotizacion === 'USD') {
    if (tc <= 0) {
      return costo;
    }
    return costo / tc;
  }
  // Unexpected combination — return unchanged.
  return costo;
}

/**
 * Compute the line importe (extended price) for a single CartItem.
 *
 * Formula (mirrors backend):
 *   precio_unit_bruto = costo_convertido × (1 + utilidad / 100)
 *   importe           = precio_unit_bruto × qty × (1 − descuento / 100)
 */
export function lineImporte(
  item: CartItem,
  monedaCotizacion: Moneda,
  tc: number,
): number {
  const costoConvertido = convertCost(
    Number(item.cost),
    item.productCurrency,
    monedaCotizacion,
    tc,
  );
  const precioUnitBruto = costoConvertido * (1 + Number(item.utilidad) / 100);
  return precioUnitBruto * Number(item.qty) * (1 - Number(item.descuento) / 100);
}

export type Totals = { subtotal: number; iva: number; total: number };

/**
 * Aggregate cart totals.
 *
 * Formula:
 *   subtotal = Σ lineImporte(item)
 *   iva      = subtotal × ivaRate   (e.g. 0.16 for 16 %)
 *   total    = subtotal + iva
 */
export function computeTotals(
  cart: CartItem[],
  monedaCotizacion: Moneda,
  tc: number,
  ivaRate: number,
): Totals {
  const subtotal = cart.reduce(
    (acc, item) => acc + lineImporte(item, monedaCotizacion, tc),
    0,
  );
  const iva = subtotal * ivaRate;
  const total = subtotal + iva;
  return { subtotal, iva, total };
}

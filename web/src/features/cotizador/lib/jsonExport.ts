// Export/Import del borrador del cotizador a JSON.
// Schema versionado: `cotizador-borrador-v1`.
//
// El snapshot guarda lo mínimo necesario para reconstruir el estado del
// editor (header + cart). Los snapshots NO guardan el producto completo
// (sku, nombre, costo, etc.) — al importar, el flujo hace un fetch
// `GET /api/productos/{id}` por línea para hidratar contra el catálogo
// actual; así si el producto cambió, el borrador refleja precios vigentes.
// Si el producto fue eliminado del catálogo, esa línea se omite.

import type { CartItem, Moneda } from '../types';

type SnapshotBase = {
  cliente_id: number | null;
  moneda: Moneda;
  tc: number;
  observaciones: string;
  terminos_condiciones: string;
  cart: CartItem[];
};

export type BorradorSnapshot = SnapshotBase & {
  schema: 'cotizador-borrador-v1';
  exportado_en: string;
};

export function exportBorrador(state: SnapshotBase): string {
  const payload: BorradorSnapshot = {
    schema: 'cotizador-borrador-v1',
    exportado_en: new Date().toISOString(),
    ...state,
  };
  return JSON.stringify(payload, null, 2);
}

export function importBorrador(json: string): SnapshotBase {
  let parsed: unknown;
  try {
    parsed = JSON.parse(json);
  } catch (e) {
    throw new Error('Archivo JSON inválido');
  }
  if (!parsed || typeof parsed !== 'object') {
    throw new Error('Archivo JSON inválido (no es un objeto)');
  }
  const obj = parsed as Partial<BorradorSnapshot>;
  if (obj.schema !== 'cotizador-borrador-v1') {
    throw new Error(`Schema desconocido: ${String(obj.schema)}`);
  }
  if (!Array.isArray(obj.cart)) {
    throw new Error('Campo "cart" inválido o ausente');
  }
  return {
    cliente_id: obj.cliente_id ?? null,
    moneda: (obj.moneda === 'USD' ? 'USD' : 'MXN'),
    tc: typeof obj.tc === 'number' && Number.isFinite(obj.tc) ? obj.tc : 1,
    observaciones: typeof obj.observaciones === 'string' ? obj.observaciones : '',
    terminos_condiciones:
      typeof obj.terminos_condiciones === 'string' ? obj.terminos_condiciones : '',
    cart: obj.cart as CartItem[],
  };
}

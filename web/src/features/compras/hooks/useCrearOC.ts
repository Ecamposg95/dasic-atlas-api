import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api, type ApiError } from '@/lib/api';
import type { OrdenCompra, Moneda } from '../types';

/** Payload de creación manual de OC (POST /api/compras/).
 *
 *  Shape mirrors `OCEditorIn` en `app/routers/compras.py`. Las líneas son
 *  fantasma por defecto (sin `producto_id`) → MVP. El backend acepta
 *  `producto_id` opcional + `descripcion_libre` requerido cuando no hay producto.
 */
export type CrearOCLineaPayload = {
  producto_id?: number | null;
  sku_libre?: string | null;
  descripcion_libre?: string | null;
  cantidad: number;
  costo_unitario: number;
  moneda_origen?: Moneda | null;
};

export type CrearOCPayload = {
  proveedor_id: number;
  cotizacion_id?: number | null;
  moneda: Moneda;
  tipo_cambio: number;
  detalles: CrearOCLineaPayload[];
};

export function useCrearOC() {
  const qc = useQueryClient();
  return useMutation<OrdenCompra, ApiError, CrearOCPayload>({
    mutationFn: (payload) => api.post<OrdenCompra>('/api/compras/', payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['ordenesCompra'] });
    },
  });
}

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

// Shape REAL del backend (`app/routers/ventas.py:1931`):
//   GET /api/ventas/productos-relacionados/{id} → array (no wrapper {items})
//   [{ producto_id, sku, nombre, marca, stock_actual, co_apariciones }]
//
// El plan asumía `{ items: Array<Producto & { veces_juntos }> }`; aquí adaptamos.
export type RelacionadoItem = {
  producto_id: number;
  sku: string | null;
  nombre: string;
  marca: string | null;
  stock_actual: number;
  co_apariciones: number;
};

/**
 * Productos que aparecen junto al primer producto del carrito.
 * El backend devuelve top N por co-ocurrencia para un solo producto ancla;
 * usamos el primero del carrito como ancla (MVP).
 */
export function useRelacionados(productoIds: number[]) {
  const ancla = productoIds[0] ?? null;
  return useQuery<RelacionadoItem[]>({
    queryKey: ['ventas', 'relacionados', ancla],
    queryFn: () => api.get<RelacionadoItem[]>(`/api/ventas/productos-relacionados/${ancla}`),
    enabled: ancla != null,
    staleTime: 60_000,
  });
}

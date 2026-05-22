import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Producto } from '../types';

// Carga todos los productos (page_size=200). Los filtros son client-side
// ya que el catálogo suele ser <500 items.

export function useProductos() {
  return useQuery<Producto[]>({
    queryKey: ['productos'],
    queryFn: () => api.get<Producto[]>('/api/productos?page_size=200'),
    staleTime: 30_000,
  });
}

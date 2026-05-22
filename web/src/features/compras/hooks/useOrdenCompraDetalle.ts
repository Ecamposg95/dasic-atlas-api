import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { OrdenCompra } from '../types';

export function useOrdenCompraDetalle(id: number | null) {
  return useQuery<OrdenCompra>({
    queryKey: ['ordenCompraDetalle', id],
    queryFn: () => api.get<OrdenCompra>(`/api/compras/${id}/json`),
    enabled: id != null,
  });
}

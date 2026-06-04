import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { EstatusOC, OrdenCompraListItem } from '../types';

// Paginación via skip/limit. q y estatus son server-side.
export function useOrdenesCompra(page = 1, q = '', estatus: EstatusOC | '' = '') {
  const PAGE_SIZE = 50;
  const skip = (page - 1) * PAGE_SIZE;
  const params = new URLSearchParams();
  params.set('skip', String(skip));
  params.set('limit', String(PAGE_SIZE));
  if (q.trim()) params.set('q', q.trim());
  if (estatus) params.set('estatus', estatus);
  return useQuery<OrdenCompraListItem[]>({
    queryKey: ['ordenesCompra', page, q.trim(), estatus],
    queryFn: () => api.get<OrdenCompraListItem[]>(`/api/compras/historial?${params.toString()}`),
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  });
}

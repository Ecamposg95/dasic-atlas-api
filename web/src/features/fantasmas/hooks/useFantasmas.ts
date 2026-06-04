import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { EstadoFantasma, FantasmasResponse } from '../types';

// Paginación server-side con page_size=50.
// Filtros q/estado/proveedor_id son server-side (backend los soporta).
// filtroMoneda y sinAsignar permanecen client-side (el backend no los soporta aún).
export function useFantasmas(
  page: number,
  q: string,
  estado: EstadoFantasma | '',
  proveedorId: number | null,
) {
  const params = new URLSearchParams();
  params.set('page', String(page));
  params.set('page_size', '50');
  if (q.trim()) params.set('q', q.trim());
  if (estado) params.set('estado', estado);
  if (proveedorId != null) params.set('proveedor_id', String(proveedorId));
  return useQuery<FantasmasResponse>({
    queryKey: ['fantasmas', page, q.trim(), estado, proveedorId],
    queryFn: () => api.get<FantasmasResponse>(`/api/fantasmas/?${params.toString()}`),
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  });
}

// web/src/features/servicios/hooks/useServicios.ts
import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { ServiciosListResponse } from '../types';

export const SERVICIOS_PAGE_SIZE = 50;

type Params = {
  q?: string;
  categoria?: string;
  activo?: boolean;
  page?: number;
};

export function useServicios(params: Params = {}) {
  const { q, categoria, activo = true, page = 1 } = params;
  const sp = new URLSearchParams();
  if (q) sp.set('q', q);
  if (categoria) sp.set('categoria', categoria);
  sp.set('activo', String(activo));
  sp.set('page', String(page));
  sp.set('page_size', String(SERVICIOS_PAGE_SIZE));

  return useQuery<ServiciosListResponse>({
    queryKey: ['servicios', { q, categoria, activo, page }],
    queryFn: () => api.get<ServiciosListResponse>(`/api/servicios/?${sp.toString()}`),
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  });
}

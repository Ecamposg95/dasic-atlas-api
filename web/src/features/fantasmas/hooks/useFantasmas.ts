import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { FantasmasResponse } from '../types';

// Siempre pide page_size=500 para tener todos los fantasmas en memoria.
// Los KPIs (conteos por estado) se calculan en JS agrupando `items`.
// Los filtros de moneda y "sin asignar" son client-side también.

export function useFantasmas() {
  return useQuery<FantasmasResponse>({
    queryKey: ['fantasmas'],
    queryFn: () => api.get<FantasmasResponse>('/api/fantasmas/?page_size=500'),
    staleTime: 30_000,
  });
}

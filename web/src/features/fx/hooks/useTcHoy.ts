import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { TipoCambio } from '../types';

export function useTcHoy(fecha?: string) {
  const qs = fecha ? `?fecha=${fecha}` : '';
  return useQuery<TipoCambio>({
    queryKey: ['fx-hoy', fecha ?? 'today'],
    queryFn: () => api.get<TipoCambio>(`/api/fx/usd-mxn${qs}`),
    staleTime: 5 * 60_000,
  });
}

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { TendenciaResponse } from '../types';

export function useTendencia(meses = 12) {
  return useQuery<TendenciaResponse>({
    queryKey: ['dashboard', 'tendencia', meses],
    queryFn: () => api.get<TendenciaResponse>(`/api/dashboard/tendencia?meses=${meses}`),
    staleTime: 60_000,
  });
}

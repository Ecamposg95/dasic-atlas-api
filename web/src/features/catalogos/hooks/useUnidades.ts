import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { UnidadesResponse } from '../types';

export function useUnidades() {
  return useQuery<UnidadesResponse>({
    queryKey: ['catalogos', 'unidades'],
    queryFn: () => api.get<UnidadesResponse>('/api/catalogos/unidades'),
    staleTime: 60_000,
  });
}

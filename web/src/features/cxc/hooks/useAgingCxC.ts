import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { AgingResponse } from '../types';

export function useAgingCxC() {
  return useQuery<AgingResponse>({
    queryKey: ['cxc-aging'],
    queryFn: () => api.get<AgingResponse>('/api/cuentas-por-cobrar/aging'),
    staleTime: 60_000,
  });
}

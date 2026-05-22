import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { ResumenCxC } from '../types';

export function useResumenCxC() {
  return useQuery<ResumenCxC>({
    queryKey: ['cxc-resumen'],
    queryFn: () => api.get<ResumenCxC>('/api/cuentas-por-cobrar/resumen'),
    staleTime: 60_000,
  });
}

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { VencimientosResponse } from '../types';

export function useVencimientosCxC(dias = 90) {
  return useQuery<VencimientosResponse>({
    queryKey: ['cxc-vencimientos', dias],
    queryFn: () => api.get<VencimientosResponse>(`/api/cuentas-por-cobrar/vencimientos?dias=${dias}`),
    staleTime: 60_000,
  });
}

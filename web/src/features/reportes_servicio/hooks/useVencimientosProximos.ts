import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { VencimientosProximosResponse } from '../types';

export function useVencimientosProximos(dias: number) {
  return useQuery({
    queryKey: ['reportes-servicio', 'vencimientos-proximos', dias],
    queryFn: () =>
      api.get<VencimientosProximosResponse>(
        `/api/reportes/vencimientos-proximos?dias=${dias}`,
      ),
  });
}

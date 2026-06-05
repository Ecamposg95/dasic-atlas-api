import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { TopDeudor } from '../types';

export function useTopDeudores(limit = 10) {
  return useQuery<TopDeudor[]>({
    queryKey: ['cxc-top-deudores', limit],
    queryFn: () => api.get<TopDeudor[]>(`/api/cuentas-por-cobrar/top-deudores?limit=${limit}`),
    staleTime: 60_000,
  });
}

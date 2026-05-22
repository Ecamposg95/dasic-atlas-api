import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { FxHistoricoResponse } from '../types';

export function useHistorialFx(dias = 30) {
  return useQuery<FxHistoricoResponse>({
    queryKey: ['fx-historico', dias],
    queryFn: () => api.get<FxHistoricoResponse>(`/api/fx/historico?dias=${dias}`),
    staleTime: 5 * 60_000,
  });
}

import { useQuery } from '@tanstack/react-query';
import { api, type ApiError } from '@/lib/api';
import type { RankingVendedorItem } from '../types';

export function useRankingVendedores(dias: number) {
  return useQuery<RankingVendedorItem[], ApiError>({
    queryKey: ['reportes', 'ranking-vendedores', dias],
    queryFn: () =>
      api.get<RankingVendedorItem[]>(
        `/api/reportes/ranking-vendedores?dias=${dias}`,
      ),
    retry: (failureCount, error) => {
      // Don't retry 401/403 — those are auth/authz errors
      if (error.status === 401 || error.status === 403) return false;
      return failureCount < 2;
    },
  });
}

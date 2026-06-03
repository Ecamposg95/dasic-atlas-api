import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { GrupoDuplicado, MergeResult } from '../types';

export function useDuplicados() {
  return useQuery<GrupoDuplicado[]>({
    queryKey: ['clientes', 'duplicados'],
    queryFn: () => api.get<GrupoDuplicado[]>('/api/clientes/duplicados'),
    staleTime: 30_000,
  });
}

export function useMergeEmpresas() {
  const qc = useQueryClient();
  return useMutation<MergeResult, { status?: number; detail?: string }, { survivor_id: number; loser_ids: number[] }>({
    mutationFn: (body) => api.post<MergeResult>('/api/clientes/merge', body),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['clientes', 'duplicados'] });
      void qc.invalidateQueries({ queryKey: ['clientes'] });
    },
  });
}

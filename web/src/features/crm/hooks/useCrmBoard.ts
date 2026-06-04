import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Board, Pipeline } from '../types';

export function useCrmPipelines() {
  return useQuery<Pipeline[]>({
    queryKey: ['crm', 'pipelines'],
    queryFn: () => api.get<Pipeline[]>('/api/crm/pipelines'),
    staleTime: 60_000,
  });
}

export function useCrmBoard(pipelineId: number | null) {
  return useQuery<Board>({
    queryKey: ['crm', 'board', pipelineId],
    queryFn: () => api.get<Board>(`/api/crm/pipelines/${pipelineId}/board`),
    enabled: pipelineId != null,
    staleTime: 30_000,
  });
}

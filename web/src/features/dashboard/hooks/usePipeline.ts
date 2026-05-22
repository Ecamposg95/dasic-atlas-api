import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { PipelineResponse } from '../types';

export function usePipeline() {
  return useQuery<PipelineResponse>({
    queryKey: ['dashboard', 'pipeline'],
    queryFn: () => api.get<PipelineResponse>('/api/dashboard/pipeline'),
    staleTime: 60_000,
  });
}

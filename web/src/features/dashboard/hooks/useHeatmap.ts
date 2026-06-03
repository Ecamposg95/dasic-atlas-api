import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { HeatmapResponse } from '../types';

export function useHeatmap(dias = 90) {
  return useQuery<HeatmapResponse>({
    queryKey: ['dashboard', 'heatmap', dias],
    queryFn: () => api.get<HeatmapResponse>(`/api/dashboard/heatmap?dias=${dias}`),
    staleTime: 60_000,
  });
}

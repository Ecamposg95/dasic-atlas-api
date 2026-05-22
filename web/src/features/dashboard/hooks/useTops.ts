import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { TopsResponse } from '../types';

export function useTops() {
  return useQuery<TopsResponse>({
    queryKey: ['dashboard', 'tops'],
    queryFn: () => api.get<TopsResponse>('/api/dashboard/tops'),
    staleTime: 60_000,
  });
}

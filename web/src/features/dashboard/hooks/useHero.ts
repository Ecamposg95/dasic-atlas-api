import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { HeroResponse } from '../types';

export function useHero(window = 'mtd') {
  return useQuery<HeroResponse>({
    queryKey: ['dashboard', 'hero', window],
    queryFn: () => api.get<HeroResponse>(`/api/dashboard/hero?window=${window}`),
    staleTime: 60_000,
  });
}

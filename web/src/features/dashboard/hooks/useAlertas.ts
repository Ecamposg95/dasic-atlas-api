import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { AlertasResponse } from '../types';

export function useAlertas() {
  return useQuery<AlertasResponse>({
    queryKey: ['dashboard', 'alertas'],
    queryFn: () => api.get<AlertasResponse>('/api/dashboard/alertas'),
    staleTime: 60_000,
  });
}

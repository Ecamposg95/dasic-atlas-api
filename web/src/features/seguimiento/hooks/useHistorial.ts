import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { HistorialItem } from '../types';

export function useHistorial(limit = 200) {
  return useQuery<HistorialItem[]>({
    queryKey: ['ventas', 'historial', limit],
    queryFn: () => api.get<HistorialItem[]>(`/api/ventas/historial?limit=${limit}`),
    staleTime: 30_000,
  });
}

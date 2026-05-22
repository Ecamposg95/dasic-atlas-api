import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { TopProductoItem } from '../types';

export function useTopProductos(dias: number) {
  return useQuery({
    queryKey: ['reportes', 'top-productos', dias],
    queryFn: () =>
      api.get<TopProductoItem[]>(`/api/reportes/top-productos?dias=${dias}`),
  });
}

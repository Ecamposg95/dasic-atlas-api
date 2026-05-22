import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { TopClienteItem } from '../types';

export function useTopClientes(dias: number) {
  return useQuery({
    queryKey: ['reportes', 'top-clientes', dias],
    queryFn: () =>
      api.get<TopClienteItem[]>(`/api/reportes/top-clientes?dias=${dias}`),
  });
}

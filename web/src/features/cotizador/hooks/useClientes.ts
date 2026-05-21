import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Cliente } from '../types';

export function useClientes() {
  return useQuery<Cliente[]>({
    queryKey: ['clientes'],
    queryFn: () => api.get<Cliente[]>('/api/clientes/'),
    staleTime: 5 * 60_000, // 5 min — los clientes no cambian a cada rato
  });
}

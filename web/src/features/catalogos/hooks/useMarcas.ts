import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Marca } from '../types';

export function useMarcas() {
  return useQuery<Marca[]>({
    queryKey: ['catalogos', 'marcas'],
    queryFn: () => api.get<Marca[]>('/api/catalogos/marcas'),
    staleTime: 60_000,
  });
}

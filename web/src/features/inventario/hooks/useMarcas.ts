import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Marca } from '../types';

export function useMarcas() {
  return useQuery<Marca[]>({
    queryKey: ['marcas'],
    queryFn: () => api.get<Marca[]>('/api/catalogos/marcas'),
    staleTime: 5 * 60 * 1_000, // 5 minutos
  });
}

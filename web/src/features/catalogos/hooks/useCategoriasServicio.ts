import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { CategoriasServicioResponse } from '../types';

export function useCategoriasServicio() {
  return useQuery<CategoriasServicioResponse>({
    queryKey: ['catalogos', 'categorias-servicio'],
    queryFn: () => api.get<CategoriasServicioResponse>('/api/catalogos/categorias-servicio'),
    staleTime: 60_000,
  });
}

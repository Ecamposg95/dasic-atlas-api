import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { CategoriasProductoResponse } from '../types';

export function useCategorias() {
  return useQuery<CategoriasProductoResponse>({
    queryKey: ['catalogos', 'categorias-producto'],
    queryFn: () => api.get<CategoriasProductoResponse>('/api/catalogos/categorias-producto'),
    staleTime: 60_000,
  });
}

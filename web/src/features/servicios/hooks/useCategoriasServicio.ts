// web/src/features/servicios/hooks/useCategoriasServicio.ts
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { CategoriasResponse } from '../types';

export function useCategoriasServicio() {
  return useQuery<CategoriasResponse>({
    queryKey: ['servicios-categorias'],
    queryFn: () => api.get<CategoriasResponse>('/api/servicios/utils/categorias'),
    staleTime: 60_000,
  });
}

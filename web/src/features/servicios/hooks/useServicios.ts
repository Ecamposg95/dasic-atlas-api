// web/src/features/servicios/hooks/useServicios.ts
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Servicio } from '../types';

type Params = {
  q?: string;
  categoria?: string;
  activo?: boolean;
};

export function useServicios(params: Params = {}) {
  const { q, categoria, activo = true } = params;
  const sp = new URLSearchParams();
  if (q) sp.set('q', q);
  if (categoria) sp.set('categoria', categoria);
  sp.set('activo', String(activo));

  return useQuery<Servicio[]>({
    queryKey: ['servicios', { q, categoria, activo }],
    queryFn: () => api.get<Servicio[]>(`/api/servicios/?${sp.toString()}`),
    staleTime: 30_000,
  });
}

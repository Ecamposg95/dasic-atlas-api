import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { TopServiciosResponse } from '../types';

export function useTopServicios(dias: number) {
  return useQuery({
    queryKey: ['reportes-servicio', 'top-servicios', dias],
    queryFn: () =>
      api.get<TopServiciosResponse>(`/api/reportes/top-servicios?dias=${dias}`),
  });
}

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { VentasMesResponse } from '../types';

export function useVentasMes(meses: number) {
  return useQuery({
    queryKey: ['reportes', 'ventas-mes', meses],
    queryFn: () =>
      api.get<VentasMesResponse>(`/api/reportes/ventas-mes?meses=${meses}`),
  });
}

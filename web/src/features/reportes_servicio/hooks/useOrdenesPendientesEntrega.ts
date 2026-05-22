import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { OrdenesPendientesEntregaResponse } from '../types';

export function useOrdenesPendientesEntrega() {
  return useQuery({
    queryKey: ['reportes-servicio', 'ordenes-pendientes-entrega'],
    queryFn: () =>
      api.get<OrdenesPendientesEntregaResponse>(
        '/api/reportes/ordenes-pendientes-entrega',
      ),
  });
}

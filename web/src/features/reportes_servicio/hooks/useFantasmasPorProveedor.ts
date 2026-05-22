import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { FantasmasPorProveedorResponse } from '../types';

export function useFantasmasPorProveedor() {
  return useQuery({
    queryKey: ['reportes-servicio', 'fantasmas-por-proveedor'],
    queryFn: () =>
      api.get<FantasmasPorProveedorResponse>(
        '/api/reportes/fantasmas-por-proveedor',
      ),
  });
}

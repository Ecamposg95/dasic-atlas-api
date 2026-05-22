import { useQuery, type UseQueryResult } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { OrdenHistorial } from '../types';

// El backend devuelve un array plano (ver `app/routers/ventas.py:1188`).
// Sólo soporta `?limit=N` como query — todos los demás filtros y la
// paginación se aplican en cliente desde `HistorialTab`.

export function useHistorial(limit = 200): UseQueryResult<OrdenHistorial[]> {
  return useQuery<OrdenHistorial[]>({
    queryKey: ['ventas', 'historial', limit],
    queryFn: () => api.get<OrdenHistorial[]>(`/api/ventas/historial?limit=${limit}`),
    staleTime: 30_000,
  });
}

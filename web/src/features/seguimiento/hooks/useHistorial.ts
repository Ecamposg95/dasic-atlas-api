import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { EstatusFilter, HistorialItem } from '../types';

// Paginación via skip/limit. q y estatus son server-side.
// vencimientoFilter permanece client-side (el backend no lo soporta aún).
export function useHistorial(page = 1, q = '', estatusFilter: EstatusFilter = 'TODOS') {
  const PAGE_SIZE = 50;
  const skip = (page - 1) * PAGE_SIZE;
  const params = new URLSearchParams();
  params.set('skip', String(skip));
  params.set('limit', String(PAGE_SIZE));
  if (q.trim()) params.set('q', q.trim());
  if (estatusFilter && estatusFilter !== 'TODOS') params.set('estatus', estatusFilter);
  return useQuery<HistorialItem[]>({
    queryKey: ['ventas', 'historial', page, q.trim(), estatusFilter],
    queryFn: () => api.get<HistorialItem[]>(`/api/ventas/historial?${params.toString()}`),
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  });
}

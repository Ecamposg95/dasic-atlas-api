import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type {
  RemisionDetalle,
  RemisionesResponse,
  RecepcionResponse,
  RemisionBorrador,
  RemisionCreatePayload,
  RemisionCreateResponse,
  OrdenHistorialItem,
} from '../types';

export function useRemisiones(
  page: number,
  q = '',
  recibida: boolean | null = null,
) {
  const params = new URLSearchParams();
  params.set('page', String(page));
  params.set('page_size', '50');
  if (q.trim()) params.set('q', q.trim());
  if (recibida !== null) params.set('recibida', String(recibida));
  return useQuery({
    queryKey: ['remisiones', page, q.trim(), recibida],
    queryFn: () =>
      api.get<RemisionesResponse>(`/api/remisiones/?${params.toString()}`),
    placeholderData: keepPreviousData,
  });
}

export function useRemisionDetalle(id: number | null) {
  return useQuery({
    queryKey: ['remision', id],
    queryFn: () => api.get<RemisionDetalle>(`/api/remisiones/${id}`),
    enabled: id !== null,
  });
}

export function useRegistrarRecepcion() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, recibido_por }: { id: number; recibido_por: string }) =>
      api.patch<RecepcionResponse>(`/api/remisiones/${id}/recepcion?recibido_por=${encodeURIComponent(recibido_por)}`),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['remisiones'] });
    },
  });
}

export function useRemisionBorrador(ordenId: number | null) {
  return useQuery({
    queryKey: ['remision-borrador', ordenId],
    queryFn: () => api.get<RemisionBorrador>(`/api/remisiones/orden/${ordenId}/borrador`),
    enabled: ordenId !== null,
  });
}

export function useCrearRemision() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: RemisionCreatePayload) =>
      api.post<RemisionCreateResponse>('/api/remisiones/', payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['remisiones'] });
    },
  });
}

export function useOrdenesRemisionables() {
  // Órdenes ya convertidas a venta (estatus != cotizacion) candidatas a remisión.
  return useQuery({
    queryKey: ['ventas', 'historial', 'remisionables'],
    queryFn: async () => {
      const items = await api.get<OrdenHistorialItem[]>('/api/ventas/historial?limit=200');
      return items.filter((o) => (o.estatus || '').toLowerCase() !== 'cotizacion');
    },
  });
}

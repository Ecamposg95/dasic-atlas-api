import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type {
  PreciosListResponse,
  PrecioProveedorCreate,
  ComparativaResponse,
} from '../types';

interface PreciosFiltros {
  producto_id?: number | null;
  proveedor_id?: number | null;
}

export function usePrecios(filtros: PreciosFiltros = {}) {
  const qs = new URLSearchParams({ page_size: '200' });
  if (filtros.producto_id) qs.set('producto_id', String(filtros.producto_id));
  if (filtros.proveedor_id) qs.set('proveedor_id', String(filtros.proveedor_id));

  return useQuery<PreciosListResponse>({
    queryKey: ['precios', filtros],
    queryFn: () => api.get<PreciosListResponse>(`/api/precios/?${qs.toString()}`),
    staleTime: 30_000,
  });
}

export function useComparativaPrecios(producto_id: number | null) {
  return useQuery<ComparativaResponse>({
    queryKey: ['precios-comparar', producto_id],
    queryFn: () =>
      api.get<ComparativaResponse>(`/api/precios/comparar?producto_id=${producto_id}`),
    enabled: producto_id !== null,
    staleTime: 30_000,
  });
}

export function useCrearPrecio() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: PrecioProveedorCreate) =>
      api.post<{ id: number }>('/api/precios/', payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['precios'] });
      void qc.invalidateQueries({ queryKey: ['precios-comparar'] });
    },
  });
}

export function useEliminarPrecio() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      api.delete<{ id: number; deleted: boolean }>(`/api/precios/${id}`),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['precios'] });
      void qc.invalidateQueries({ queryKey: ['precios-comparar'] });
    },
  });
}

import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Gasto, GastoCreate, GastoUpdate, GastosPage, GastosFiltros } from '../types';

export const GASTOS_PAGE_SIZE = 50;

export function useGastos(page: number, filtros: GastosFiltros) {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(GASTOS_PAGE_SIZE),
  });
  if (filtros.q?.trim()) params.set('q', filtros.q.trim());
  if (filtros.categoria) params.set('categoria', filtros.categoria);
  if (filtros.fechaDesde) params.set('fecha_desde', filtros.fechaDesde);
  if (filtros.fechaHasta) params.set('fecha_hasta', filtros.fechaHasta);

  return useQuery({
    queryKey: ['gastos', page, filtros],
    queryFn: () => api.get<GastosPage>(`/api/gastos/?${params.toString()}`),
    placeholderData: keepPreviousData,
  });
}

export function useCategoriasGasto() {
  return useQuery({
    queryKey: ['gastos', 'categorias'],
    queryFn: () => api.get<string[]>('/api/gastos/categorias'),
  });
}

export function useCrearGasto() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: GastoCreate) => api.post<Gasto>('/api/gastos/', payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['gastos'] });
    },
  });
}

export function useEditarGasto() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: GastoUpdate }) =>
      api.put<Gasto>(`/api/gastos/${id}`, payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['gastos'] });
    },
  });
}

export function useEliminarGasto() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.delete<{ mensaje: string }>(`/api/gastos/${id}`),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['gastos'] });
    },
  });
}

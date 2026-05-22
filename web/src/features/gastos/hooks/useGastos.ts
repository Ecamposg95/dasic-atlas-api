import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Gasto, GastoCreate, GastoUpdate } from '../types';

export function useGastos() {
  return useQuery({
    queryKey: ['gastos'],
    queryFn: () => api.get<Gasto[]>('/api/gastos/?limit=500'),
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

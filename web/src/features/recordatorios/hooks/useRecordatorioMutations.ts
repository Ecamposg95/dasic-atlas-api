import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Recordatorio, RecordatorioCreate } from '../types';

function invalidateAll(qc: ReturnType<typeof useQueryClient>) {
  qc.invalidateQueries({ queryKey: ['recordatorios'] });
}

export function useCrearRecordatorio() {
  const qc = useQueryClient();
  return useMutation<Recordatorio, { status: number; detail: string }, RecordatorioCreate>({
    mutationFn: (body) => api.post<Recordatorio>('/api/recordatorios/', body),
    onSuccess: () => invalidateAll(qc),
  });
}

export function useCompletarRecordatorio() {
  const qc = useQueryClient();
  return useMutation<Recordatorio, { status: number; detail: string }, number>({
    mutationFn: (id) => api.patch<Recordatorio>(`/api/recordatorios/${id}/completar`),
    onSuccess: () => invalidateAll(qc),
  });
}

export function usePosponerRecordatorio() {
  const qc = useQueryClient();
  return useMutation<Recordatorio, { status: number; detail: string }, { id: number; nueva_fecha: string }>({
    mutationFn: ({ id, nueva_fecha }) =>
      api.patch<Recordatorio>(`/api/recordatorios/${id}/posponer`, { nueva_fecha }),
    onSuccess: () => invalidateAll(qc),
  });
}

export function useEliminarRecordatorio() {
  const qc = useQueryClient();
  return useMutation<void, { status: number; detail: string }, number>({
    mutationFn: (id) => api.delete<void>(`/api/recordatorios/${id}`),
    onSuccess: () => invalidateAll(qc),
  });
}

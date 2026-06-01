import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { RecepcionParcialPayload, RecepcionParcialResponse } from '../types';

export function useRecibirParcial(id: number) {
  const qc = useQueryClient();
  return useMutation<RecepcionParcialResponse, { status?: number; detail?: string }, RecepcionParcialPayload>({
    mutationFn: (payload) => api.post<RecepcionParcialResponse>(`/api/compras/${id}/recibir-parcial`, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['ordenesCompra'] });
      qc.invalidateQueries({ queryKey: ['ordenCompraDetalle', id] });
    },
  });
}

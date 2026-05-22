import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api, type ApiError } from '@/lib/api';
import type { ConvertirResponse } from '../types';

export function useConvertir() {
  const qc = useQueryClient();
  return useMutation<ConvertirResponse, ApiError, number>({
    mutationFn: (cotizacionId) =>
      api.post<ConvertirResponse>(`/api/ventas/${cotizacionId}/convertir`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['ventas'] });
    },
  });
}

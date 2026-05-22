import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, type ApiError } from '@/lib/api';
import type { RecotizarResponse, VersionOrden } from '../types';

export function useRecotizar() {
  const qc = useQueryClient();
  return useMutation<RecotizarResponse, ApiError, number>({
    mutationFn: (cotizacionId) =>
      api.post<RecotizarResponse>(`/api/ventas/${cotizacionId}/recotizar`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['ventas'] });
    },
  });
}

export function useVersiones(cotizacionId: number | null) {
  return useQuery<VersionOrden[]>({
    queryKey: ['ventas', 'versiones', cotizacionId],
    queryFn: () => api.get<VersionOrden[]>(`/api/ventas/${cotizacionId}/versiones`),
    enabled: cotizacionId != null,
    staleTime: 30_000,
  });
}

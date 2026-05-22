import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, type ApiError } from '@/lib/api';
import type { Plantilla, PlantillaCreate, PlantillaCreateResponse } from '../types';

export function usePlantillas() {
  return useQuery<Plantilla[]>({
    queryKey: ['ventas', 'plantillas'],
    queryFn: () => api.get<Plantilla[]>('/api/ventas/plantillas'),
    staleTime: 60_000,
  });
}

export function useCrearPlantilla() {
  const qc = useQueryClient();
  return useMutation<PlantillaCreateResponse, ApiError, PlantillaCreate>({
    mutationFn: (body) => api.post<PlantillaCreateResponse>('/api/ventas/plantillas', body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['ventas', 'plantillas'] }),
  });
}

export function useBorrarPlantilla() {
  const qc = useQueryClient();
  return useMutation<{ ok: boolean; id: number }, ApiError, number>({
    mutationFn: (id) => api.delete<{ ok: boolean; id: number }>(`/api/ventas/plantillas/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['ventas', 'plantillas'] }),
  });
}

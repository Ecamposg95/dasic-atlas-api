import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useCotizador } from '../store';
import { buildSavePayload, type CotizadorSnapshot } from '../lib/serialize';
import type { OrdenVentaDetail } from '../types';

export function useCotizacionLoader(id: number | null) {
  return useQuery<OrdenVentaDetail>({
    queryKey: ['orden', id],
    // El backend NO expone `GET /api/ventas/{id}` plano; el detalle completo
    // para el editor vive en `/detalle-json` (app/routers/ventas.py:1354).
    queryFn: () => api.get<OrdenVentaDetail>(`/api/ventas/${id}/detalle-json`),
    enabled: id != null,
    staleTime: 0,
  });
}

type SaveResult = { id: number; folio: string };

export function useGuardarCotizacion() {
  const qc = useQueryClient();
  const editingId = useCotizador((s) => s.editingId);

  return useMutation<SaveResult, { status?: number; detail?: string }, CotizadorSnapshot>({
    mutationFn: async (snapshot) => {
      const payload = buildSavePayload(snapshot);
      if (editingId != null) {
        return api.put<SaveResult>(`/api/ventas/${editingId}`, payload);
      }
      return api.post<SaveResult>('/api/ventas/', payload);
    },
    onSuccess: (data) => {
      // Invalidar la lista de seguimiento si existe en cache
      qc.invalidateQueries({ queryKey: ['ventas'] });
      qc.invalidateQueries({ queryKey: ['orden', data.id] });
    },
  });
}

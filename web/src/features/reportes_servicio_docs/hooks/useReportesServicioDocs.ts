import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type {
  ReporteServicioDocCreate,
  ReporteServicioDocItem,
  ReportesServicioDocsResponse,
} from '../types';

export function useReportesServicioDocs(page: number) {
  return useQuery({
    queryKey: ['reportes-servicio-docs', page],
    queryFn: () =>
      api.get<ReportesServicioDocsResponse>(
        `/api/reportes-servicio-docs/?page=${page}&page_size=50`,
      ),
    placeholderData: keepPreviousData,
  });
}

export function useCrearReporteServicioDoc() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: ReporteServicioDocCreate) =>
      api.post<ReporteServicioDocItem>('/api/reportes-servicio-docs/', payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['reportes-servicio-docs'] });
    },
  });
}

export function useRegistrarRecepcionReporte() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      cliente_recibe_nombre,
    }: {
      id: number;
      cliente_recibe_nombre: string;
    }) =>
      api.patch<ReporteServicioDocItem>(
        `/api/reportes-servicio-docs/${id}/recepcion?cliente_recibe_nombre=${encodeURIComponent(cliente_recibe_nombre)}`,
      ),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['reportes-servicio-docs'] });
    },
  });
}

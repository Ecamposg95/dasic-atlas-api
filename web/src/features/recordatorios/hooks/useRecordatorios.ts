import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Recordatorio, RecordatorioResumen, RecordatorioVista } from '../types';

export function useRecordatorios(vista: RecordatorioVista = 'pendientes') {
  return useQuery<Recordatorio[]>({
    queryKey: ['recordatorios', vista],
    queryFn: () => api.get<Recordatorio[]>(`/api/recordatorios/?vista=${vista}`),
    placeholderData: (prev) => prev,
  });
}

export function useResumenRecordatorios() {
  return useQuery<RecordatorioResumen>({
    queryKey: ['recordatorios', 'resumen'],
    queryFn: () => api.get<RecordatorioResumen>('/api/recordatorios/resumen'),
    staleTime: 60_000,
  });
}

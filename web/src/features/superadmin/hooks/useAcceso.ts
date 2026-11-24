import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

export type AccesoEstado = {
  suspendida: boolean;
  mensaje: string;
  mensaje_personalizado: boolean;
  mensaje_default: string;
  actualizado_en: string | null;
  actualizado_por: string | null;
  usuarios_afectados: number;
};

// `mensaje` omitido = no tocar el guardado; '' = volver al mensaje default.
export type AccesoCambio = { suspendida: boolean; mensaje?: string };

const KEY = ['superadmin', 'acceso'];

export function useAcceso() {
  return useQuery<AccesoEstado>({
    queryKey: KEY,
    queryFn: () => api.get<AccesoEstado>('/api/superadmin/acceso'),
  });
}

export function useSetAcceso() {
  const qc = useQueryClient();
  return useMutation<AccesoEstado, { status?: number; detail?: string }, AccesoCambio>({
    mutationFn: (body) => api.put<AccesoEstado>('/api/superadmin/acceso', body),
    onSuccess: (data) => {
      qc.setQueryData(KEY, data);
      void qc.invalidateQueries({ queryKey: ['superadmin', 'audit'] });
    },
  });
}

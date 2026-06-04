import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

export type ConfigItem = { clave: string; valor_efectivo: number; default: number; overrideado: boolean };
type ConfigResp = { items: ConfigItem[] };

export function useConfigPlataforma() {
  return useQuery<ConfigResp>({
    queryKey: ['superadmin', 'config'],
    queryFn: () => api.get<ConfigResp>('/api/superadmin/config'),
  });
}

export function useSetConfigPlataforma() {
  const qc = useQueryClient();
  return useMutation<ConfigResp, { status?: number; detail?: string }, { clave: string; valor: string | null }>({
    mutationFn: (body) => api.put<ConfigResp>('/api/superadmin/config', body),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['superadmin', 'config'] });
      void qc.invalidateQueries({ queryKey: ['cotizador-config'] });
    },
  });
}

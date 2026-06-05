import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { PagoDistribuidoRequest, PagoDistribuidoResponse } from '../types';

export function usePagoDistribuido(clienteId: number) {
  const qc = useQueryClient();
  return useMutation<PagoDistribuidoResponse, { status?: number; detail?: string }, PagoDistribuidoRequest>({
    mutationFn: (body) =>
      api.post<PagoDistribuidoResponse>(`/api/clientes/${clienteId}/pago-distribuido`, body),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['cxc-resumen'] });
      void qc.invalidateQueries({ queryKey: ['cxc-vencimientos'] });
      void qc.invalidateQueries({ queryKey: ['cxc-aging'] });
      void qc.invalidateQueries({ queryKey: ['cxc-top-deudores'] });
    },
  });
}

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Contacto, ContactoInput } from '../types';

export function useContactosEmpresa(clienteId: number | null) {
  return useQuery<Contacto[]>({
    queryKey: ['contactos', clienteId],
    queryFn: () => api.get<Contacto[]>(`/api/clientes/${clienteId}/contactos`),
    enabled: clienteId !== null,
  });
}

export function useGuardarContacto(clienteId: number) {
  const qc = useQueryClient();
  return useMutation<Contacto, { status?: number; detail?: string }, { id?: number; data: ContactoInput }>({
    mutationFn: ({ id, data }) =>
      id
        ? api.patch<Contacto>(`/api/clientes/${clienteId}/contactos/${id}`, data)
        : api.post<Contacto>(`/api/clientes/${clienteId}/contactos`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['contactos', clienteId] });
      qc.invalidateQueries({ queryKey: ['clientes'] });
      void qc.invalidateQueries({ queryKey: ['contactos', 'global'] });
    },
  });
}

export function useEliminarContacto(clienteId: number) {
  const qc = useQueryClient();
  return useMutation<{ ok: boolean }, { status?: number; detail?: string }, number>({
    mutationFn: (id) => api.delete<{ ok: boolean }>(`/api/clientes/${clienteId}/contactos/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['contactos', clienteId] });
      void qc.invalidateQueries({ queryKey: ['contactos', 'global'] });
    },
  });
}

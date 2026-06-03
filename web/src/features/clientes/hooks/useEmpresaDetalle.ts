import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Contacto, ContactoInput, TransaccionCuenta, CxCClienteResponse } from '../types';

export function useContactos(clienteId: number | null) {
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

export function useEstadoCuenta(clienteId: number | null) {
  return useQuery<TransaccionCuenta[]>({
    queryKey: ['estado-cuenta', clienteId],
    queryFn: () => api.get<TransaccionCuenta[]>(`/api/clientes/${clienteId}/estado-cuenta`),
    enabled: clienteId !== null,
  });
}

export function useCxCCliente(clienteId: number | null) {
  return useQuery<CxCClienteResponse>({
    queryKey: ['cxc-cliente', clienteId],
    queryFn: () => api.get<CxCClienteResponse>(`/api/clientes/${clienteId}/cuentas-por-cobrar`),
    enabled: clienteId !== null,
  });
}

export function useRegistrarPago(clienteId: number) {
  const qc = useQueryClient();
  return useMutation<{ mensaje: string; nuevo_saldo: number }, { status?: number; detail?: string }, { monto: number; descripcion: string }>({
    mutationFn: ({ monto, descripcion }) =>
      api.post<{ mensaje: string; nuevo_saldo: number }>(
        `/api/clientes/${clienteId}/registrar-pago?monto=${monto}&descripcion=${encodeURIComponent(descripcion)}`,
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['cxc-cliente', clienteId] });
      qc.invalidateQueries({ queryKey: ['estado-cuenta', clienteId] });
      qc.invalidateQueries({ queryKey: ['clientes'] });
    },
  });
}

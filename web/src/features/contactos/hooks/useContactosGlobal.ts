import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { ContactosResponse, ContactoOrden } from '../types';

export function useContactosGlobal(q: string, clienteId: number | null) {
  const params = new URLSearchParams();
  if (q.trim()) params.set('q', q.trim());
  if (clienteId != null) params.set('cliente_id', String(clienteId));
  const qs = params.toString();
  return useQuery<ContactosResponse>({
    queryKey: ['contactos', 'global', q.trim(), clienteId],
    queryFn: () => api.get<ContactosResponse>(`/api/contactos/${qs ? `?${qs}` : ''}`),
    staleTime: 30_000,
  });
}

export function useContactoHistorial(id: number | null) {
  return useQuery<ContactoOrden[]>({
    queryKey: ['contacto', 'historial', id],
    queryFn: () => api.get<ContactoOrden[]>(`/api/contactos/${id}/historial`),
    enabled: id !== null,
  });
}

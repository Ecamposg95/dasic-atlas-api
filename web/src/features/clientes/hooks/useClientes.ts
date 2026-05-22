import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Cliente } from '../types';

// Shape completo — distinto de features/cotizador/hooks/useClientes.ts
// que tiene un shape reducido para el ClientPicker.

export function useClientes() {
  return useQuery<Cliente[]>({
    queryKey: ['clientes'],
    queryFn: () => api.get<Cliente[]>('/api/clientes/'),
    staleTime: 60_000,
  });
}

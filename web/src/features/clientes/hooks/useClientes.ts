import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Cliente } from '../types';

// Shape completo — distinto de features/cotizador/hooks/useClientes.ts
// que tiene un shape reducido para el ClientPicker.
// Paginación via skip/limit (backend retorna array plano).
// pageSize: pasa 500 para obtener todos (uso en selectores/pickers).

export function useClientes(page = 1, q = '', pageSize = 50) {
  const skip = (page - 1) * pageSize;
  const params = new URLSearchParams();
  params.set('skip', String(skip));
  params.set('limit', String(pageSize));
  if (q.trim()) params.set('q', q.trim());
  return useQuery<Cliente[]>({
    queryKey: ['clientes', page, q.trim(), pageSize],
    queryFn: () => api.get<Cliente[]>(`/api/clientes/?${params.toString()}`),
    placeholderData: keepPreviousData,
    staleTime: 60_000,
  });
}

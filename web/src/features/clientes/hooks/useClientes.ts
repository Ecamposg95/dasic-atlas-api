import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Cliente } from '../types';

type ListParams = {
  page?: number;
  q?: string;
  pageSize?: number;
  estatus?: string;
  sort?: string;
  dir?: 'asc' | 'desc';
};

export function useClientes({ page = 1, q = '', pageSize = 50, estatus = '', sort = '', dir = 'asc' }: ListParams = {}) {
  const skip = (page - 1) * pageSize;
  const params = new URLSearchParams();
  params.set('skip', String(skip));
  params.set('limit', String(pageSize));
  if (q.trim()) params.set('q', q.trim());
  if (estatus) params.set('estatus', estatus);
  if (sort) { params.set('sort', sort); params.set('dir', dir); }
  return useQuery<Cliente[]>({
    queryKey: ['clientes', page, q.trim(), pageSize, estatus, sort, dir],
    queryFn: () => api.get<Cliente[]>(`/api/clientes/?${params.toString()}`),
    placeholderData: keepPreviousData,
    staleTime: 60_000,
  });
}

export function useClientesCount(q = '', estatus = '') {
  const params = new URLSearchParams();
  if (q.trim()) params.set('q', q.trim());
  if (estatus) params.set('estatus', estatus);
  return useQuery<{ total: number }>({
    queryKey: ['clientes-count', q.trim(), estatus],
    queryFn: () => api.get<{ total: number }>(`/api/clientes/count?${params.toString()}`),
    staleTime: 60_000,
  });
}

export function useBulkEstatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { ids: number[]; estatus: string }) =>
      api.patch<{ updated: number }>('/api/clientes/bulk-estatus', body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['clientes'] });
      qc.invalidateQueries({ queryKey: ['clientes-count'] });
    },
  });
}

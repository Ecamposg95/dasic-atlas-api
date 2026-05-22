import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Proveedor } from '../types';

export function useProveedores() {
  return useQuery<Proveedor[]>({
    queryKey: ['compras-proveedores'],
    queryFn: () => api.get<Proveedor[]>('/api/compras/proveedores'),
    staleTime: 5 * 60 * 1_000, // 5 minutos
  });
}

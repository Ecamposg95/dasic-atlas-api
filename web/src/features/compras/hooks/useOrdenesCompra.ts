import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { OrdenCompraListItem } from '../types';

export function useOrdenesCompra() {
  return useQuery<OrdenCompraListItem[]>({
    queryKey: ['ordenesCompra'],
    queryFn: () => api.get<OrdenCompraListItem[]>('/api/compras/historial'),
    staleTime: 30_000, // 30 segundos — datos operativos, refrescar con frecuencia
  });
}

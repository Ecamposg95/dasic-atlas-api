import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export type Proveedor = {
  id: number;
  nombre_empresa: string;
};

/**
 * Lista plana de proveedores (5 min staleTime). Reusada por
 * AgregarFantasmaModal para el picker y por sugerir-oc UI.
 */
export function useProveedores() {
  return useQuery<Proveedor[]>({
    queryKey: ['proveedores'],
    queryFn: () => api.get<Proveedor[]>('/api/compras/proveedores'),
    staleTime: 5 * 60 * 1_000,
  });
}

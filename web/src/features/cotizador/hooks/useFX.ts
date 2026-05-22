import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, type ApiError } from '@/lib/api';

// Shape REAL del backend (`app/schemas/fx.py::TipoCambioDiaResponse`):
//   { fecha, usd_mxn, fuente, obtenido_en }
// `usd_mxn` viene como Decimal serializado a string por Pydantic v2.
export type FXResponse = {
  fecha: string;
  usd_mxn: number | string;
  fuente: string;
  obtenido_en: string;
};

export function useFX() {
  return useQuery<FXResponse>({
    queryKey: ['fx', 'usd-mxn'],
    queryFn: () => api.get<FXResponse>('/api/fx/usd-mxn'),
    staleTime: 5 * 60_000,
  });
}

export function useFXRefresh() {
  const qc = useQueryClient();
  return useMutation<FXResponse, ApiError, void>({
    mutationFn: () => api.post<FXResponse>('/api/fx/refresh'),
    onSuccess: (data) => {
      qc.setQueryData(['fx', 'usd-mxn'], data);
    },
  });
}

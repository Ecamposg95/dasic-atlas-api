import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

// Shape real del backend (`app/routers/ventas.py:1262`): `page`, `page_size`,
// `items[]`. NO incluye `total` global, sólo el page-slice. La paginación es
// "tiene más" derivado de `items.length === page_size`.
export type BorradorItem = {
  id: number;
  folio: string;
  cliente_id: number | null;
  cliente_nombre: string | null;
  moneda: 'MXN' | 'USD';
  total: number;
  tipo_cambio: number;
  actualizado_en: string | null;
  edad_dias: number | null;
  pdf_desactualizado: boolean;
  lineas_count: number;
};

export type BorradoresResponse = {
  page: number;
  page_size: number;
  items: BorradorItem[];
};

export function useBorradores(page: number = 1) {
  return useQuery<BorradoresResponse>({
    queryKey: ['ventas', 'borradores', page],
    queryFn: () =>
      api.get<BorradoresResponse>(`/api/ventas/borradores?page=${page}&page_size=10`),
    staleTime: 30_000,
  });
}

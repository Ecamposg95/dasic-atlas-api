import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

// Shape devuelto por GET /api/fantasmas/ (`app/routers/fantasmas.py::_serialize_fantasma_row`).
// Listamos solo los campos que el cotizador consume al agregar al cart.
export type FantasmaPrevio = {
  id: number;
  descripcion: string;
  sku_libre: string | null;
  costo_referencia: number;
  moneda: string;
  proveedor_sugerido_id: number | null;
  proveedor_sugerido_nombre: string | null;
  estado: string;
  veces_solicitado: number;
  ultimo_visto_en: string | null;
};

// El endpoint devuelve un objeto con `items: [...]`. En algunas versiones
// legacy puede venir como array suelto; nos defendemos contra ambas formas.
type FantasmasResponse = { items: FantasmaPrevio[] } | FantasmaPrevio[];

function normalize(data: FantasmasResponse | undefined): FantasmaPrevio[] {
  if (!data) return [];
  if (Array.isArray(data)) return data;
  return data.items ?? [];
}

export function useFantasmasSearch(q: string) {
  const [debouncedQ, setDebouncedQ] = useState(q);
  useEffect(() => {
    const t = setTimeout(() => setDebouncedQ(q), 300);
    return () => clearTimeout(t);
  }, [q]);

  const trimmed = debouncedQ.trim();
  // Permitir lista inicial sin query (los más recientes) y buscar con >=2 chars.
  const enabled = trimmed.length === 0 || trimmed.length >= 2;

  const query = useQuery<FantasmasResponse>({
    queryKey: ['cotizador', 'fantasmas', 'search', trimmed],
    queryFn: () =>
      api.get<FantasmasResponse>(
        `/api/fantasmas/?estado=PENDIENTE&page_size=50${trimmed ? `&q=${encodeURIComponent(trimmed)}` : ''}`,
      ),
    staleTime: 30_000,
    enabled,
  });

  return {
    ...query,
    items: normalize(query.data),
  };
}

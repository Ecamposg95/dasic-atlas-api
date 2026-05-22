import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

// Shape REAL del backend (`app/routers/ventas.py:2007` → app/data/sinonimos.json):
//
//   { fuente, actualizado, descripcion, entradas: [{ canonico, sinonimos[], ... }] }
//
// El plan asume `{ diccionario: Record<string, string[]> }`; aquí preservamos el shape
// crudo del backend y exponemos un `dict` derivado para que `expandSinonimos` lo use.
export type SinonimoEntry = {
  canonico: string;
  sinonimos: string[];
  categoria?: string;
  marcas_comunes?: string[];
};

export type SinonimosResponse = {
  fuente?: string;
  actualizado?: string;
  descripcion?: string;
  entradas?: SinonimoEntry[];
};

export type SinonimosData = {
  raw: SinonimosResponse;
  dict: Record<string, string[]>;
};

function buildDict(resp: SinonimosResponse): Record<string, string[]> {
  const dict: Record<string, string[]> = {};
  for (const e of resp.entradas ?? []) {
    const key = (e.canonico || '').toLowerCase().trim();
    if (!key) continue;
    const syns = (e.sinonimos ?? [])
      .map((s) => (s || '').toLowerCase().trim())
      .filter(Boolean);
    if (syns.length > 0) dict[key] = syns;
  }
  return dict;
}

export function useSinonimos() {
  return useQuery<SinonimosData>({
    queryKey: ['ventas', 'sinonimos'],
    queryFn: async () => {
      const raw = await api.get<SinonimosResponse>('/api/ventas/sinonimos');
      return { raw, dict: buildDict(raw) };
    },
    staleTime: 30 * 60_000, // 30 min — el diccionario cambia muy poco
  });
}

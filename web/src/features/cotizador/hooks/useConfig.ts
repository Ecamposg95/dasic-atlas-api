import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { CotizadorConfig } from '../types';

const DEFAULTS: CotizadorConfig = {
  iva_rate: 0.16,
  iva_pct_label: '16%',
  quote_validity_days: 15,
};

export function useConfig() {
  const q = useQuery<CotizadorConfig>({
    queryKey: ['cotizador-config'],
    queryFn: () => api.get<CotizadorConfig>('/api/ventas/config/cotizador-defaults'),
    staleTime: 60 * 60_000, // 1h — la config casi nunca cambia
  });
  // Fallback síncrono para el render inicial: usamos defaults hardcoded mientras
  // el query corre. Cuando llega, sustituye.
  return { ...q, config: q.data ?? DEFAULTS };
}

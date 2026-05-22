import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { ConversionCotizacionesResponse } from '../types';

export function useConversionCotizaciones(dias: number) {
  return useQuery({
    queryKey: ['reportes-servicio', 'conversion-cotizaciones', dias],
    queryFn: () =>
      api.get<ConversionCotizacionesResponse>(
        `/api/reportes/conversion-cotizaciones?dias=${dias}`,
      ),
  });
}

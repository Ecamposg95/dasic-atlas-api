// Hook para "Última cotización del cliente" (Phase 5 — Task 5.3).
//
// Shape REAL del backend (`app/routers/ventas.py::ultima_cotizacion_cliente`):
//   {
//     id, folio, fecha, dias_atras, total, moneda, estatus
//   }
// Devuelve `null` si el cliente no tiene cotizaciones (no error 404).
// El campo correcto es `fecha` — NO `fecha_creacion` como decía el plan.

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export type UltimaCotResponse = {
  id: number;
  folio: string;
  fecha: string | null;
  dias_atras: number | null;
  total: number;
  moneda: string;
  estatus: string;
};

export function useUltimaCot(clienteId: number | null) {
  return useQuery<UltimaCotResponse | null>({
    queryKey: ['ventas', 'ultima-cotizacion-cliente', clienteId],
    queryFn: () =>
      api.get<UltimaCotResponse | null>(
        `/api/ventas/ultima-cotizacion-cliente/${clienteId}`,
      ),
    enabled: clienteId != null,
    staleTime: 60_000,
  });
}

export interface HistorialItem {
  id: number;
  folio: string;
  fecha: string; // ISO date
  fecha_vencimiento: string | null;
  cliente: string;
  total: number | string;
  moneda: string;
  tipo_cambio: number | string;
  estatus: string; // backend EstatusOrden: 'cotizacion' | 'pendiente' | 'pagada' | 'cancelada'
  version: number;
  cotizacion_origen_id: number | null;
  edad_dias: number;
  dias_restantes: number | null;
  esta_vencida: boolean;
}

export type EstatusFilter = 'TODOS' | 'COTIZACION' | 'PENDIENTE' | 'PAGADA' | 'CANCELADA';
export type VencimientoFilter = 'TODAS' | 'vigente' | 'vencida' | 'sin_fecha';

export interface RecotizarResult {
  id: number;
  folio: string;
}

export interface ConvertirResult {
  id: number;
  folio_venta: string;
}

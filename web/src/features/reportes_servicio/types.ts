// Tipos para la feature de Reportes operativos — refleja los responses de
// GET /api/reportes/conversion-cotizaciones, /top-servicios,
// /fantasmas-por-proveedor, /vencimientos-proximos, /ordenes-pendientes-entrega

export type ConversionCotizacionesResponse = {
  dias: number;
  total_cotizaciones: number;
  convertidas: number;
  canceladas: number;
  activas: number;
  tasa_conversion_pct: number;
  tasa_cancelacion_pct: number;
  tiempo_medio_conversion_dias: number | null;
  monto_convertido_mxn: number;
  monto_pipeline_activo_mxn: number;
};

export type TopServicioItem = {
  servicio_id: number | null;
  nombre: string;
  cantidad_lineas: number;
  cantidad_total: number;
  monto_mxn: number;
};

export type TopServiciosResponse = {
  dias: number;
  items: TopServicioItem[];
  total_lineas_servicio: number;
  monto_total_servicios_mxn: number;
};

export type FantasmaItem = {
  id: number;
  descripcion: string;
  veces_solicitado: number;
  costo_referencia: number;
  moneda: string;
};

export type FantasmaGrupo = {
  proveedor_id: number | null;
  proveedor_nombre: string;
  cantidad: number;
  veces_solicitado_total: number;
  items: FantasmaItem[];
};

export type FantasmasPorProveedorResponse = {
  grupos: FantasmaGrupo[];
  total_pendientes: number;
};

export type VencimientoItem = {
  id: number;
  folio: string;
  cliente_nombre: string | null;
  vendedor_nombre: string | null;
  moneda: string;
  total: number;
  total_mxn: number;
  fecha_vencimiento: string | null;
  dias_restantes: number;
};

export type VencimientosProximosResponse = {
  dias_horizonte: number;
  total_cotizaciones: number;
  monto_total_mxn: number;
  items: VencimientoItem[];
};

export type OrdenPendienteItem = {
  id: number;
  folio: string;
  cliente_nombre: string | null;
  estatus: string;
  moneda: string;
  total: number;
  total_mxn: number;
  fecha_creacion: string | null;
  dias_desde_venta: number | null;
};

export type OrdenesPendientesEntregaResponse = {
  total: number;
  monto_total_mxn: number;
  items: OrdenPendienteItem[];
};

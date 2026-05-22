// Tipos curados para el Dashboard.
// Shape derivado de los handlers en app/routers/dashboard.py.

// ---------- /api/dashboard/hero ----------

export type SparklinePoint = {
  d: string; // YYYY-MM-DD
  v: number;
};

export type HeroVentas = {
  monto_mxn: number;
  count: number;
  delta_pct: number | null;
  sparkline_30d: SparklinePoint[];
};

export type HeroPipeline = {
  monto_mxn: number;
  count: number;
  ticket_promedio_mxn: number;
};

export type HeroConversion = {
  tasa_pct: number;
  target_pct: number;
  sparkline_4w: number[];
};

export type HeroMargen = {
  pct: number;
  muestra_lineas: number;
};

export type HeroResponse = {
  window: string;
  ventas: HeroVentas;
  pipeline: HeroPipeline;
  conversion: HeroConversion;
  margen: HeroMargen;
};

// ---------- /api/dashboard/pipeline ----------

export type OrdenBreve = {
  id: number;
  folio: string;
  cliente: string;
  contacto: string | null;
  monto_mxn: number;
  moneda: string;
  vendedor: string | null;
  fecha: string | null;
  // Only on pipeline items:
  edad_dias?: number;
  dias_restantes?: number | null;
  // Only on convertida items:
  estatus?: string;
};

export type PipelineColumna = {
  items: OrdenBreve[];
  count: number;
  monto_total_mxn: number;
};

export type PipelineResponse = {
  nueva: PipelineColumna;
  seguimiento: PipelineColumna;
  por_vencer: PipelineColumna;
  vencida: PipelineColumna;
  convertida: PipelineColumna;
};

// ---------- /api/dashboard/alertas ----------

export type AlertaPorVencer = OrdenBreve & {
  dias_restantes: number | null;
};

export type StockCritico = {
  producto_id: number;
  sku: string;
  nombre: string;
  marca: string | null;
  stock_actual: number;
  stock_minimo: number;
  cotizaciones_activas: number;
  cantidad_cotizada: number;
};

export type SaldoVencido = {
  id: number;
  empresa: string;
  contacto: string | null;
  saldo: number;
  dias_sin_pago: number;
};

export type OcBorrador = {
  id: number;
  folio: string;
  proveedor: string | null;
  total: number;
  moneda: string;
  fecha: string | null;
};

export type AlertasResponse = {
  por_vencer_3d: AlertaPorVencer[];
  stock_critico_cotizado: StockCritico[];
  saldos_vencidos: SaldoVencido[];
  oc_borrador: OcBorrador[];
};

// ---------- /api/dashboard/tops ----------

export type TopCliente = {
  id: number;
  empresa: string;
  saldo: number;
  orden_count: number;
  monto_mxn: number;
};

export type TopProducto = {
  id: number;
  sku: string;
  nombre: string;
  marca: string | null;
  cantidad_total: number;
  apariciones: number;
  stock_actual: number;
  stock_minimo: number;
  stock_riesgo: boolean;
};

export type TopVendedor = {
  id: number;
  nombre: string;
  orden_count: number;
  monto_mxn: number;
};

export type TopsResponse = {
  clientes: TopCliente[];
  productos: TopProducto[];
  vendedores: TopVendedor[];
  ve_equipo: boolean;
};

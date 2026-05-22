// Tipos para la feature de Reportes financieros — refleja los responses de
// GET /api/reportes/ventas-mes, /top-productos, /top-clientes, /ranking-vendedores

export type VentasMesItem = {
  mes: string;           // "2026-05"
  label: string;         // "may 26"
  ventas_count: number;
  ventas_mxn: number;
  cotizaciones_count: number;
  cotizaciones_mxn: number;
};

export type VentasMesResponse = {
  series: VentasMesItem[];
  meses: number;
};

export type TopProductoItem = {
  producto_id: number;
  sku: string;
  nombre: string;
  marca: string | null;
  cantidad_total: number;
  apariciones: number;
  monto_mxn: number;
};

export type TopClienteItem = {
  cliente_id: number;
  empresa: string;
  orden_count: number;
  monto_mxn: number;
  saldo_actual: number;
};

export type RankingVendedorItem = {
  usuario_id: number;
  nombre: string;
  email: string;
  orden_count: number;
  monto_mxn: number;
};

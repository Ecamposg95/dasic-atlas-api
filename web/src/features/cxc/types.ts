// Tipos para Cuentas por Cobrar.
// Shapes derivados de app/routers/cuentas_por_cobrar.py + app/services/cuentas_por_cobrar.py

export type ResumenCxC = {
  total_pendiente: number;
  total_vencido: number;
  por_vencer_7d: number;
  por_vencer_30d: number;
  n_cargos_abiertos: number;
};

export type VencimientoItem = {
  id: number;
  cliente_id: number;
  cliente: string | null;
  orden_venta_id: number | null;
  fecha: string | null;
  fecha_vencimiento: string | null;
  monto: number;
  monto_pagado: number;
  saldo_pendiente: number;
  estatus_pago: string;
  dias_atraso: number;
};

export type VencimientosResponse = {
  items: VencimientoItem[];
};

export type MarcarVencidosResponse = {
  ok: boolean;
  actualizados: number;
};

// ---------------------------------------------------------------------------
// Aging report
// ---------------------------------------------------------------------------

export type AgingBucket = {
  rango: '0-30' | '31-60' | '61-90' | '90+';
  dias_min: number;
  dias_max: number | null;
  monto: number;
  count: number;
};

export type AgingResponse = {
  buckets: AgingBucket[];
  total: number;
  total_count: number;
};

// ---------------------------------------------------------------------------
// Top deudores
// ---------------------------------------------------------------------------

export type TopDeudor = {
  cliente_id: number;
  nombre_empresa: string;
  saldo: number;
  dias_max_atraso: number;
  n_cargos_abiertos: number;
};

// ---------------------------------------------------------------------------
// Pago distribuido
// ---------------------------------------------------------------------------

export type PagoDistribuidoRequest = {
  monto: number;
  descripcion?: string;
  orden_venta_ids?: number[] | null;
};

export type PagoDistribuidoResponse = {
  ok: boolean;
  monto_aplicado: number;
  monto_excedente: number;
  detalle: unknown[];
};

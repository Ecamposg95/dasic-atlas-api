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

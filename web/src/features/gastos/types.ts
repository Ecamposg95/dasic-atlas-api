// Tipos para la feature de Gastos — refleja GastoResponse de
// GET /api/gastos/ y POST/PUT /api/gastos/

export type Gasto = {
  id: number;
  categoria: string;
  descripcion: string | null;
  monto: number;
  moneda: string;
  fecha: string;
  usuario: string | null;
  usuario_id: number | null;
};

export type GastoCreate = {
  categoria: string;
  descripcion?: string | null;
  monto: number;
  moneda: string;
};

export type GastoUpdate = {
  categoria?: string;
  descripcion?: string | null;
  monto?: number;
  moneda?: string;
};

export type GastosPage = {
  page: number;
  page_size: number;
  total: number;
  items: Gasto[];
};

export type GastosFiltros = {
  q?: string;
  categoria?: string;
  fechaDesde?: string;
  fechaHasta?: string;
};

// Tipos para la feature de Clientes.
// Shape derivado de GET /api/clientes/.

export type MonedaCredito = 'MXN' | 'USD';

export type Cliente = {
  id: number;
  nombre_empresa: string;
  contacto_nombre: string | null;
  rfc_tax_id: string | null;
  email: string | null;
  telefono: string | null;
  direccion: string | null;
  limite_credito: number | string;
  dias_credito: number;
  dia_corte: number | null;
  moneda_credito: MonedaCredito;
  saldo_actual: number | string;
  creado_por_id: number | null;
};

export type ClienteCreate = {
  nombre_empresa: string;
  contacto_nombre?: string | null;
  rfc_tax_id?: string | null;
  email?: string | null;
  telefono?: string | null;
  direccion?: string | null;
  limite_credito?: number;
  dias_credito?: number;
  dia_corte?: number | null;
  moneda_credito?: MonedaCredito;
};

export type ClienteUpdate = Partial<ClienteCreate>;

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
  n_contactos?: number;
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

export type Contacto = {
  id: number;
  cliente_id: number;
  nombre: string;
  cargo: string | null;
  email: string | null;
  telefono: string | null;
  es_principal: boolean;
};

export type ContactoInput = {
  nombre: string;
  cargo?: string | null;
  email?: string | null;
  telefono?: string | null;
  es_principal?: boolean;
};

export type TransaccionCuenta = {
  id: number;
  fecha: string;
  monto: number | string;
  tipo: string;
  descripcion: string;
  referencia_id: number | null;
};

export type CargoAbierto = {
  id: number;
  orden_venta_id: number | null;
  folio: string | null;
  fecha: string | null;
  fecha_vencimiento: string | null;
  descripcion: string;
  monto: number;
  monto_pagado: number;
  saldo_pendiente: number;
  estatus_pago: string;
  dias_atraso: number;
};

export type CxCClienteResponse = {
  cliente: {
    id: number;
    nombre_empresa: string;
    saldo_actual: number;
    limite_credito: number;
    dias_credito: number;
    moneda_credito: string;
  };
  cargos: CargoAbierto[];
};

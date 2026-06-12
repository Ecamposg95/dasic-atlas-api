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

export type ContactoGlobal = Contacto & { empresa_nombre: string | null };

export type ContactosResponse = {
  page: number;
  page_size: number;
  total: number;
  items: ContactoGlobal[];
};

export type ContactoOrden = {
  id: number;
  folio: string;
  fecha: string | null;
  estatus: string;
  total: number;
  moneda: string | null;
};

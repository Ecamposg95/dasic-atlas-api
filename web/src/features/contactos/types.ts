export type ContactoGlobal = {
  id: number;
  cliente_id: number;
  empresa_nombre: string | null;
  nombre: string;
  cargo: string | null;
  email: string | null;
  telefono: string | null;
  es_principal: boolean;
};

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

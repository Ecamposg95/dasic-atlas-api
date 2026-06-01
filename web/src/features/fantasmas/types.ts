// Tipos curados para la feature de Productos Fantasma.
// Shape derivado de GET /api/fantasmas/ y GET /api/fantasmas/{id}.

export type EstadoFantasma =
  | 'PENDIENTE'
  | 'EN_OC'
  | 'RECIBIDO'
  | 'PROMOVIDO'
  | 'DESCARTADO';

export type Moneda = 'MXN' | 'USD';

export type Fantasma = {
  id: number;
  descripcion: string;
  sku_libre: string | null;
  proveedor_sugerido_id: number | null;
  proveedor_sugerido_nombre: string | null;
  veces_solicitado: number;
  costo_referencia: number;
  moneda: Moneda;
  marca: string | null;
  marca_id: number | null;
  clave_prod_serv: string | null;
  clave_unidad_sat: string | null;
  observaciones: string | null;
  estado: EstadoFantasma;
  creado_en: string | null;
  ultimo_visto_en: string | null;
  promovido_a_producto_id: number | null;
};

export type FantasmaDetalle = Omit<Fantasma, 'proveedor_sugerido_nombre'> & {
  cotizaciones: Array<{
    id: number;
    folio: string;
    estatus: string;
    cantidad: number;
  }>;
};

export type FantasmasResponse = {
  page: number;
  page_size: number;
  items: Fantasma[];
};

export type FantasmaUpdatePayload = {
  descripcion_original?: string;
  sku_libre?: string;
  costo_referencia?: number;
  moneda_referencia?: Moneda;
  proveedor_sugerido_id?: number | null;
  marca?: string | null;
  marca_id?: number | null;
  clave_prod_serv?: string | null;
  clave_unidad_sat?: string | null;
  observaciones?: string | null;
};

export type Proveedor = {
  id: number;
  nombre_empresa: string;
};

export type FantasmaFiltros = {
  q: string;
  estado: EstadoFantasma | '';
  proveedor_id: number | null;
  moneda: Moneda | '';
  sinAsignar: boolean;
};

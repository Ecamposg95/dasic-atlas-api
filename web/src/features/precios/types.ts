// Tipos para Precios de Proveedores.
// Shapes derivados de app/routers/precios.py y app/schemas/precios.py

export type Moneda = 'MXN' | 'USD';

export type PrecioProveedor = {
  id: number;
  proveedor_id: number;
  proveedor_nombre: string | null;
  producto_id: number | null;
  producto_nombre: string | null;
  descripcion_busqueda: string | null;
  sku_libre: string | null;
  precio: number;
  moneda: Moneda;
  fecha_vigencia_desde: string | null;
  fecha_vigencia_hasta: string | null;
  notas: string | null;
  fuente: string;
  creado_en: string;
};

export type PrecioProveedorCreate = {
  proveedor_id: number;
  producto_id?: number | null;
  descripcion_busqueda?: string | null;
  sku_libre?: string | null;
  precio: number;
  moneda?: Moneda;
  fecha_vigencia_desde?: string | null;
  fecha_vigencia_hasta?: string | null;
  notas?: string | null;
};

export type PreciosListResponse = {
  page: number;
  page_size: number;
  items: PrecioProveedor[];
};

export type ComparativaItem = {
  proveedor_id: number;
  proveedor_nombre: string | null;
  precio: number;
  moneda: Moneda;
  fecha_vigencia_desde: string | null;
  fuente: string;
  precio_id: number;
};

export type ComparativaResponse = {
  items: ComparativaItem[];
  total: number;
};

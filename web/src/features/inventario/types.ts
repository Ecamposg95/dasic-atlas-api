// Tipos curados para la feature de Inventario (Productos).
// Shape derivado de GET /api/productos, POST /api/productos/, PUT /api/productos/{id}.

export type Moneda = 'MXN' | 'USD';

export type Producto = {
  id: number;
  sku: string | null;
  sku_comercial: string | null;
  nombre: string;
  descripcion: string | null;
  marca: string | null;
  marca_id: number | null;
  categoria: string | null;
  unidad: string;
  stock_actual: number;
  stock_minimo: number;
  moneda_compra: Moneda;
  costo_compra?: number; // solo admin
  proveedor_principal_id: number | null;
  proveedor_alterno_id: number | null;
  tiempo_entrega_dias: number;
  es_servicio: boolean;
  precio_publico: number | null;
  precio_mayorista: number;
  precio_distribuidor: number;
};

export type ProductoCreate = {
  sku?: string | null;
  sku_comercial?: string | null;
  nombre: string;
  descripcion?: string | null;
  marca_id?: number | null;
  categoria?: string | null;
  unidad?: string;
  stock_actual: number;
  stock_minimo?: number;
  moneda_compra?: Moneda;
  costo_compra: number;
  proveedor_principal_id?: number | null;
  proveedor_alterno_id?: number | null;
  tiempo_entrega_dias?: number;
  es_servicio?: boolean;
  precio_publico?: number | null;
  precio_mayorista?: number;
  precio_distribuidor?: number;
};

export type ProductoUpdate = {
  sku?: string | null;
  sku_comercial?: string | null;
  nombre?: string;
  descripcion?: string | null;
  marca_id?: number | null;
  categoria?: string | null;
  unidad?: string;
  stock_actual?: number;
  stock_minimo?: number;
  moneda_compra?: Moneda;
  costo_compra?: number;
  proveedor_principal_id?: number | null;
  proveedor_alterno_id?: number | null;
  tiempo_entrega_dias?: number;
  es_servicio?: boolean;
  precio_publico?: number | null;
  precio_mayorista?: number;
  precio_distribuidor?: number;
};

export type Marca = {
  id: number;
  nombre: string;
};

export type Proveedor = {
  id: number;
  nombre_empresa: string;
};

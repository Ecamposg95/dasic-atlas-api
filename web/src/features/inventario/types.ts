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
  clave_prod_serv?: string | null;
  clave_unidad_sat?: string | null;
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
  clave_prod_serv?: string | null;
  clave_unidad_sat?: string | null;
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
  clave_prod_serv?: string | null;
  clave_unidad_sat?: string | null;
};

export type Marca = {
  id: number;
  nombre: string;
};

export type Proveedor = {
  id: number;
  nombre_empresa: string;
};

// GET /api/productos/{id}/cardex
export type MovimientoKardex = {
  id: number;
  tipo: string; // 'ENTRADA' | 'SALIDA' | 'AJUSTE' | 'RESERVA' | 'LIBERACION'
  cantidad: number;
  stock_resultante: number;
  referencia_tipo: string | null;
  referencia_id: number | null;
  motivo: string | null;
  creado_en: string | null;
};

export type CardexProducto = {
  identificacion: {
    id: number;
    sku: string | null;
    sku_comercial: string | null;
    nombre: string;
    descripcion: string | null;
    imagen_url: string | null;
    es_servicio: boolean;
  };
  clasificacion: {
    marca: string | null;
    marca_id: number | null;
    categoria: string | null;
    unidad: string;
  };
  fiscales: {
    clave_prod_serv: string | null;
    clave_unidad_sat: string | null;
    objeto_imp: string | null;
    descripcion_fiscal: string | null;
  };
  inventario: {
    stock_actual: number;
    stock_minimo: number;
    moneda_compra: string;
    costo_compra: number;
    proveedor_principal_id: number | null;
    proveedor_alterno_id: number | null;
  };
  historico: {
    primer_movimiento: string | null;
    ultimo_movimiento: string | null;
    total_movimientos: number;
    ultimo_uso_en_cotizacion: string | null;
  };
  movimientos: MovimientoKardex[];
};

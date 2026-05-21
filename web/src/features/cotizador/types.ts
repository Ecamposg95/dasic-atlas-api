// Tipos del cotizador. Subset curado de los DTOs del backend; reflejan solo
// lo que el MVP usa. Cuando los endpoints cambien, los regeneramos con
// `npm run types:gen` y comparamos contra esto.

export type Producto = {
  id: number;
  sku: string;
  sku_comercial: string | null;
  nombre: string;
  marca: string | null;
  costo_compra: number;
  moneda_compra: 'MXN' | 'USD';
  stock_actual: number;
};

export type Cliente = {
  id: number;
  nombre_empresa: string;
  contacto_nombre: string | null;
  rfc_tax_id: string | null;
};

export type CotizadorConfig = {
  iva_rate: number;
  iva_pct_label: string;
  quote_validity_days: number;
};

export type Moneda = 'MXN' | 'USD';
export type EntregaUnidad = 'dias' | 'semanas' | null;

export type CartItem = {
  // UID local para keying en React. Si la línea viene del backend, usamos
  // `linea-<detalle_id>`. Si se agregó en sesión, `nuevo-<id-producto>-<random>`.
  uid: string;

  // Snapshot del catálogo al agregar — usado para detectar overrides.
  producto_id: number;
  sku: string;
  nom: string;
  cost: number;
  productCurrency: Moneda;
  sku_original: string;
  nom_original: string;
  cost_original: number;
  max: number; // stock_actual al momento de agregar (puede quedar stale)

  // Campos editables por el usuario:
  qty: number;
  utilidad: number;       // 0-99 (porcentaje)
  descuento: number;      // 0-100 (porcentaje)
  entrega_min: number | null;
  entrega_max: number | null;
  entrega_unidad: EntregaUnidad;
  observaciones_linea: string;

  // Solo presente cuando la línea viene de una cotización cargada (modo edit).
  detalle_id?: number;
};

// Una línea NO soportada en MVP (fantasma/servicio). Solo se preserva para mostrar
// el banner; no entra en `cart`.
export type LineaNoSoportada = {
  detalle_id: number;
  descripcion: string;
  cantidad: number;
};

// Respuesta del GET /api/ventas/{id} (subset MVP).
export type OrdenVentaDetail = {
  id: number;
  folio: string;
  estatus: string;
  cliente_id: number | null;
  moneda: string;
  tipo_cambio: number | string;
  fecha_creacion: string | null;
  fecha_vencimiento: string | null;
  observaciones: string | null;
  terminos_condiciones: string | null;
  version: number;
  detalles: Array<{
    id: number;
    producto_id: number | null;
    servicio_id: number | null;
    sku_libre: string | null;
    descripcion_libre: string | null;
    moneda_origen_linea: string | null;
    costo_base_linea: number | string;
    cantidad: number;
    utilidad_aplicada: number | string;
    descuento_aplicado: number | string;
    tipo_linea: string;
    entrega_min: number | null;
    entrega_max: number | null;
    entrega_unidad: string | null;
    observaciones_linea: string | null;
    producto: {
      sku: string;
      sku_comercial: string | null;
      nombre: string;
      costo_compra: number | string;
    } | null;
    servicio: {
      codigo: string;
      nombre: string;
    } | null;
  }>;
};

// Payload para POST/PUT /api/ventas (subset MVP, solo líneas de catálogo).
export type DetalleOrdenCreate = {
  producto_id: number;
  servicio_id: null;
  cantidad: number;
  utilidad: number;
  descuento: number;
  moneda_origen: Moneda;
  sku_libre: string | null;
  descripcion_libre: string | null;
  costo_unitario: number | null;
  tipo_linea: 'producto_catalogo';
  proveedor_sugerido_id: null;
  entrega_min: number | null;
  entrega_max: number | null;
  entrega_unidad: EntregaUnidad;
  observaciones_linea: string | null;
};

export type OrdenVentaCreate = {
  cliente_id: number | null;
  moneda: Moneda;
  tipo_cambio: number;
  fecha_creacion: string | null;
  fecha_vencimiento: string | null;
  observaciones: string | null;
  terminos_condiciones: string | null;
  tipo: 'cotizacion';
  detalles: DetalleOrdenCreate[];
};

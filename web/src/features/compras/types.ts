// Tipos curados para la feature de Compras (Órdenes de Compra).
// Shapes derivados de los endpoints en app/routers/compras.py.

/** Estatus real que devuelve el backend (cadenas libres del modelo). */
export type EstatusOC =
  | 'borrador'
  | 'enviada'
  | 'confirmada'
  | 'recibido'          // backend usa "recibido" (sin a)
  | 'recibida_parcial'
  | 'pagado'
  | 'cancelada';

export type Moneda = 'MXN' | 'USD';

// ── GET /api/compras/historial ────────────────────────────────────────────────
export type OrdenCompraListItem = {
  id: number;
  folio: string | null;
  fecha: string;           // ISO string
  proveedor: string;       // nombre_empresa directo en el listado
  total: number;
  moneda: Moneda;
  estatus: EstatusOC;
  cotizacion_id: number | null;
};

// ── GET /api/compras/{id}/json (_serializar_oc) ───────────────────────────────
export type OrdenCompraDetalleProd = {
  id: number;
  sku: string;
  nombre: string;
};

export type OrdenCompraLinea = {
  id: number;
  producto_id: number | null;
  producto: OrdenCompraDetalleProd | null;
  sku_libre: string | null;
  descripcion_libre: string | null;
  moneda_origen_linea: string | null;
  costo_base_linea: number;
  cantidad: number;
  costo_unitario: number;
  marca?: string | null;
  clave_prod_serv?: string | null;
  clave_unidad_sat?: string | null;
  cantidad_recibida: number;
  fecha_recepcion: string | null;
};

export type OrdenCompra = {
  id: number;
  folio: string | null;
  fecha: string | null;
  estatus: EstatusOC;
  proveedor_id: number;
  proveedor: string | null;
  cotizacion_id: number | null;
  moneda: Moneda;
  tipo_cambio: number;
  total: number;
  detalles: OrdenCompraLinea[];
};

// ── GET /api/compras/proveedores ──────────────────────────────────────────────
export type Proveedor = {
  id: number;
  nombre_empresa: string;
  contacto_nombre: string | null;
  telefono: string | null;
  email: string | null;
  saldo_actual: number;
};

// ── POST /api/compras/proveedores ─────────────────────────────────────────────
export type ProveedorCreatePayload = {
  nombre_empresa: string;
  contacto_nombre?: string;
  telefono?: string;
  email?: string;
};

// ── POST /api/compras/{id}/recibir ────────────────────────────────────────────
export type RecepcionResponse = {
  ok: boolean;
  folio: string;
  productos_ingresados: number;
};

// ── POST /api/compras/{id}/recibir-parcial ────────────────────────────────────
export type RecepcionParcialPayload = {
  lineas: { detalle_compra_id: number; cantidad: number }[];
  fecha?: string | null;
};

export type RecepcionParcialResponse = {
  ok: boolean;
  folio: string | null;
  estatus: EstatusOC;
  procesados: number;
};

// ── POST /api/compras/registrar-pago ─────────────────────────────────────────
// El endpoint usa query params: proveedor_id, monto, ref
// Devuelve { mensaje, nuevo_saldo }
export type PagoResponse = {
  mensaje: string;
  nuevo_saldo: number;
};

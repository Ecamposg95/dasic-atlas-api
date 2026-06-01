// Tipos para la feature de Remisiones — refleja los responses de
// GET /api/remisiones/ y GET /api/remisiones/{id}

export type RemisionItem = {
  id: number;
  folio: string;
  orden_venta_id: number | null;
  orden_folio: string | null;
  cliente_nombre: string | null;
  fecha_remision: string | null;
  transportista: string | null;
  recibido_por: string | null;
  recibido_at: string | null;
  lineas_count: number;
};

export type RemisionDetalleLine = {
  id: number;
  descripcion: string | null;
  sku: string | null;
  cantidad: number;
  observaciones_linea: string | null;
};

export type RemisionDetalle = {
  id: number;
  folio: string;
  orden_venta_id: number | null;
  orden_folio: string | null;
  cliente_nombre: string | null;
  fecha_remision: string | null;
  transportista: string | null;
  recibido_por: string | null;
  recibido_at: string | null;
  observaciones: string | null;
  detalles: RemisionDetalleLine[];
};

export type RemisionesResponse = {
  page: number;
  page_size: number;
  items: RemisionItem[];
};

export type RecepcionResponse = {
  id: number;
  recibido_at: string;
  recibido_por: string;
};

// Borrador devuelto por GET /api/remisiones/orden/{id}/borrador
export type RemisionBorradorLinea = {
  detalle_orden_id: number;
  descripcion: string;
  sku: string | null;
  clave_unidad_sat: string | null;
  precio_unitario: number;
  cantidad_orden: number;
};

export type RemisionBorrador = {
  orden_venta_id: number;
  orden_folio: string | null;
  cliente_nombre: string | null;
  moneda: string | null;
  lineas: RemisionBorradorLinea[];
};

// Línea editable en la página de creación (estado local).
export type RemisionLineaEdit = {
  // Para líneas de orden: el id del DetalleOrden. Para fantasma ad-hoc: null.
  detalle_orden_id: number | null;
  incluir: boolean;
  descripcion: string;
  sku: string | null;
  clave_unidad_sat: string | null;
  precio_unitario: number;
  cantidad: number;
  cantidad_max: number | null; // null para fantasma ad-hoc (sin tope)
  observaciones_linea: string;
};

// Payload de POST /api/remisiones/
export type RemisionDetalleInput = {
  detalle_orden_id: number | null;
  descripcion: string;
  sku: string | null;
  cantidad: number;
  observaciones_linea: string | null;
  clave_unidad_sat: string | null;
  precio_unitario: number | null;
};

export type RemisionCreatePayload = {
  orden_venta_id: number;
  transportista: string | null;
  observaciones: string | null;
  mostrar_precios: boolean;
  detalles: RemisionDetalleInput[];
};

export type RemisionCreateResponse = { id: number; folio: string };

// Item de /api/ventas/historial usado en el selector de orden.
// El backend devuelve `cliente` (nombre de empresa), no `cliente_nombre`.
export type OrdenHistorialItem = {
  id: number;
  folio: string;
  estatus: string;
  cliente?: string | null;
};

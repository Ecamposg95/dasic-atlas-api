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

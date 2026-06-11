// Tipos para Reportes de Servicio (documento hijo de OrdenVenta).
//
// ⚠ NO confundir con `features/reportes_servicio/` que es el DASHBOARD
// analítico. Esta feature corresponde al documento (acta) que nace de
// una cot con líneas de tipo servicio, análogo a Remision para productos.

export type ReporteServicioDocItem = {
  id: number;
  folio: string | null;
  orden_venta_id: number;
  orden_venta_folio: string | null;
  cliente_nombre: string | null;
  fecha_reporte: string | null;
  tecnico_nombre: string | null;
  cliente_recibe_nombre: string | null;
  recibido_at: string | null;
  observaciones: string | null;
  creado_en: string | null;
};

export type ReporteServicioDocCreate = {
  orden_venta_id: number;
  tecnico_nombre?: string;
  cliente_recibe_nombre?: string;
  observaciones?: string;
};

export type ReportesServicioDocsResponse = {
  page: number;
  page_size: number;
  total: number;
  items: ReporteServicioDocItem[];
};

// Tipos para la feature de Borradores — refleja el response de
// GET /api/ventas/borradores

export type BorradorItem = {
  id: number;
  folio: string;
  cliente_id: number | null;
  cliente_nombre: string | null;
  moneda: string;
  total: number;
  tipo_cambio: number;
  actualizado_en: string | null;
  edad_dias: number | null;
  pdf_desactualizado: boolean;
  lineas_count: number;
};

export type BorradoresResponse = {
  page: number;
  page_size: number;
  items: BorradorItem[];
};

// Types for the CRM Pipeline / Kanban feature.
// Shapes mirror EXACT backend field names from /api/crm/*.

export type Pipeline = {
  id: number;
  organization_id: string;
  nombre: string;
  es_default: boolean;
  creado_en: string;
};

export type Stage = {
  id: number;
  organization_id: string;
  pipeline_id: number;
  nombre: string;
  orden: number;
  color: string | null;
  es_ganado: boolean;
  es_perdido: boolean;
};

export type Deal = {
  id: number;
  organization_id: string;
  pipeline_id: number;
  stage_id: number;
  titulo: string;
  cliente_id: number | null;
  orden_id: number | null;
  monto: number | null;
  moneda: string;
  owner_user_id: number | null;
  orden_en_stage: number;
  creado_en: string;
  actualizado_en: string;
  cerrado_en: string | null;
};

// GET /api/crm/pipelines/{pipeline_id}/board response
export type Board = {
  pipeline: Pipeline;
  stages: Stage[];
  // Keys are stage ids as STRINGS (backend serialises dict keys as strings).
  deals_by_stage: Record<string, Deal[]>;
};

// POST body
export type DealCreate = {
  pipeline_id: number;
  titulo: string;
  stage_id?: number;
  cliente_id?: number | null;
  orden_id?: number | null;
  monto?: number | null;
  moneda?: string;
  owner_user_id?: number | null;
};

// PATCH body (all optional)
export type DealUpdate = Partial<Omit<DealCreate, 'pipeline_id'>>;

// PATCH /move body
export type DealMove = {
  stage_id: number;
  orden_en_stage?: number;
};

// Tipos para Tipo de Cambio (FX).
// Shapes derivados de app/routers/fx.py y app/schemas/fx.py

export type TipoCambio = {
  fecha: string;      // YYYY-MM-DD
  usd_mxn: number;
  fuente: string;     // "BANXICO" | "FALLBACK" | "MANUAL" etc.
  obtenido_en: string; // ISO datetime
  nota?: string | null;
  actualizado_por?: number | null;
};

export type FxHistoricoResponse = {
  dias: number;
  items: TipoCambioHistorico[];
};

export type TipoCambioHistorico = {
  fecha: string;
  usd_mxn: number;
  fuente: string;
  nota: string | null;
  actualizado_por: number | null;
  obtenido_en: string | null;
};

export type FxOverridePayload = {
  fecha: string;       // YYYY-MM-DD
  usd_mxn: number;
  nota?: string | null;
};

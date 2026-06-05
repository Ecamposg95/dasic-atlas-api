export type RecordatorioVista = 'vencidos' | 'hoy' | 'proximos' | 'pendientes' | 'todos';

export type TipoAccion = 'llamada' | 'email' | 'whatsapp' | 'visita' | 'otro';

export interface Recordatorio {
  id: number;
  orden_id: number;
  usuario_id: number;
  fecha_proximo_contacto: string;
  tipo_accion: TipoAccion;
  descripcion: string | null;
  estado: 'pendiente' | 'completado' | 'pospuesto';
  creado_en: string;
  completado_en: string | null;
  folio: string | null;
  cliente: string | null;
  usuario_nombre: string | null;
  dias: number; // negative=overdue, 0=today, positive=future
}

export interface RecordatorioResumen {
  vencidos: number;
  hoy: number;
  proximos_7d: number;
  pendientes_total: number;
}

export interface RecordatorioCreate {
  orden_id: number;
  fecha_proximo_contacto: string; // ISO datetime
  tipo_accion?: TipoAccion;
  descripcion?: string;
}

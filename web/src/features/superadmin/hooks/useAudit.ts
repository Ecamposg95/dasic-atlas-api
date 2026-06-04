import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export type AuditFuente = 'cotizacion' | 'fusion_cliente';

export type AuditEvent = {
  fuente: AuditFuente;
  fecha: string;          // ISO; el backend serializa datetime como string
  usuario: string | null;
  usuario_id: number | null;
  accion: string;
  entidad: string;
  detalle: string;
  link: string | null;
};

export type AuditResponse = {
  items: AuditEvent[];
  total: number;
  page: number;
  page_size: number;
};

export type AuditFiltros = {
  fuente?: AuditFuente;
  usuario_id?: number;
  desde?: string;         // 'YYYY-MM-DD'
  hasta?: string;         // 'YYYY-MM-DD'
  page: number;
};

function buildQuery(f: AuditFiltros): string {
  const p = new URLSearchParams();
  if (f.fuente) p.set('fuente', f.fuente);
  if (f.usuario_id != null) p.set('usuario_id', String(f.usuario_id));
  if (f.desde) p.set('desde', f.desde);
  if (f.hasta) p.set('hasta', f.hasta);
  p.set('page', String(f.page));
  return p.toString();
}

export function useAudit(filtros: AuditFiltros) {
  return useQuery<AuditResponse>({
    queryKey: ['superadmin', 'audit', filtros],
    queryFn: () => api.get<AuditResponse>(`/api/superadmin/audit?${buildQuery(filtros)}`),
  });
}

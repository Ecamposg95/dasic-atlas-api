import { useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api';

// ─── Types ────────────────────────────────────────────────────────────────────

export type ReseedWhich =
  | 'ddl'
  | 'marcas'
  | 'sat'
  | 'sat_unidad'
  | 'contactos'
  | 'pipeline';

export type JobWhich = 'marcar_vencidos' | 'refresh_fx';

export type ReseedResponse = { ok: boolean; which: string; mensaje: string };
export type JobResponse = { ok: boolean; which: string; [key: string]: unknown };
export type SeedContextResponse = { [key: string]: unknown };

export type DropAllResponse = {
  status: string;
  dropped_tables: string[];
  count: number;
};

export type ApiError = { status?: number; detail?: string };

// ─── Hooks ────────────────────────────────────────────────────────────────────

export function useReseed() {
  return useMutation<ReseedResponse, ApiError, { which: ReseedWhich }>({
    mutationFn: (body) =>
      api.post<ReseedResponse>('/api/superadmin/maintenance/reseed', body),
  });
}

export function useJob() {
  return useMutation<JobResponse, ApiError, { which: JobWhich }>({
    mutationFn: (body) =>
      api.post<JobResponse>('/api/superadmin/maintenance/job', body),
  });
}

export function useSeedContext() {
  return useMutation<SeedContextResponse, ApiError, { dry_run: boolean }>({
    mutationFn: (body) =>
      api.post<SeedContextResponse>(
        '/api/superadmin/maintenance/seed-context',
        body,
      ),
  });
}

export function useDropAllTables() {
  return useMutation<DropAllResponse, ApiError, { confirm: string }>({
    mutationFn: (body) =>
      api.post<DropAllResponse>('/api/admin/drop-all-tables', body),
  });
}

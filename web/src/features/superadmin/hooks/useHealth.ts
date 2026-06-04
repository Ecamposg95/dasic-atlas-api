import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

// ─── Health response types ────────────────────────────────────────────────────

export type HealthApp = {
  version: string;
  git_sha: string | null;
  python: string;
  env: string;
  started_at: string;
  uptime_seconds: number;
};

export type HealthDb = {
  status: 'ok' | 'error' | string;
  error?: string | null;
};

export type HealthCounts = {
  usuarios: number;
  clientes: number;
  contactos: number;
  productos: number;
  ordenes_venta: number;
  remisiones: number;
  ordenes_compra: number;
  deals: number;
  quote_events: number;
  gastos: number;
  productos_fantasma: number;
};

export type HealthFx = {
  fecha: string;
  usd_mxn: number;
  fuente: string;
  obtenido_en: string;
  age_horas: number;
} | null;

export type HealthIntegraciones = {
  smtp: boolean;
  anthropic: boolean;
  banxico: boolean;
};

export type RuntimeConfigItem = {
  clave: string;
  valor_efectivo: number | string;
  default: number | string;
  overrideado: boolean;
};

export type HealthResponse = {
  app: HealthApp;
  db: HealthDb;
  counts: HealthCounts;
  fx: HealthFx;
  integraciones: HealthIntegraciones;
  runtime_config: RuntimeConfigItem[];
};

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function useHealth() {
  return useQuery<HealthResponse>({
    queryKey: ['superadmin', 'health'],
    queryFn: () => api.get<HealthResponse>('/api/superadmin/health'),
    refetchInterval: 30_000,
    staleTime: 10_000,
    retry: 1,
  });
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

/** Format uptime seconds → "Xd Xh Xm" */
export function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const parts: string[] = [];
  if (d > 0) parts.push(`${d}d`);
  if (h > 0) parts.push(`${h}h`);
  parts.push(`${m}m`);
  return parts.join(' ');
}

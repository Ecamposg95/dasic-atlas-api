import { useEffect } from 'react';
import { LayoutDashboard, AlertTriangle, TrendingUp, Package, CreditCard } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { toast } from '@/lib/toast';
import { useHero } from '../hooks/useHero';
import { usePipeline } from '../hooks/usePipeline';
import { useAlertas } from '../hooks/useAlertas';
import { useTops } from '../hooks/useTops';
import type { PipelineResponse } from '../types';

// ─── Helpers ──────────────────────────────────────────────────────────────────

function fmtMoney(n: number, moneda = 'MXN') {
  return `${moneda} $${Number(n || 0).toLocaleString('es-MX', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function fmtInt(n: number) {
  return Number(n || 0).toLocaleString('es-MX');
}

function fmtPct(n: number) {
  return `${Number(n || 0).toLocaleString('es-MX', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%`;
}

function useSafeQuery<T>(
  queryResult: { data: T | undefined; isLoading: boolean; error: unknown },
  label: string,
) {
  const { data, isLoading, error } = queryResult;
  useEffect(() => {
    if (!error) return;
    const status = (error as { status?: number } | undefined)?.status;
    if (status === 401) {
      window.location.href = '/spa/login';
      return;
    }
    toast({ kind: 'error', title: `Error cargando ${label}` });
  }, [error, label]);
  return { data, isLoading };
}

// ─── KPI Card ─────────────────────────────────────────────────────────────────

function KpiCard({
  label,
  value,
  sub,
  loading,
}: {
  label: string;
  value: string;
  sub?: string;
  loading: boolean;
}) {
  return (
    <Card>
      <CardHeader className="pb-1 pt-4 px-4">
        <p className="text-xs text-slate-500 uppercase tracking-wide font-semibold">{label}</p>
      </CardHeader>
      <CardContent className="px-4 pb-4">
        <CardTitle className={`text-2xl font-bold ${loading ? 'text-slate-400 dark:text-slate-600' : ''}`}>
          {loading ? '—' : value}
        </CardTitle>
        {sub && (
          <p className="text-xs text-slate-500 mt-1">{loading ? '' : sub}</p>
        )}
      </CardContent>
    </Card>
  );
}

// ─── Pipeline Cards ────────────────────────────────────────────────────────────

const PIPELINE_COLS: {
  key: keyof PipelineResponse;
  label: string;
  variant: 'default' | 'cyan' | 'amber' | 'rose' | 'emerald';
}[] = [
  { key: 'nueva', label: 'Nuevas', variant: 'cyan' },
  { key: 'seguimiento', label: 'Seguimiento', variant: 'default' },
  { key: 'por_vencer', label: 'Por vencer', variant: 'amber' },
  { key: 'vencida', label: 'Vencidas', variant: 'rose' },
  { key: 'convertida', label: 'Convertidas', variant: 'emerald' },
];

// ─── Alert badge severity ──────────────────────────────────────────────────────

type Severity = 'urgente' | 'warning' | 'info';

function severityVariant(s: Severity) {
  if (s === 'urgente') return 'rose' as const;
  if (s === 'warning') return 'amber' as const;
  return 'slate' as const;
}

function severityLabel(s: Severity) {
  if (s === 'urgente') return 'Urgente';
  if (s === 'warning') return 'Aviso';
  return 'Info';
}

// ─── Main Page ─────────────────────────────────────────────────────────────────

export function DashboardPage() {
  const heroQ = useSafeQuery(useHero(), 'hero');
  const pipelineQ = useSafeQuery(usePipeline(), 'pipeline');
  const alertasQ = useSafeQuery(useAlertas(), 'alertas');
  const topsQ = useSafeQuery(useTops(), 'tops');

  const hero = heroQ.data;
  const pipeline = pipelineQ.data;
  const alertas = alertasQ.data;
  const tops = topsQ.data;

  // ── Alertas unificadas ──────────────────────────────────────────────────────
  type AlertaItem = {
    key: string;
    severity: Severity;
    text: string;
    link?: string;
  };

  const alertItems: AlertaItem[] = [];

  if (alertas) {
    alertas.por_vencer_3d.forEach((o) => {
      const dias = o.dias_restantes;
      const severity: Severity = dias !== null && dias <= 0 ? 'urgente' : dias !== null && dias <= 1 ? 'urgente' : 'warning';
      alertItems.push({
        key: `vencer-${o.id}`,
        severity,
        text: `Cotización ${o.folio} (${o.cliente}) vence en ${dias !== null ? `${dias}d` : '—'}`,
        link: `/spa/seguimiento`,
      });
    });

    alertas.stock_critico_cotizado.forEach((p) => {
      alertItems.push({
        key: `stock-${p.producto_id}`,
        severity: 'warning',
        text: `${p.nombre} (${p.sku}): stock ${p.stock_actual} ≤ mínimo ${p.stock_minimo}, ${p.cotizaciones_activas} cot. activas`,
        link: `/spa/inventario`,
      });
    });

    alertas.saldos_vencidos.forEach((c) => {
      const severity: Severity = c.dias_sin_pago > 90 ? 'urgente' : 'warning';
      alertItems.push({
        key: `saldo-${c.id}`,
        severity,
        text: `${c.empresa}: saldo ${fmtMoney(c.saldo)} sin pago hace ${c.dias_sin_pago} días`,
        link: `/spa/clientes`,
      });
    });

    alertas.oc_borrador.forEach((oc) => {
      alertItems.push({
        key: `oc-${oc.id}`,
        severity: 'info',
        text: `OC borrador ${oc.folio}${oc.proveedor ? ` (${oc.proveedor})` : ''} — ${fmtMoney(oc.total, oc.moneda)}`,
      });
    });
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <header className="flex items-center gap-2">
        <LayoutDashboard className="h-5 w-5 text-accent-glow" />
        <h1 className="text-2xl font-semibold">Dashboard</h1>
      </header>

      {/* Row 1: KPIs hero */}
      <section>
        <h2 className="text-xs text-slate-500 uppercase font-semibold tracking-wide mb-3">
          Ventas — mes actual
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <KpiCard
            label="Ventas del mes"
            value={fmtMoney(hero?.ventas.monto_mxn ?? 0)}
            sub={
              hero
                ? `${fmtInt(hero.ventas.count)} órdenes${
                    hero.ventas.delta_pct !== null
                      ? ` · ${hero.ventas.delta_pct > 0 ? '+' : ''}${fmtPct(hero.ventas.delta_pct)} vs periodo ant.`
                      : ''
                  }`
                : undefined
            }
            loading={heroQ.isLoading}
          />
          <KpiCard
            label="Pipeline abierto"
            value={fmtMoney(hero?.pipeline.monto_mxn ?? 0)}
            sub={hero ? `${fmtInt(hero.pipeline.count)} cotizaciones · ticket promedio ${fmtMoney(hero.pipeline.ticket_promedio_mxn)}` : undefined}
            loading={heroQ.isLoading}
          />
          <KpiCard
            label="Conversión 30d"
            value={fmtPct(hero?.conversion.tasa_pct ?? 0)}
            sub={hero ? `Meta: ${fmtPct(hero.conversion.target_pct)}` : undefined}
            loading={heroQ.isLoading}
          />
          <KpiCard
            label="Margen prom."
            value={fmtPct(hero?.margen.pct ?? 0)}
            sub={hero ? `${fmtInt(hero.margen.muestra_lineas)} líneas` : undefined}
            loading={heroQ.isLoading}
          />
        </div>
      </section>

      {/* Row 2: Pipeline */}
      <section>
        <h2 className="text-xs text-slate-500 uppercase font-semibold tracking-wide mb-3">
          Pipeline de cotizaciones
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {PIPELINE_COLS.map(({ key, label, variant }) => {
            const col = pipeline?.[key];
            return (
              <Card key={key}>
                <CardHeader className="pb-1 pt-4 px-4">
                  <div className="flex items-center justify-between">
                    <p className="text-xs text-slate-500 uppercase font-semibold tracking-wide">{label}</p>
                    <Badge variant={variant}>{pipelineQ.isLoading ? '—' : fmtInt(col?.count ?? 0)}</Badge>
                  </div>
                </CardHeader>
                <CardContent className="px-4 pb-4">
                  <p className="text-lg font-bold">
                    {pipelineQ.isLoading ? '—' : fmtMoney(col?.monto_total_mxn ?? 0)}
                  </p>
                  {!pipelineQ.isLoading && col && col.items.length > 0 && (
                    <ul className="mt-2 space-y-1">
                      {col.items.slice(0, 3).map((o) => (
                        <li key={o.id} className="text-xs text-slate-600 dark:text-slate-400 truncate">
                          {o.folio} · {o.cliente}
                        </li>
                      ))}
                      {col.count > 3 && (
                        <li className="text-xs text-slate-400 dark:text-slate-600">+{col.count - 3} más</li>
                      )}
                    </ul>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>

      {/* Row 3: Alertas */}
      <section>
        <h2 className="text-xs text-slate-500 uppercase font-semibold tracking-wide mb-3 flex items-center gap-1">
          <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />
          Alertas
        </h2>
        {alertasQ.isLoading ? (
          <div className="text-slate-400 dark:text-slate-600 text-sm">Cargando alertas…</div>
        ) : alertItems.length === 0 ? (
          <p className="text-sm text-slate-500">Sin alertas activas.</p>
        ) : (
          <div className="space-y-2">
            {alertItems.map((a) => (
              <div
                key={a.key}
                className="flex items-start gap-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-2"
              >
                <Badge variant={severityVariant(a.severity)} className="mt-0.5 shrink-0">
                  {severityLabel(a.severity)}
                </Badge>
                <span className="text-sm text-slate-700 dark:text-slate-300 flex-1 leading-snug">{a.text}</span>
                {a.link && (
                  <a
                    href={a.link}
                    className="text-xs text-cyan-400 hover:text-cyan-300 shrink-0 self-center"
                  >
                    ver →
                  </a>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Row 4: Tops */}
      <section>
        <h2 className="text-xs text-slate-500 uppercase font-semibold tracking-wide mb-3">
          Tops del mes
        </h2>
        <div className={`grid gap-4 ${tops?.ve_equipo ? 'md:grid-cols-3' : 'md:grid-cols-2'}`}>
          {/* Top Productos */}
          <Card>
            <CardHeader className="pb-2 pt-4 px-4">
              <CardTitle className="text-sm font-semibold flex items-center gap-1.5">
                <Package className="h-4 w-4 text-violet-400" />
                Top productos cotizados
              </CardTitle>
            </CardHeader>
            <CardContent className="px-4 pb-4">
              {topsQ.isLoading ? (
                <p className="text-slate-400 dark:text-slate-600 text-sm">Cargando…</p>
              ) : !tops?.productos.length ? (
                <p className="text-slate-500 text-sm">Sin datos</p>
              ) : (
                <ol className="space-y-2">
                  {tops.productos.map((p, i) => (
                    <li key={p.id} className="flex items-start gap-2 text-sm">
                      <span className="text-xs text-slate-400 dark:text-slate-600 w-4 pt-0.5">{i + 1}.</span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-1 flex-wrap">
                          <span className="font-medium text-slate-800 dark:text-slate-200 truncate">{p.nombre}</span>
                          {p.stock_riesgo && (
                            <Badge variant="rose">Stock bajo</Badge>
                          )}
                        </div>
                        <p className="text-xs text-slate-500 font-mono">
                          {p.sku}{p.marca ? ` · ${p.marca}` : ''}
                        </p>
                        <p className="text-xs text-slate-500">
                          {fmtInt(p.cantidad_total)} uds en {p.apariciones} cot.
                        </p>
                      </div>
                    </li>
                  ))}
                </ol>
              )}
            </CardContent>
          </Card>

          {/* Top Clientes */}
          <Card>
            <CardHeader className="pb-2 pt-4 px-4">
              <CardTitle className="text-sm font-semibold flex items-center gap-1.5">
                <TrendingUp className="h-4 w-4 text-emerald-400" />
                Top clientes del mes
              </CardTitle>
            </CardHeader>
            <CardContent className="px-4 pb-4">
              {topsQ.isLoading ? (
                <p className="text-slate-400 dark:text-slate-600 text-sm">Cargando…</p>
              ) : !tops?.clientes.length ? (
                <p className="text-slate-500 text-sm">Sin datos</p>
              ) : (
                <ol className="space-y-2">
                  {tops.clientes.map((c, i) => (
                    <li key={c.id} className="flex items-start gap-2 text-sm">
                      <span className="text-xs text-slate-400 dark:text-slate-600 w-4 pt-0.5">{i + 1}.</span>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-slate-800 dark:text-slate-200 truncate">{c.empresa}</p>
                        <p className="text-xs text-slate-500">
                          {fmtMoney(c.monto_mxn)} · {fmtInt(c.orden_count)} orden(es)
                        </p>
                        {c.saldo > 0 && (
                          <p className="text-xs text-amber-700 dark:text-amber-400">Saldo: {fmtMoney(c.saldo)}</p>
                        )}
                      </div>
                    </li>
                  ))}
                </ol>
              )}
            </CardContent>
          </Card>

          {/* Top Vendedores — solo admin/gerente */}
          {tops?.ve_equipo && (
            <Card>
              <CardHeader className="pb-2 pt-4 px-4">
                <CardTitle className="text-sm font-semibold flex items-center gap-1.5">
                  <CreditCard className="h-4 w-4 text-cyan-400" />
                  Top vendedores del mes
                </CardTitle>
              </CardHeader>
              <CardContent className="px-4 pb-4">
                {topsQ.isLoading ? (
                  <p className="text-slate-400 dark:text-slate-600 text-sm">Cargando…</p>
                ) : !tops.vendedores.length ? (
                  <p className="text-slate-500 text-sm">Sin datos</p>
                ) : (
                  <ol className="space-y-2">
                    {tops.vendedores.map((v, i) => (
                      <li key={v.id} className="flex items-start gap-2 text-sm">
                        <span className="text-xs text-slate-400 dark:text-slate-600 w-4 pt-0.5">{i + 1}.</span>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-slate-800 dark:text-slate-200">{v.nombre}</p>
                          <p className="text-xs text-slate-500">
                            {fmtMoney(v.monto_mxn)} · {fmtInt(v.orden_count)} venta(s)
                          </p>
                        </div>
                      </li>
                    ))}
                  </ol>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </section>
    </div>
  );
}

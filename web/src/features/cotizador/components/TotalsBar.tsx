import { useMemo, useState } from 'react';
import { confirm } from '@/lib/confirm';
import { Sigma, Percent, Coins, TrendingUp, AlertTriangle, Wallet } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { DocumentTotalsBar } from '@/components/document/DocumentTotalsBar';
import { toast } from '@/lib/toast';
import { useCotizador } from '../store';
import { useConfig } from '../hooks/useConfig';
import { useGuardarCotizacion } from '../hooks/useCotizacion';
import {
  computeCostos,
  computeTotals,
  computeTotalsPorMoneda,
  resolveDirectionalTcs,
} from '../lib/calc';

function fmtMoney(n: number, moneda: string) {
  return `${moneda} $${n.toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function TotalsBar() {
  const [err, setErr] = useState<string | null>(null);
  const cart = useCotizador((s) => s.cart);
  const moneda = useCotizador((s) => s.moneda);
  const tc = useCotizador((s) => s.tc);
  const tcMnAUsd = useCotizador((s) => s.tc_mn_a_usd);
  const tcUsdAMn = useCotizador((s) => s.tc_usd_a_mn);
  const toleranciaTc = useCotizador((s) => s.tolerancia_tc);
  const cliente_id = useCotizador((s) => s.cliente_id);
  const lineasNoSoportadas = useCotizador((s) => s.lineasNoSoportadas);
  const editingId = useCotizador((s) => s.editingId);
  const editingEstatus = useCotizador((s) => s.editingEstatus);
  const { config } = useConfig();
  const guardar = useGuardarCotizacion();

  const tcs = resolveDirectionalTcs(tc, tcMnAUsd, tcUsdAMn, toleranciaTc);
  const { subtotal, iva, total } = computeTotals(cart, moneda, tcs, config.iva_rate);
  // Costo y margen "real": costo con DOF puro (lo que Dasic paga al proveedor)
  // vs subtotal (lo que cobra al cliente, ya con spread del TC). El margen
  // incluye tanto la utilidad explícita por línea como el spread del TC.
  const { costo, margen, margenPct } = computeCostos(cart, moneda, tcs, subtotal);
  const breakdown = useMemo(() => computeTotalsPorMoneda(cart), [cart]);
  // Solo mostrar el desglose por moneda nativa cuando la cot tiene mix:
  // hay líneas de las DOS monedas, o cualquier línea difiere de la moneda
  // de la cotización. Si todo es de una sola moneda igual a la de la cot,
  // el desglose sería redundante con el subtotal de arriba.
  const hayMixDeMonedas = breakdown.mxn_count > 0 && breakdown.usd_count > 0;
  const hayLineasEnOtraMoneda =
    (moneda === 'MXN' && breakdown.usd_count > 0) ||
    (moneda === 'USD' && breakdown.mxn_count > 0);
  const showBreakdown = hayMixDeMonedas || hayLineasEnOtraMoneda;

  const noEditable = !!editingEstatus && editingEstatus.toUpperCase() !== 'COTIZACION';
  const tieneNoSoportadas = lineasNoSoportadas.length > 0;
  // TC necesario si la cot es USD o tiene líneas en otra moneda. Implausible si
  // sigue < 5 (USD/MXN nunca baja de ahí) → bloquea guardar para no subvaluar ×2.
  const tcNecesario = moneda === 'USD' || hayLineasEnOtraMoneda;
  const tcImplausible = tcNecesario && (!Number.isFinite(tc) || tc < 5);

  const reasons: string[] = [];
  if (cart.length === 0) reasons.push('agrega productos');
  if (cliente_id == null) reasons.push('selecciona cliente');
  if (cart.some((l) => l.qty <= 0)) reasons.push('hay líneas con cantidad 0');
  if (tcImplausible) reasons.push('captura el TC de Banxico (TC actual implausible)');
  if (tieneNoSoportadas) reasons.push('cotización contiene líneas ad-hoc no soportadas');
  if (noEditable) reasons.push(`cotización en estatus ${editingEstatus}`);
  const disabled = reasons.length > 0 || guardar.isPending;

  async function onCancel() {
    if (editingId != null) {
      window.location.href = '/seguimiento';
      return;
    }
    if (cart.length === 0 || (await confirm({ mensaje: '¿Descartar cotización?', tono: 'danger' }))) {
      useCotizador.getState().reset();
      window.location.href = '/seguimiento';
    }
  }

  const margenStats = useMemo(() => {
    const criticas = cart.filter((l) => l.utilidad < 5).length;
    const bajas = cart.filter((l) => l.utilidad < 15).length;
    const avg = cart.length
      ? cart.reduce((acc, l) => acc + (Number(l.utilidad) || 0), 0) / cart.length
      : 0;
    return { criticas, bajas, avg };
  }, [cart]);

  async function onSave() {
    setErr(null);
    const s = useCotizador.getState();

    if (margenStats.criticas > 0) {
      if (
        !(await confirm({
          mensaje: `⚠ ${margenStats.criticas} línea(s) con utilidad < 5 %. Riesgo de venta en pérdida. ¿Continuar?`,
          tono: 'warning',
        }))
      ) {
        return;
      }
    } else if (margenStats.bajas > 0) {
      if (!(await confirm({ mensaje: `${margenStats.bajas} línea(s) con utilidad < 15 %. ¿Continuar?`, tono: 'warning' }))) {
        return;
      }
    }

    const entregaParcial = cart.filter((l) => {
      const tiene = (v: unknown) => v != null && v !== '';
      const campos = [tiene(l.entrega_min), tiene(l.entrega_max), tiene(l.entrega_unidad)];
      return campos.some(Boolean) && !campos.every(Boolean);
    });
    if (entregaParcial.length > 0) {
      if (
        !(await confirm({
          mensaje: `${entregaParcial.length} línea(s) con tiempo de entrega incompleto (falta min, max o unidad). ¿Guardar de todas formas?`,
          tono: 'warning',
        }))
      ) {
        return;
      }
    }

    guardar.mutate(
      {
        cliente_id: s.cliente_id,
        contacto_id: s.contacto_id,
        moneda: s.moneda,
        tc: s.tc,
        tc_mn_a_usd: s.tc_mn_a_usd,
        tc_usd_a_mn: s.tc_usd_a_mn,
        tolerancia_tc: s.tolerancia_tc,
        fecha_creacion: s.fecha_creacion,
        fecha_vencimiento: s.fecha_vencimiento,
        observaciones: s.observaciones,
        terminos_condiciones: s.terminos_condiciones,
        pdf_concepto_unificado: s.pdf_concepto_unificado,
        pdf_concepto_enabled: s.pdf_concepto_enabled,
        cart: s.cart,
      },
      {
        onSuccess: (data) => {
          window.location.href = `/seguimiento?folio=${encodeURIComponent(data.folio)}`;
        },
        onError: (e: { status?: number; detail?: string }) => {
          if (e.status === 401) {
            window.location.href = '/spa/login';
            return;
          }
          toast({ kind: 'error', title: 'No se pudo guardar la cotización', description: e.detail });
          setErr(e.detail || 'No se pudo guardar la cotización');
        },
      },
    );
  }

  const avgClass =
    margenStats.avg < 5
      ? 'bg-rose-900/30 text-rose-300 border-rose-700/50'
      : margenStats.avg < 15
        ? 'bg-amber-900/30 text-amber-300 border-amber-700/50'
        : 'bg-emerald-900/30 text-emerald-300 border-emerald-700/50';

  return (
    <DocumentTotalsBar
      warnings={
        <>
          {err && (
            <div className="mb-2 text-[11px] bg-rose-900/30 border border-rose-700/50 text-rose-300 rounded px-2 py-1.5 flex items-center gap-1.5">
              <AlertTriangle className="h-3 w-3 shrink-0" />
              {err}
            </div>
          )}
          {reasons.length > 0 && cart.length > 0 && (
            <div className="mb-1 text-[11px] text-amber-400 flex items-center gap-1">
              <AlertTriangle className="h-3 w-3" />
              Pendiente para guardar: {reasons.join(', ')}
            </div>
          )}
          {margenStats.bajas > 0 && (
            <div className="mb-1 text-[11px] text-amber-400 flex items-center gap-1">
              <AlertTriangle className="h-3 w-3" />
              {margenStats.criticas > 0
                ? `${margenStats.criticas} línea(s) con utilidad crítica (<5 %)`
                : `${margenStats.bajas} línea(s) con utilidad baja (<15 %)`}
            </div>
          )}
          {showBreakdown && (
            <div
              className="mb-1 flex items-center gap-1.5 flex-wrap"
              title="Subtotales antes de IVA, en la moneda nativa de cada línea (sin conversión por TC)"
            >
              <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
                Por moneda nativa
              </span>
              {breakdown.usd_count > 0 && (
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded border bg-cyan-900/30 text-cyan-300 border-cyan-700/50">
                  USD {breakdown.usd_count} línea{breakdown.usd_count === 1 ? '' : 's'} · $
                  {breakdown.usd.toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
              )}
              {breakdown.mxn_count > 0 && (
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded border bg-emerald-900/30 text-emerald-300 border-emerald-700/50">
                  MXN {breakdown.mxn_count} línea{breakdown.mxn_count === 1 ? '' : 's'} · $
                  {breakdown.mxn.toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
              )}
            </div>
          )}
        </>
      }
      stats={[
        { label: <><Sigma className="h-3 w-3" /> Subtotal</>, value: fmtMoney(subtotal, moneda), emphasis: 'big' },
        { label: <><Wallet className="h-3 w-3" /> Costo</>, value: fmtMoney(costo, moneda) },
        {
          label: <><TrendingUp className="h-3 w-3 text-emerald-400" /> Margen</>,
          value: `${fmtMoney(margen, moneda)} (${margenPct.toFixed(1)}%)`,
          valueClass: `font-mono text-sm font-semibold ${margen < 0 ? 'text-rose-400' : margenPct < 15 ? 'text-amber-300' : 'text-emerald-300'}`,
        },
        { label: <><Percent className="h-3 w-3" /> IVA ({config.iva_pct_label})</>, value: fmtMoney(iva, moneda) },
        { label: <><Coins className="h-3 w-3 text-accent-glow" /> Total</>, value: fmtMoney(total, moneda), emphasis: 'accent' },
      ]}
      trailing={
        cart.length > 0 ? (
          <span className={`self-center text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border flex items-center gap-1 ${avgClass}`}>
            <TrendingUp className="h-2.5 w-2.5" /> Util prom. {margenStats.avg.toFixed(1)}%
          </span>
        ) : null
      }
      actions={
        <>
          <Button variant="ghost" onClick={onCancel} disabled={guardar.isPending}>Cancelar</Button>
          <Button onClick={onSave} disabled={disabled} data-cot-save>
            {guardar.isPending ? 'Guardando…' : editingId != null ? 'Actualizar cotización' : 'Guardar cotización'}
          </Button>
        </>
      }
    />
  );
}

import { useMemo, useState } from 'react';
import { Sigma, Percent, Coins, TrendingUp, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useCotizador } from '../store';
import { useConfig } from '../hooks/useConfig';
import { useGuardarCotizacion } from '../hooks/useCotizacion';
import { computeTotals, resolveDirectionalTcs } from '../lib/calc';

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
  const cliente_id = useCotizador((s) => s.cliente_id);
  const lineasNoSoportadas = useCotizador((s) => s.lineasNoSoportadas);
  const editingId = useCotizador((s) => s.editingId);
  const editingEstatus = useCotizador((s) => s.editingEstatus);
  const { config } = useConfig();
  const guardar = useGuardarCotizacion();

  const tcs = resolveDirectionalTcs(tc, tcMnAUsd, tcUsdAMn);
  const { subtotal, iva, total } = computeTotals(cart, moneda, tcs, config.iva_rate);

  const noEditable = !!editingEstatus && editingEstatus.toUpperCase() !== 'COTIZACION';
  const tieneNoSoportadas = lineasNoSoportadas.length > 0;
  const tcInvalido = moneda === 'USD' && tc <= 0;

  const reasons: string[] = [];
  if (cart.length === 0) reasons.push('agrega productos');
  if (cliente_id == null) reasons.push('selecciona cliente');
  if (tcInvalido) reasons.push('captura TC');
  if (tieneNoSoportadas) reasons.push('cotización contiene líneas ad-hoc no soportadas');
  if (noEditable) reasons.push(`cotización en estatus ${editingEstatus}`);
  const disabled = reasons.length > 0 || guardar.isPending;

  function onCancel() {
    if (editingId != null) {
      window.location.href = '/seguimiento';
      return;
    }
    if (cart.length === 0 || window.confirm('¿Descartar cotización?')) {
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

  function onSave() {
    setErr(null);
    const s = useCotizador.getState();

    if (margenStats.criticas > 0) {
      if (
        !window.confirm(
          `⚠ ${margenStats.criticas} línea(s) con utilidad < 5 %. Riesgo de venta en pérdida. ¿Continuar?`,
        )
      ) {
        return;
      }
    } else if (margenStats.bajas > 0) {
      if (!window.confirm(`${margenStats.bajas} línea(s) con utilidad < 15 %. ¿Continuar?`)) {
        return;
      }
    }

    guardar.mutate(
      {
        cliente_id: s.cliente_id,
        moneda: s.moneda,
        tc: s.tc,
        tc_mn_a_usd: s.tc_mn_a_usd,
        tc_usd_a_mn: s.tc_usd_a_mn,
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
    <div className="sticky bottom-0 bg-slate-900 border-t border-slate-800 px-4 py-2">
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
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-4 text-xs flex-wrap">
          <div className="flex items-center gap-1.5">
            <Sigma className="h-3.5 w-3.5 text-slate-500" />
            <span className="text-slate-500">Subtotal</span>
            <span className="font-mono">{fmtMoney(subtotal, moneda)}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Percent className="h-3.5 w-3.5 text-slate-500" />
            <span className="text-slate-500">IVA ({config.iva_pct_label})</span>
            <span className="font-mono">{fmtMoney(iva, moneda)}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Coins className="h-3.5 w-3.5 text-accent-glow" />
            <span className="text-slate-500">Total</span>
            <span className="font-mono font-bold text-accent-glow">{fmtMoney(total, moneda)}</span>
          </div>
          {cart.length > 0 && (
            <span
              className={`text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border flex items-center gap-1 ${avgClass}`}
              title="Utilidad promedio del carrito"
            >
              <TrendingUp className="h-2.5 w-2.5" />
              Util prom. {margenStats.avg.toFixed(1)}%
            </span>
          )}
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" onClick={onCancel} disabled={guardar.isPending}>
            Cancelar
          </Button>
          <Button onClick={onSave} disabled={disabled} data-cot-save>
            {guardar.isPending ? 'Guardando…' : editingId != null ? 'Actualizar cotización' : 'Guardar cotización'}
          </Button>
        </div>
      </div>
    </div>
  );
}

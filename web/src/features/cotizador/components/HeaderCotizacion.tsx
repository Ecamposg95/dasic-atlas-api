import { useEffect } from 'react';
import { User, Coins, ArrowRightLeft, CalendarPlus, CalendarClock, ShieldAlert, Minus, Plus, RotateCcw } from 'lucide-react';
import { ClientPicker } from './ClientPicker';
import { Input } from '@/components/ui/input';
import { useCotizador } from '../store';
import { useConfig } from '../hooks/useConfig';
import { useAuth } from '@/stores/auth';
import { FXBadge } from './FXBadge';
import { UltimaCotHint } from './UltimaCotHint';
import { resolveDirectionalTcs } from '../lib/calc';

export function HeaderCotizacion() {
  const moneda = useCotizador((s) => s.moneda);
  const setMoneda = useCotizador((s) => s.setMoneda);
  const tc = useCotizador((s) => s.tc);
  const setTc = useCotizador((s) => s.setTc);
  const tcMnAUsd = useCotizador((s) => s.tc_mn_a_usd);
  const tcUsdAMn = useCotizador((s) => s.tc_usd_a_mn);
  const setTcMnAUsd = useCotizador((s) => s.setTcMnAUsd);
  const setTcUsdAMn = useCotizador((s) => s.setTcUsdAMn);
  const fechaCreacion = useCotizador((s) => s.fecha_creacion);
  const setFechaCreacion = useCotizador((s) => s.setFechaCreacion);
  const fechaVencimiento = useCotizador((s) => s.fecha_vencimiento);
  const setFechaVencimiento = useCotizador((s) => s.setFechaVencimiento);
  const editingId = useCotizador((s) => s.editingId);
  const clienteId = useCotizador((s) => s.cliente_id);
  const { config } = useConfig();
  const user = useAuth((s) => s.user);
  // Patrones existentes en `web/src/features/{clientes,reportes,cxc,fx,precios,inventario}/`
  // usan `user?.rol === 'ADMINISTRADOR' || user?.rol === 'ADMIN'`. Replicamos.
  const esAdmin = user?.rol === 'ADMINISTRADOR' || user?.rol === 'ADMIN';

  // Defaults para cotización nueva: hoy + vigencia (config.quote_validity_days).
  useEffect(() => {
    if (editingId != null) return; // modo edit: respeta lo que vino del backend
    if (fechaCreacion == null) {
      const hoy = new Date().toISOString().slice(0, 10);
      setFechaCreacion(hoy);
    }
    if (fechaVencimiento == null) {
      const d = new Date();
      d.setDate(d.getDate() + (config.quote_validity_days || 15));
      setFechaVencimiento(d.toISOString().slice(0, 10));
    }
  }, [editingId, fechaCreacion, fechaVencimiento, config.quote_validity_days, setFechaCreacion, setFechaVencimiento]);

  const tcVisible = moneda === 'USD';
  const tcs = resolveDirectionalTcs(tc, tcMnAUsd, tcUsdAMn);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 grid grid-cols-1 md:grid-cols-3 gap-3">
      <div className="md:col-span-2">
        <label className="text-[10px] uppercase tracking-[0.15em] font-bold text-slate-400 mb-1 flex items-center gap-1.5">
          <User className="h-3 w-3" />
          Cliente
        </label>
        <ClientPicker />
        <UltimaCotHint clienteId={clienteId} />
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="text-[10px] uppercase tracking-[0.15em] font-bold text-slate-400 mb-1 flex items-center gap-1.5">
            <Coins className="h-3 w-3" />
            Moneda
          </label>
          <select
            value={moneda}
            onChange={(e) => setMoneda(e.target.value as 'MXN' | 'USD')}
            className="w-full h-8 rounded-md border border-slate-700 bg-slate-900 px-2 text-xs focus:border-accent-glow focus:ring-2 focus:ring-accent-glow/40 outline-none"
          >
            <option value="MXN">MXN</option>
            <option value="USD">USD</option>
          </select>
        </div>
        <div>
          <label className="text-[10px] uppercase tracking-[0.15em] font-bold text-slate-400 mb-1 flex items-center gap-1.5">
            <ArrowRightLeft className="h-3 w-3" />
            DOF (TC oficial)
          </label>
          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => setTc(Math.max(0, +(tc - 1).toFixed(4)))}
              title="-1 peso"
              aria-label="Restar 1 peso al DOF"
              className="h-8 w-7 inline-flex items-center justify-center rounded border border-slate-700 bg-slate-800/50 text-slate-300 hover:bg-slate-700 hover:border-accent-glow transition text-sm font-bold shrink-0"
            >
              <Minus className="h-3.5 w-3.5" />
            </button>
            <Input
              type="number"
              step="0.0001"
              min="0"
              value={tc}
              onChange={(e) => setTc(parseFloat(e.target.value) || 0)}
              className="h-8 text-xs text-right font-mono"
              title="DOF (TC oficial Banxico)"
            />
            <button
              type="button"
              onClick={() => setTc(+(tc + 1).toFixed(4))}
              title="+1 peso"
              aria-label="Sumar 1 peso al DOF"
              className="h-8 w-7 inline-flex items-center justify-center rounded border border-slate-700 bg-slate-800/50 text-slate-300 hover:bg-slate-700 hover:border-accent-glow transition text-sm font-bold shrink-0"
            >
              <Plus className="h-3.5 w-3.5" />
            </button>
          </div>
          {tcVisible && (
            <div className="mt-1 space-y-0.5">
              <FXBadge />
              {esAdmin && (
                <button
                  type="button"
                  onClick={() =>
                    window.dispatchEvent(new CustomEvent('cot:open-pisartc'))
                  }
                  className="text-[10px] text-amber-400 hover:underline flex items-center gap-1"
                >
                  <ShieldAlert className="h-2.5 w-2.5" /> Pisar TC manualmente
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* TCs direccionales (modelo Excel V_03): default DOF±1. Editable
          individualmente para overrides puntuales. Reset (↺) vuelve al
          auto-derive desde DOF. */}
      <div className="md:col-span-3 grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 border-t border-slate-800/60">
        <div>
          <label className="text-[10px] uppercase tracking-[0.15em] font-bold text-slate-500 mb-1 flex items-center gap-1.5">
            <ArrowRightLeft className="h-3 w-3" />
            MN → USD
            <span className="text-slate-600 normal-case tracking-normal font-normal">(default DOF − 1)</span>
            {tcMnAUsd != null && (
              <button
                type="button"
                onClick={() => setTcMnAUsd(null)}
                title="Volver al default (DOF − 1)"
                className="ml-auto text-slate-500 hover:text-accent-glow flex items-center gap-0.5"
              >
                <RotateCcw className="h-2.5 w-2.5" />
                <span className="text-[10px]">reset</span>
              </button>
            )}
          </label>
          <Input
            type="number"
            step="0.0001"
            min="0"
            value={tcs.tc_mn_a_usd}
            onChange={(e) => {
              const v = parseFloat(e.target.value);
              setTcMnAUsd(Number.isFinite(v) && v > 0 ? v : null);
            }}
            className={`h-8 text-xs text-right font-mono ${tcMnAUsd == null ? 'text-slate-500' : ''}`}
            title={tcMnAUsd == null ? 'Auto: DOF − 1' : 'Sobreescrito manualmente'}
          />
        </div>
        <div>
          <label className="text-[10px] uppercase tracking-[0.15em] font-bold text-slate-500 mb-1 flex items-center gap-1.5">
            <ArrowRightLeft className="h-3 w-3" />
            USD → MN
            <span className="text-slate-600 normal-case tracking-normal font-normal">(default DOF + 1)</span>
            {tcUsdAMn != null && (
              <button
                type="button"
                onClick={() => setTcUsdAMn(null)}
                title="Volver al default (DOF + 1)"
                className="ml-auto text-slate-500 hover:text-accent-glow flex items-center gap-0.5"
              >
                <RotateCcw className="h-2.5 w-2.5" />
                <span className="text-[10px]">reset</span>
              </button>
            )}
          </label>
          <Input
            type="number"
            step="0.0001"
            min="0"
            value={tcs.tc_usd_a_mn}
            onChange={(e) => {
              const v = parseFloat(e.target.value);
              setTcUsdAMn(Number.isFinite(v) && v > 0 ? v : null);
            }}
            className={`h-8 text-xs text-right font-mono ${tcUsdAMn == null ? 'text-slate-500' : ''}`}
            title={tcUsdAMn == null ? 'Auto: DOF + 1' : 'Sobreescrito manualmente'}
          />
        </div>
      </div>

      <div>
        <label className="text-[10px] uppercase tracking-[0.15em] font-bold text-slate-400 mb-1 flex items-center gap-1.5">
          <CalendarPlus className="h-3 w-3" />
          F. creación
        </label>
        <Input
          type="date"
          value={fechaCreacion ?? ''}
          onChange={(e) => setFechaCreacion(e.target.value || null)}
          className="h-8 text-xs"
        />
      </div>

      <div>
        <label className="text-[10px] uppercase tracking-[0.15em] font-bold text-slate-400 mb-1 flex items-center gap-1.5">
          <CalendarClock className="h-3 w-3" />
          F. vencimiento
        </label>
        <Input
          type="date"
          value={fechaVencimiento ?? ''}
          onChange={(e) => setFechaVencimiento(e.target.value || null)}
          className="h-8 text-xs"
        />
      </div>

      <div className="text-[11px] text-slate-500 flex items-end">
        Vigencia default: {config.quote_validity_days} días
      </div>
    </div>
  );
}

import { useEffect } from 'react';
import { User, Coins, ArrowRightLeft, CalendarPlus, CalendarClock } from 'lucide-react';
import { ClientPicker } from './ClientPicker';
import { Input } from '@/components/ui/input';
import { useCotizador } from '../store';
import { useConfig } from '../hooks/useConfig';
import { TCMiniTable } from './TCMiniTable';
import { UltimaCotHint } from './UltimaCotHint';

export function HeaderCotizacion() {
  const moneda = useCotizador((s) => s.moneda);
  const setMoneda = useCotizador((s) => s.setMoneda);
  const tc = useCotizador((s) => s.tc);
  const setTc = useCotizador((s) => s.setTc);
  const cart = useCotizador((s) => s.cart);
  const fechaCreacion = useCotizador((s) => s.fecha_creacion);
  const setFechaCreacion = useCotizador((s) => s.setFechaCreacion);
  const fechaVencimiento = useCotizador((s) => s.fecha_vencimiento);
  const setFechaVencimiento = useCotizador((s) => s.setFechaVencimiento);
  const editingId = useCotizador((s) => s.editingId);
  const clienteId = useCotizador((s) => s.cliente_id);
  const { config } = useConfig();

  // Defaults para cotización nueva: hoy + vigencia (config.quote_validity_days).
  useEffect(() => {
    if (editingId != null) return;
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

  // Regla Jinja `actualizarVisibilidadTC`: el TC se atenúa visualmente
  // cuando NO se necesita (cot MXN sin líneas USD) pero NUNCA se bloquea
  // — una cot MXN puede tener productos USD en cualquier momento y va a
  // requerir el TC. El spread direccional (DOF±1 del modelo Excel V_03)
  // se aplica automáticamente en el backend; el usuario solo ve este TC.
  const hayLineasOtraMoneda = cart.some((i) => i.productCurrency && i.productCurrency !== moneda);
  const tcNecesario = moneda === 'USD' || hayLineasOtraMoneda;

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
        <div className={tcNecesario ? '' : 'opacity-60'}>
          <label className="text-[10px] uppercase tracking-[0.15em] font-bold text-slate-400 mb-1 flex items-center gap-1.5">
            <ArrowRightLeft className="h-3 w-3" />
            TC
            {!tcNecesario && (
              <span className="text-slate-600 normal-case tracking-normal font-normal text-[10px]">
                (no requerido)
              </span>
            )}
          </label>
          <Input
            type="number"
            step="0.01"
            min="0"
            value={tc}
            onChange={(e) => setTc(parseFloat(e.target.value) || 0)}
            className="h-8 text-xs text-right font-mono"
            title="Tipo de cambio MXN/USD. Se respeta siempre, regardless de la moneda de la cotización — una cot MXN puede tener productos USD."
          />
          <TCMiniTable />
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

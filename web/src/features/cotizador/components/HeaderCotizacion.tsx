import { useEffect } from 'react';
import { User, Coins, ArrowRightLeft, CalendarPlus, CalendarClock, ShieldAlert } from 'lucide-react';
import { ClientPicker } from './ClientPicker';
import { Input } from '@/components/ui/input';
import { useCotizador } from '../store';
import { useConfig } from '../hooks/useConfig';
import { useAuth } from '@/stores/auth';
import { FXBadge } from './FXBadge';
import { UltimaCotHint } from './UltimaCotHint';

export function HeaderCotizacion() {
  const moneda = useCotizador((s) => s.moneda);
  const setMoneda = useCotizador((s) => s.setMoneda);
  const tc = useCotizador((s) => s.tc);
  const setTc = useCotizador((s) => s.setTc);
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
            TC (MXN/USD)
          </label>
          <Input
            type="number"
            step="0.0001"
            min="0"
            value={tc}
            onChange={(e) => setTc(parseFloat(e.target.value) || 0)}
            disabled={!tcVisible}
            className={`h-8 text-xs ${tcVisible ? '' : 'opacity-50'}`}
          />
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

import { useEffect } from 'react';
import { ClientPicker } from './ClientPicker';
import { Input } from '@/components/ui/input';
import { useCotizador } from '../store';
import { useConfig } from '../hooks/useConfig';

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
  const { config } = useConfig();

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
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 grid grid-cols-1 md:grid-cols-3 gap-4">
      <div className="md:col-span-2">
        <label className="block text-[10px] uppercase tracking-wider font-bold text-slate-400 mb-1">
          Cliente
        </label>
        <ClientPicker />
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="block text-[10px] uppercase tracking-wider font-bold text-slate-400 mb-1">
            Moneda
          </label>
          <select
            value={moneda}
            onChange={(e) => setMoneda(e.target.value as 'MXN' | 'USD')}
            className="w-full h-10 rounded-md border border-slate-700 bg-slate-900 px-3 text-sm focus:border-accent-glow focus:ring-2 focus:ring-accent-glow/40 outline-none"
          >
            <option value="MXN">MXN</option>
            <option value="USD">USD</option>
          </select>
        </div>
        <div>
          <label className="block text-[10px] uppercase tracking-wider font-bold text-slate-400 mb-1">
            TC (MXN/USD)
          </label>
          <Input
            type="number"
            step="0.0001"
            min="0"
            value={tc}
            onChange={(e) => setTc(parseFloat(e.target.value) || 0)}
            disabled={!tcVisible}
            className={tcVisible ? '' : 'opacity-50'}
          />
        </div>
      </div>

      <div>
        <label className="block text-[10px] uppercase tracking-wider font-bold text-slate-400 mb-1">
          F. creación
        </label>
        <Input
          type="date"
          value={fechaCreacion ?? ''}
          onChange={(e) => setFechaCreacion(e.target.value || null)}
        />
      </div>

      <div>
        <label className="block text-[10px] uppercase tracking-wider font-bold text-slate-400 mb-1">
          F. vencimiento
        </label>
        <Input
          type="date"
          value={fechaVencimiento ?? ''}
          onChange={(e) => setFechaVencimiento(e.target.value || null)}
        />
      </div>

      <div className="text-xs text-slate-500 flex items-end">
        Vigencia default: {config.quote_validity_days} días
      </div>
    </div>
  );
}

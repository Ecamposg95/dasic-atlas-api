import { Edit3, History } from 'lucide-react';

export type CotizadorTab = 'editor' | 'historial';

export function TabsCotizador({
  active,
  onChange,
  countHistorial,
}: {
  active: CotizadorTab;
  onChange: (t: CotizadorTab) => void;
  countHistorial?: number;
}) {
  return (
    <div className="flex items-center gap-1 border-b border-slate-800 -mt-2 mb-4">
      <button
        type="button"
        onClick={() => onChange('editor')}
        className={`flex items-center gap-2 px-4 py-2 text-sm font-medium transition border-b-2 ${
          active === 'editor'
            ? 'text-accent-glow border-accent-glow'
            : 'text-slate-400 border-transparent hover:text-slate-200'
        }`}
      >
        <Edit3 className="h-4 w-4" /> Cotizador
      </button>
      <button
        type="button"
        onClick={() => onChange('historial')}
        className={`flex items-center gap-2 px-4 py-2 text-sm font-medium transition border-b-2 ${
          active === 'historial'
            ? 'text-accent-glow border-accent-glow'
            : 'text-slate-400 border-transparent hover:text-slate-200'
        }`}
      >
        <History className="h-4 w-4" /> Historial
        {countHistorial != null && countHistorial > 0 && (
          <span className="text-[10px] bg-slate-700 text-slate-200 rounded-full px-2 py-0.5">
            {countHistorial}
          </span>
        )}
      </button>
    </div>
  );
}

import { useEffect, useState } from 'react';
import { X, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useCotizador } from '../store';

export function ModalPisarTC() {
  const [open, setOpen] = useState(false);
  const setTc = useCotizador((s) => s.setTc);
  const [draft, setDraft] = useState('');
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    function onOpen() {
      setDraft(String(useCotizador.getState().tc));
      setErr(null);
      setOpen(true);
    }
    window.addEventListener('cot:open-pisartc', onOpen);
    return () => window.removeEventListener('cot:open-pisartc', onOpen);
  }, []);

  function onApply() {
    const n = parseFloat(draft);
    if (!Number.isFinite(n) || n <= 0) {
      setErr('Captura un TC válido > 0');
      return;
    }
    setTc(n);
    setOpen(false);
  }

  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-50 bg-slate-950/80 flex items-center justify-center p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) setOpen(false);
      }}
    >
      <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-2xl max-w-sm w-full p-5">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-400" /> Pisar TC manualmente
          </h3>
          <button
            type="button"
            onClick={() => setOpen(false)}
            className="text-slate-400 hover:text-slate-100"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <p className="text-xs text-amber-300 mb-3 bg-amber-900/10 border border-amber-700/30 rounded p-2">
          Sobreescribe el TC sólo para esta cotización. No afecta el TC oficial del día —
          solo el campo <code>tipo_cambio</code> que se guardará en este folio.
        </p>
        <label className="block text-xs text-slate-400 mb-1">Nuevo TC (MXN/USD)</label>
        <Input
          type="number"
          step="0.0001"
          min="0.0001"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          autoFocus
        />
        {err && (
          <div className="text-xs bg-rose-900/30 border border-rose-700/50 rounded p-2 mt-2 text-rose-300">
            {err}
          </div>
        )}
        <div className="flex justify-end gap-2 pt-3 mt-3 border-t border-slate-800">
          <Button variant="ghost" size="sm" onClick={() => setOpen(false)}>
            Cancelar
          </Button>
          <Button size="sm" onClick={onApply}>
            Aplicar
          </Button>
        </div>
      </div>
    </div>
  );
}

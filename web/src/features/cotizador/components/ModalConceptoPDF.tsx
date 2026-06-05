import { useEffect, useState } from 'react';
import { X, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useCotizador } from '../store';

export function ModalConceptoPDF() {
  const [open, setOpen] = useState(false);
  const setConcepto = useCotizador((s) => s.setPdfConcepto);
  const [draft, setDraft] = useState('');

  useEffect(() => {
    function onOpen() {
      setDraft(useCotizador.getState().pdf_concepto_unificado);
      setOpen(true);
    }
    window.addEventListener('cot:open-concepto', onOpen);
    return () => window.removeEventListener('cot:open-concepto', onOpen);
  }, []);

  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-50 bg-slate-100 dark:bg-slate-950/80 flex items-center justify-center p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) setOpen(false);
      }}
    >
      <div className="bg-card border border-border rounded-xl shadow-2xl max-w-lg w-full p-5">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <FileText className="h-4 w-4 text-accent-glow" /> Concepto unificado para PDF
          </h3>
          <button
            type="button"
            onClick={() => setOpen(false)}
            className="text-muted-foreground hover:text-slate-900 dark:hover:text-slate-100"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <p className="text-xs text-muted-foreground mb-3">
          Cuando esté activado, el PDF muestra UNA línea con este concepto en lugar del
          detalle por línea. Útil para cotizaciones a clientes que solo necesitan un total
          con descripción ejecutiva.
        </p>
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          rows={6}
          placeholder='Ej. "Suministro de tablero de control eléctrico según especificación adjunta."'
          className="w-full text-sm rounded border border-border-strong bg-card px-3 py-2 focus:border-accent-glow outline-none resize-none"
        />
        <div className="flex justify-end gap-2 pt-3 mt-3 border-t border-border">
          <Button variant="ghost" size="sm" onClick={() => setOpen(false)}>
            Cancelar
          </Button>
          <Button
            size="sm"
            onClick={() => {
              setConcepto(draft);
              setOpen(false);
            }}
          >
            Guardar
          </Button>
        </div>
      </div>
    </div>
  );
}

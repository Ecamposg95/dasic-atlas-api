import { useEffect, useState } from 'react';
import { X, ClipboardList, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useBorradores } from '../hooks/useBorradores';

function fmtMoney(n: number, m: string) {
  return `${m} $${Number(n || 0).toLocaleString('es-MX', { minimumFractionDigits: 2 })}`;
}
function fmtDate(s: string | null) {
  if (!s) return '—';
  try {
    return new Date(s).toLocaleDateString('es-MX', { day: '2-digit', month: 'short' });
  } catch {
    return s;
  }
}

export function DrawerBorradores() {
  const [open, setOpen] = useState(false);
  const [page, setPage] = useState(1);
  const { data, isLoading } = useBorradores(page);

  useEffect(() => {
    function onOpen() {
      setOpen(true);
      setPage(1);
    }
    window.addEventListener('cot:open-borradores', onOpen);
    return () => window.removeEventListener('cot:open-borradores', onOpen);
  }, []);

  if (!open) return null;

  const items = data?.items ?? [];
  // El backend no devuelve un `total` global — derivamos "hay más" del tamaño
  // de la página actual.
  const hayMas = items.length === (data?.page_size ?? 10);

  return (
    <>
      <div
        className="fixed inset-0 z-40 bg-slate-100 dark:bg-slate-950/60"
        onClick={() => setOpen(false)}
      />
      <aside className="fixed right-0 top-0 bottom-0 z-50 w-full max-w-md bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col">
        <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-800">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <ClipboardList className="h-4 w-4 text-accent-glow" /> Borradores apilados
          </h3>
          <button
            type="button"
            onClick={() => setOpen(false)}
            className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {isLoading && (
            <div className="text-xs text-slate-500 dark:text-slate-400 text-center p-4">Cargando…</div>
          )}
          {!isLoading && items.length === 0 && (
            <div className="text-xs text-slate-500 dark:text-slate-400 text-center p-4">
              No tienes borradores en curso
            </div>
          )}
          {items.map((b) => (
            <a
              key={b.id}
              href={`/ventas/cotizador?edit=${b.id}`}
              className="block p-3 rounded border border-slate-200 dark:border-slate-800 hover:border-accent-glow bg-slate-100 dark:bg-slate-950 transition"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-mono text-xs font-bold text-cyan-400">{b.folio}</span>
                <span className="text-[10px] text-slate-500 dark:text-slate-400">
                  {fmtDate(b.actualizado_en)}
                </span>
              </div>
              <div className="text-sm text-slate-700 dark:text-slate-300 truncate">
                {b.cliente_nombre ?? 'Sin cliente'}
              </div>
              <div className="flex items-center justify-between mt-1">
                <span className="font-mono text-xs font-bold text-accent-glow">
                  {fmtMoney(b.total, b.moneda)}
                </span>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-slate-500 dark:text-slate-400">
                    {b.lineas_count} línea(s)
                  </span>
                  <ExternalLink className="h-3 w-3 text-slate-500 dark:text-slate-400" />
                </div>
              </div>
            </a>
          ))}
        </div>

        <div className="p-4 border-t border-slate-200 dark:border-slate-800 flex justify-between items-center">
          <Button
            size="sm"
            variant="ghost"
            disabled={page === 1}
            onClick={() => setPage((p) => p - 1)}
          >
            ← Anterior
          </Button>
          <span className="text-[10px] text-slate-500 dark:text-slate-400">Página {page}</span>
          <Button
            size="sm"
            variant="ghost"
            disabled={!hayMas}
            onClick={() => setPage((p) => p + 1)}
          >
            Siguiente →
          </Button>
        </div>
      </aside>
    </>
  );
}

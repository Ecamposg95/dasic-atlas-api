import { useEffect, useState } from 'react';
import { Keyboard, X } from 'lucide-react';
import type { AtajoHandler } from '../hooks/useAtajos';

export function AtajosPopover({ atajos }: { atajos: AtajoHandler[] }) {
  const [open, setOpen] = useState(false);

  // Escuchar un evento `cot:open-atajos` para abrir el popover desde teclado.
  // (El atajo `?` despacha este evento; antes hacía .click() sobre el botón,
  // pero con `data-cot-atajos` no era estable.)
  useEffect(() => {
    function onOpen() { setOpen(true); }
    window.addEventListener('cot:open-atajos', onOpen);
    return () => window.removeEventListener('cot:open-atajos', onOpen);
  }, []);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="fixed bottom-20 right-4 z-30 h-10 w-10 rounded-full bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 hover:border-accent-glow text-slate-700 dark:text-slate-300 hover:text-accent-glow shadow-lg flex items-center justify-center"
        title="Atajos de teclado (?)"
      >
        <Keyboard className="h-4 w-4" />
      </button>
      {open && (
        <div className="fixed inset-0 z-50 bg-slate-100 dark:bg-slate-950/80 flex items-center justify-center p-4"
          onClick={(e) => { if (e.target === e.currentTarget) setOpen(false); }}>
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-2xl max-w-md w-full p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Keyboard className="h-4 w-4 text-accent-glow" /> Atajos de teclado
              </h3>
              <button type="button" onClick={() => setOpen(false)} className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100">
                <X className="h-4 w-4" />
              </button>
            </div>
            <ul className="space-y-2">
              {atajos.map((a) => (
                <li key={a.combo} className="flex items-center justify-between text-sm">
                  <span className="text-slate-700 dark:text-slate-300">{a.description}</span>
                  <kbd className="px-2 py-1 text-[10px] font-mono bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded text-slate-800 dark:text-slate-200">
                    {a.combo}
                  </kbd>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </>
  );
}

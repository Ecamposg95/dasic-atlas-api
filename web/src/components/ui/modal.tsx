import { useEffect } from 'react';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';

// Modal shell reutilizable. Cierra en Esc + click fuera.
// Usar como envoltorio; el consumidor pone su propio contenido.

export function Modal({
  title, onClose, children, size = 'md',
}: {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}) {
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [onClose]);

  const sizeCls = {
    sm: 'max-w-sm',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
  }[size];

  return (
    <div
      className="fixed inset-0 z-50 bg-slate-950/80 flex items-center justify-center p-4"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className={cn('bg-white border border-slate-200 text-slate-900 rounded-xl shadow-2xl w-full p-5 max-h-[85vh] sm:max-h-[90vh] overflow-y-auto dark:bg-slate-900 dark:border-slate-800 dark:text-slate-100', sizeCls)}>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold">{title}</h3>
          <button type="button" onClick={onClose} className="text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100">
            <X className="h-4 w-4" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

export function ModalFooter({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex justify-end gap-2 pt-3 mt-3 border-t border-slate-200 dark:border-slate-800">
      {children}
    </div>
  );
}

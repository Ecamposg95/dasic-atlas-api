import { useEffect, useRef, useState } from 'react';
import { Input } from '@/components/ui/input';

// El endpoint clave-unidad devuelve `nombre`; clave-prod-serv devuelve
// `descripcion`. Leemos ambos para la etiqueta.
type SatItem = { codigo: string; descripcion?: string | null; nombre?: string | null };

export function SatCombobox({
  value,
  onChange,
  endpoint,
  minChars = 2,
  placeholder,
  maxLength,
  className,
}: {
  value: string;
  onChange: (code: string) => void;
  endpoint: string;
  minChars?: number;
  placeholder?: string;
  maxLength?: number;
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<SatItem[]>([]);
  const [loading, setLoading] = useState(false);
  const boxRef = useRef<HTMLDivElement | null>(null);

  // Búsqueda debounced mientras el panel está abierto y hay >= minChars.
  useEffect(() => {
    const q = value.trim();
    if (!open || q.length < minChars) {
      setItems([]);
      return;
    }
    let cancel = false;
    setLoading(true);
    const t = setTimeout(async () => {
      try {
        const r = await fetch(`${endpoint}?q=${encodeURIComponent(q)}&limit=20`, {
          credentials: 'include',
        });
        if (!r.ok) {
          if (!cancel) setItems([]);
          return;
        }
        const data = (await r.json()) as SatItem[];
        if (!cancel) setItems(Array.isArray(data) ? data : []);
      } catch {
        if (!cancel) setItems([]);
      } finally {
        if (!cancel) setLoading(false);
      }
    }, 250);
    return () => {
      cancel = true;
      clearTimeout(t);
    };
  }, [value, open, endpoint, minChars]);

  // Cerrar al click fuera.
  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener('mousedown', onDocClick);
    return () => document.removeEventListener('mousedown', onDocClick);
  }, []);

  function label(it: SatItem) {
    return it.descripcion ?? it.nombre ?? '';
  }

  return (
    <div className="relative" ref={boxRef}>
      <Input
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        placeholder={placeholder}
        maxLength={maxLength}
        className={className}
      />
      {open && value.trim().length >= minChars && (items.length > 0 || loading) && (
        <div className="absolute left-0 right-0 mt-1 max-h-56 overflow-y-auto bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-md shadow-xl z-30">
          {loading && items.length === 0 ? (
            <div className="px-2 py-2 text-xs text-slate-500">Buscando…</div>
          ) : (
            items.map((it) => (
              <button
                key={it.codigo}
                type="button"
                onClick={() => {
                  onChange(it.codigo);
                  setOpen(false);
                }}
                className="w-full text-left px-2 py-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 border-b border-slate-100 dark:border-slate-800 last:border-b-0 flex items-baseline gap-2"
              >
                <span className="font-mono text-xs text-accent-glow">{it.codigo}</span>
                <span className="text-xs text-slate-600 dark:text-slate-300 truncate">{label(it)}</span>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}

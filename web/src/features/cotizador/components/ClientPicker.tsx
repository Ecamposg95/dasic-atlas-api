import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { api } from '@/lib/api';
import { useClientes } from '../hooks/useClientes';
import { useCotizador } from '../store';
import type { ContactoLite } from '../types';

export function ClientPicker() {
  const { data: clientes, isLoading, error } = useClientes();
  const cliente_id = useCotizador((s) => s.cliente_id);
  const setCliente = useCotizador((s) => s.setCliente);
  const contacto_id = useCotizador((s) => s.contacto_id);
  const setContacto = useCotizador((s) => s.setContacto);
  const [q, setQ] = useState('');
  const [open, setOpen] = useState(false);

  const selected = useMemo(
    () => clientes?.find((c) => c.id === cliente_id) ?? null,
    [clientes, cliente_id],
  );

  const matches = useMemo(() => {
    const lista = clientes ?? [];
    const needle = q.trim().toLowerCase();
    if (!needle) return lista.slice(0, 50);
    return lista
      .filter(
        (c) =>
          c.nombre_empresa.toLowerCase().includes(needle) ||
          (c.rfc_tax_id ?? '').toLowerCase().includes(needle) ||
          (c.contacto_nombre ?? '').toLowerCase().includes(needle) ||
          (c.email ?? '').toLowerCase().includes(needle),
      )
      .slice(0, 50);
  }, [clientes, q]);

  // Contactos de la empresa seleccionada (para el sub-selector "Atiende a").
  const { data: contactos } = useQuery<ContactoLite[]>({
    queryKey: ['contactos', cliente_id],
    queryFn: () => api.get<ContactoLite[]>(`/api/clientes/${cliente_id}/contactos`),
    enabled: cliente_id !== null,
  });

  // Autollenar con el contacto principal cuando hay contactos y aún no hay
  // contacto elegido. El guard "solo si null" evita pisar el contacto de una
  // orden ya cargada en edición.
  useEffect(() => {
    if (cliente_id === null || contacto_id !== null) return;
    const lista = contactos ?? [];
    if (lista.length === 0) return;
    const principal = lista.find((c) => c.es_principal) ?? lista[0];
    setContacto(principal.id);
  }, [contactos, cliente_id, contacto_id, setContacto]);

  if (isLoading) {
    return (
      <div className="text-xs text-slate-500 dark:text-slate-400 px-3 py-2 border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900">
        Cargando clientes…
      </div>
    );
  }
  if (error) {
    return (
      <div className="text-xs text-rose-400 px-3 py-2 border border-rose-800 rounded-md bg-white dark:bg-slate-900">
        Error al cargar clientes
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="relative">
        {selected && !open ? (
          <button
            type="button"
            onClick={() => setOpen(true)}
            className="w-full text-left px-3 py-2 border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 hover:border-accent-glow transition"
          >
            <div className="text-sm font-medium">{selected.nombre_empresa}</div>
            <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
              {selected.rfc_tax_id && <span className="font-mono">{selected.rfc_tax_id}</span>}
              {selected.email && <span className="truncate">{selected.email}</span>}
            </div>
          </button>
        ) : (
          <div>
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500 dark:text-slate-400" />
              <Input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                onFocus={() => setOpen(true)}
                placeholder="Buscar cliente por nombre, RFC, contacto, correo…"
                className="pl-8"
                autoFocus={open}
              />
            </div>
            {open && (
              <div className="absolute left-0 right-0 mt-1 max-h-64 overflow-y-auto bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-md shadow-xl z-20">
                {matches.length === 0 ? (
                  <div className="px-3 py-4 text-xs text-slate-500 dark:text-slate-400 text-center">
                    Sin coincidencias
                  </div>
                ) : (
                  matches.map((c) => (
                    <button
                      key={c.id}
                      type="button"
                      onClick={() => {
                        setCliente(c.id);
                        setContacto(null);
                        setQ('');
                        setOpen(false);
                      }}
                      className="w-full text-left px-3 py-2 hover:bg-slate-100 dark:hover:bg-slate-800 transition border-b border-slate-200 dark:border-slate-800 last:border-b-0"
                    >
                      <div className="text-sm">{c.nombre_empresa}</div>
                      <div className="flex items-center gap-2 text-[11px] text-slate-500 dark:text-slate-400">
                        {c.rfc_tax_id && <span className="font-mono">{c.rfc_tax_id}</span>}
                        {c.email && <span className="truncate">{c.email}</span>}
                      </div>
                    </button>
                  ))
                )}
                {selected && (
                  <button
                    type="button"
                    onClick={() => {
                      setCliente(null);
                      setContacto(null);
                      setQ('');
                      setOpen(false);
                    }}
                    className="w-full text-left px-3 py-2 text-xs text-rose-400 hover:bg-rose-900/20 border-t border-slate-300 dark:border-slate-700"
                  >
                    Quitar selección
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {cliente_id !== null && (contactos ?? []).length > 0 && (
        <div>
          <label className="block text-[11px] uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">Atiende a</label>
          <select
            value={contacto_id ?? ''}
            onChange={(e) => setContacto(e.target.value ? Number(e.target.value) : null)}
            className="w-full h-8 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-2 text-xs"
          >
            <option value="">— Sin contacto —</option>
            {(contactos ?? []).map((c) => (
              <option key={c.id} value={c.id}>
                {c.nombre}{c.cargo ? ` · ${c.cargo}` : ''}{c.es_principal ? ' ★' : ''}
              </option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
}

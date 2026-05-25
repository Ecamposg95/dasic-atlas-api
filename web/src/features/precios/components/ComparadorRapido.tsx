import { useState } from 'react';
import { Trophy, Search } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { useCompararPorTexto } from '../hooks/usePrecios';
import type { Moneda } from '../types';

function fmtPrecio(precio: number, _moneda: Moneda): string {
  return `$${precio.toLocaleString('es-MX', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

/**
 * Comparador rápido: input de búsqueda libre por SKU o descripción.
 * Devuelve el mismo shape que ComparativaResponse, ordenado por precio asc.
 * El primer resultado (más barato) se resalta con icono Trophy.
 */
export function ComparadorRapido() {
  const [input, setInput] = useState('');
  // queryText es el último valor confirmado con Enter/botón. Mientras es '' el hook está disabled.
  const [queryText, setQueryText] = useState('');

  const { data, isFetching, error } = useCompararPorTexto(queryText);
  const items = data?.items ?? [];

  function submit() {
    const v = input.trim();
    if (!v) return;
    setQueryText(v);
  }

  return (
    <Card>
      <CardContent className="p-4">
        <h2 className="text-xs uppercase font-bold tracking-wider text-slate-500 dark:text-slate-400 mb-3">
          Comparador rápido
        </h2>

        <div className="flex flex-wrap gap-2 items-stretch">
          <div className="relative flex-1 min-w-[220px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 dark:text-slate-500 pointer-events-none" />
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') submit();
              }}
              placeholder="Buscar SKU o descripción…"
              className="pl-9"
            />
          </div>
          <Button size="sm" onClick={submit} disabled={!input.trim() || isFetching}>
            {isFetching ? 'Buscando…' : 'Comparar'}
          </Button>
        </div>

        {queryText && (
          <div className="mt-4">
            {error ? (
              <p className="text-sm text-rose-600 dark:text-rose-400">
                No se pudo comparar. Intenta de nuevo.
              </p>
            ) : items.length === 0 && !isFetching ? (
              <p className="text-sm text-slate-500 dark:text-slate-400 text-center py-4">
                Sin coincidencias para «{queryText}».
              </p>
            ) : (
              <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-800">
                <table className="w-full text-sm">
                  <thead className="bg-slate-50 dark:bg-slate-800/50 text-[10px] text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    <tr>
                      <th className="text-left p-2 w-10">#</th>
                      <th className="text-left p-2">Proveedor</th>
                      <th className="text-right p-2">Precio</th>
                      <th className="text-center p-2">Moneda</th>
                      <th className="text-left p-2">Vigencia</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((it, idx) => {
                      const isWinner = idx === 0;
                      return (
                        <tr
                          key={`${it.proveedor_id}-${it.precio_id}`}
                          className={
                            isWinner
                              ? 'bg-emerald-50 dark:bg-emerald-900/20 border-b border-slate-200 dark:border-slate-800'
                              : 'border-b border-slate-200 dark:border-slate-800'
                          }
                        >
                          <td className="p-2 text-xs text-slate-700 dark:text-slate-300">
                            <span className="inline-flex items-center gap-1">
                              {idx + 1}
                              {isWinner && (
                                <Trophy className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
                              )}
                            </span>
                          </td>
                          <td className="p-2 text-slate-800 dark:text-slate-200">
                            {it.proveedor_nombre ?? `Prov. ${it.proveedor_id}`}
                          </td>
                          <td
                            className={`p-2 text-right font-mono tabular-nums ${
                              isWinner
                                ? 'text-emerald-700 dark:text-emerald-300 font-semibold'
                                : 'text-slate-700 dark:text-slate-300'
                            }`}
                          >
                            {fmtPrecio(it.precio, it.moneda)}
                          </td>
                          <td className="p-2 text-center text-xs font-mono text-slate-600 dark:text-slate-400">
                            {it.moneda}
                          </td>
                          <td className="p-2 text-xs text-slate-600 dark:text-slate-400">
                            {it.fecha_vigencia_desde ?? '—'}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

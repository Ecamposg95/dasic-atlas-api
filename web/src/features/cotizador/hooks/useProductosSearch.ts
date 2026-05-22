import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useSinonimos } from './useSinonimos';
import { buildSearchVariants, levenshteinTruncated } from '../lib/search';
import type { Producto } from '../types';

// Debounce 300ms. Si query < 2 chars y no es vacío, deshabilita.
// Si vacío, devuelve los primeros 30 del catálogo (útil para mostrar algo
// cuando el dropdown se abre sin texto).
//
// Con sinónimos cargados: expande el término en hasta 5 variantes y consulta
// `/api/productos?q=<variant>` por cada una en paralelo. Deduplica por id y
// scorea cada resultado por mejor distancia Levenshtein contra el término
// original (mejor score → primero).

export type SearchResult = {
  producto: Producto;
  score: number; // 0..1, mayor es mejor match
};

export type SearchData = {
  items: SearchResult[];
  cantidad: number | null;
};

export function useProductosSearch(q: string) {
  const [debouncedQ, setDebouncedQ] = useState(q);
  const { data: sinonimos } = useSinonimos();

  useEffect(() => {
    const t = setTimeout(() => setDebouncedQ(q), 300);
    return () => clearTimeout(t);
  }, [q]);

  return useQuery<SearchData>({
    queryKey: ['productos', 'search', debouncedQ, !!sinonimos],
    queryFn: async () => {
      const dict = sinonimos?.dict ?? {};
      const { cantidad, queries } = buildSearchVariants(debouncedQ, dict);

      // Sin término → primeros 30 del catálogo
      if (queries.length === 0) {
        const p = new URLSearchParams({ page_size: '30' });
        const items = await api.get<Producto[]>(`/api/productos?${p.toString()}`);
        return {
          cantidad,
          items: items.map((producto) => ({ producto, score: 0.5 })),
        };
      }

      // Lanzar las queries en paralelo, deduplicar por id, scorear por Levenshtein.
      // El primer variante (i === 0) es el término literal del usuario y debe
      // burbujear errores (p.ej. 401) para que TanStack Query lo exponga vía
      // `error`. Los variantes secundarios (sinónimos) son best-effort y caen
      // a [] si fallan.
      const responses = await Promise.all(
        queries.map((variant, i) => {
          const p = new URLSearchParams({ q: variant, page_size: '20' });
          const promise = api.get<Producto[]>(`/api/productos?${p.toString()}`);
          return i === 0 ? promise : promise.catch(() => [] as Producto[]);
        }),
      );
      const map = new Map<number, SearchResult>();
      const termino = queries[0];
      responses.flat().forEach((producto) => {
        if (map.has(producto.id)) return;
        const hay = `${producto.sku} ${producto.sku_comercial ?? ''} ${producto.nombre} ${producto.marca ?? ''}`.toLowerCase();
        // score = 1 si match exacto del término, si no, 1 - distancia/longitud (truncada).
        let score = 0.5;
        if (hay.includes(termino)) {
          score = 1;
        } else {
          const tokens = hay.split(/\s+/);
          let best = Infinity;
          tokens.forEach((tok) => {
            const d = levenshteinTruncated(tok, termino, 2);
            if (d < best) best = d;
          });
          score = best === Infinity ? 0 : Math.max(0, 1 - best / Math.max(termino.length, 1));
        }
        map.set(producto.id, { producto, score });
      });
      const items = Array.from(map.values())
        .sort((a, b) => b.score - a.score)
        .slice(0, 30);
      return { cantidad, items };
    },
    enabled: debouncedQ.length === 0 || debouncedQ.length >= 2,
    staleTime: 30_000,
  });
}

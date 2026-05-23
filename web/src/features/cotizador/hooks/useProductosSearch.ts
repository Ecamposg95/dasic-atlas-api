import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useSinonimos } from './useSinonimos';
import { buildSearchVariants, levenshteinTruncated } from '../lib/search';
import type { Producto, Servicio } from '../types';

// Debounce 300ms. Si query < 2 chars y no es vacío, deshabilita.
// Si vacío, devuelve los primeros 30 del catálogo (útil para mostrar algo
// cuando el dropdown se abre sin texto).
//
// Con sinónimos cargados: expande el término en hasta 5 variantes y consulta
// `/api/productos?q=<variant>` por cada una en paralelo. Deduplica por id y
// scorea cada resultado por mejor distancia Levenshtein contra el término
// original (mejor score → primero).
//
// Phase 5 (Task 5.1): firma extendida con `scope` para soportar tabs
// Productos/Servicios y filtros marca/categoría. Notas sobre el backend:
//  - `/api/productos` SOLO acepta `q`, `marca` (texto), `skip`, `limit`. No
//    soporta `marca_id` ni `categoria_id`; los enviamos igualmente porque
//    FastAPI los ignora (future-proof si se agregan).
//  - El filtro de marca se aplica server-side enviando `marca=<nombre>`.
//  - El filtro de categoría se aplica CLIENT-side sobre la respuesta,
//    contra `producto.categoria` (texto). Si en el futuro el backend acepta
//    `categoria`, podemos quitar el filtro local.
//  - Para servicios (`scope.tipo === 'servicio'`) usamos `/api/servicios/buscar`
//    cuando hay query y `/api/servicios/` con `activo=true` cuando no. Desde
//    2026-05-23 el store soporta `addServicio`, así que devolvemos los
//    resultados en el campo `servicios` (separado de `items` para no mezclar
//    schemas Producto/Servicio).

export type SearchResult = {
  producto: Producto;
  score: number; // 0..1, mayor es mejor match
};

export type SearchData = {
  items: SearchResult[];
  // Resultados del catálogo de servicios. Solo populado cuando
  // `scope.tipo === 'servicio'`; en otros modos siempre vacío.
  servicios: Servicio[];
  cantidad: number | null;
};

export type SearchScope = {
  q: string;
  tipo: 'producto' | 'servicio';
  marca_id?: number | null;
  marca_nombre?: string | null;
  categoria_id?: number | null;
  categoria_nombre?: string | null;
};

export function useProductosSearch(scope: SearchScope) {
  const [debouncedQ, setDebouncedQ] = useState(scope.q);
  const { data: sinonimos } = useSinonimos();

  useEffect(() => {
    const t = setTimeout(() => setDebouncedQ(scope.q), 300);
    return () => clearTimeout(t);
  }, [scope.q]);

  return useQuery<SearchData>({
    queryKey: [
      'productos',
      'search',
      debouncedQ,
      scope.tipo,
      scope.marca_id ?? null,
      scope.marca_nombre ?? null,
      scope.categoria_id ?? null,
      scope.categoria_nombre ?? null,
      !!sinonimos,
    ],
    queryFn: async () => {
      const dict = sinonimos?.dict ?? {};
      const { cantidad, queries } = buildSearchVariants(debouncedQ, dict);

      // Servicios: usamos `/api/servicios/` (lista filtrable) cuando no hay
      // término, y `/api/servicios/buscar?q=…` cuando lo hay. El backend
      // (`app/routers/servicios.py:99`) busca en codigo/nombre/descripcion.
      // No reutilizamos sinónimos aquí — el set de servicios es chico y los
      // typos no son tan comunes como en productos.
      if (scope.tipo === 'servicio') {
        const termino = (queries[0] ?? '').trim();
        try {
          let servicios: Servicio[];
          if (termino) {
            const p = new URLSearchParams();
            p.set('q', termino);
            p.set('limit', '30');
            servicios = await api.get<Servicio[]>(`/api/servicios/buscar?${p.toString()}`);
          } else {
            const p = new URLSearchParams();
            p.set('activo', 'true');
            servicios = await api.get<Servicio[]>(`/api/servicios/?${p.toString()}`);
          }
          return { items: [], servicios, cantidad };
        } catch (err) {
          // 401 burbujea para que ProductSearch redirija a login; el resto
          // tampoco lo silenciamos porque el usuario espera ver algo.
          throw err;
        }
      }

      // Build base params. Sólo `marca` (texto) es filtro real server-side
      // para productos; los `*_id` van por compatibilidad future-proof.
      const baseParams = new URLSearchParams();
      if (scope.marca_id != null) baseParams.set('marca_id', String(scope.marca_id));
      if (scope.marca_nombre) baseParams.set('marca', scope.marca_nombre);
      if (scope.categoria_id != null) baseParams.set('categoria_id', String(scope.categoria_id));
      if (scope.categoria_nombre) baseParams.set('categoria', scope.categoria_nombre);

      // Filtro client-side de categoría (backend aún no la soporta).
      const filtrarCategoria = (items: Producto[]) => {
        if (!scope.categoria_nombre) return items;
        const target = scope.categoria_nombre.trim().toLowerCase();
        return items.filter((p) => (p.categoria ?? '').trim().toLowerCase() === target);
      };

      // Sin término → primeros 30 del catálogo
      if (queries.length === 0) {
        const p = new URLSearchParams(baseParams);
        p.set('limit', '30');
        const items = await api.get<Producto[]>(`/api/productos?${p.toString()}`);
        return {
          cantidad,
          items: filtrarCategoria(items).map((producto) => ({ producto, score: 0.5 })),
          servicios: [],
        };
      }

      // Lanzar las queries en paralelo, deduplicar por id, scorear por Levenshtein.
      // El primer variante (i === 0) es el término literal del usuario y debe
      // burbujear errores (p.ej. 401) para que TanStack Query lo exponga vía
      // `error`. Los variantes secundarios (sinónimos) son best-effort y caen
      // a [] si fallan.
      // Cuando hay filtro de categoría (que se aplica client-side), ampliamos
      // la red por variante para evitar pantallas vacías en categorías nicho
      // donde los primeros 20 resultados no contienen matches.
      const limitPerVariant = scope.categoria_nombre ? 100 : 20;
      const responses = await Promise.all(
        queries.map((variant, i) => {
          const p = new URLSearchParams(baseParams);
          p.set('q', variant);
          p.set('limit', String(limitPerVariant));
          const promise = api.get<Producto[]>(`/api/productos?${p.toString()}`);
          return i === 0 ? promise : promise.catch(() => [] as Producto[]);
        }),
      );
      const map = new Map<number, SearchResult>();
      const termino = queries[0];
      const productosFiltrados = filtrarCategoria(responses.flat());
      productosFiltrados.forEach((producto) => {
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
      return { cantidad, items, servicios: [] };
    },
    enabled: debouncedQ.length === 0 || debouncedQ.length >= 2,
    staleTime: 30_000,
  });
}

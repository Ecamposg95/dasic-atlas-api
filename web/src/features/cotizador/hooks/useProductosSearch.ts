import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Producto } from '../types';

// Debounce 300ms para no spammear el backend al teclear.
// Si query < 2 chars y no es vacío, devuelve []. Si vacío, devuelve los primeros 30
// del catálogo (útil para mostrar algo cuando el dropdown se abre sin texto).

export function useProductosSearch(q: string) {
  const [debouncedQ, setDebouncedQ] = useState(q);

  useEffect(() => {
    const t = setTimeout(() => setDebouncedQ(q), 300);
    return () => clearTimeout(t);
  }, [q]);

  return useQuery<Producto[]>({
    queryKey: ['productos-search', debouncedQ],
    queryFn: () => {
      const params = new URLSearchParams();
      if (debouncedQ) params.set('q', debouncedQ);
      params.set('page_size', '30');
      return api.get<Producto[]>(`/api/productos?${params.toString()}`);
    },
    enabled: debouncedQ.length === 0 || debouncedQ.length >= 2,
    staleTime: 30_000,
  });
}

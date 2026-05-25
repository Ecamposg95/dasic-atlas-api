import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Producto } from '../types';

// Carga todos los productos (page_size=200). Los filtros son client-side
// ya que el catálogo suele ser <500 items.

export function useProductos() {
  return useQuery<Producto[]>({
    queryKey: ['productos'],
    queryFn: () => api.get<Producto[]>('/api/productos?page_size=200'),
    staleTime: 30_000,
  });
}

// Respuesta del endpoint POST /api/productos/upload-csv.
// Caso éxito: { mensaje, creados, actualizados, omitidos, errores: string[] }.
// Caso 4xx: { detail: { mensaje?, columnas_compatibles? } } o { detail: string }.
export type ImportProductosResult = {
  mensaje?: string;
  creados: number;
  actualizados: number;
  omitidos: number;
  errores: string[];
};

export type ImportProductosError = {
  status: number;
  mensaje: string;
  columnas_compatibles?: string[];
};

// Hook para importar productos vía CSV/XLSX. Usa fetch directo (no api.post)
// porque el wrapper en @/lib/api hardcodea Content-Type: application/json y
// FormData necesita que el navegador setee multipart/form-data con boundary.
// Invalida ['productos'] al éxito para refrescar el listado.
export function useImportProductos() {
  const qc = useQueryClient();
  return useMutation<ImportProductosResult, ImportProductosError, File>({
    mutationFn: async (file) => {
      const body = new FormData();
      body.append('file', file);
      const r = await fetch('/api/productos/upload-csv', {
        method: 'POST',
        body,
        credentials: 'include',
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) {
        const detail = (data as { detail?: unknown }).detail;
        if (detail && typeof detail === 'object') {
          const d = detail as { mensaje?: string; columnas_compatibles?: string[] };
          throw {
            status: r.status,
            mensaje: d.mensaje ?? 'No se pudo importar el archivo.',
            columnas_compatibles: d.columnas_compatibles,
          } satisfies ImportProductosError;
        }
        throw {
          status: r.status,
          mensaje: typeof detail === 'string' ? detail : 'No se pudo importar el archivo.',
        } satisfies ImportProductosError;
      }
      return data as ImportProductosResult;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['productos'] });
    },
  });
}

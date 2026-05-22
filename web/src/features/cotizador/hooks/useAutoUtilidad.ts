import { api } from '@/lib/api';

// Shape REAL del backend (`app/routers/ventas.py:1802`):
//   { sugerido: number, fuente: 'cliente_producto'|'cliente'|'producto'|'default', n: number }
// El plan asume `utilidad_sugerida`; aquí adaptamos al nombre real `sugerido`.
type AutoUtilidadResponse = {
  sugerido: number;
  fuente: string;
  n: number;
};

/**
 * Devuelve la utilidad % sugerida para (cliente, producto). Si no hay cliente o el
 * backend falla, devuelve null y el caller usa su default.
 *
 * Nota: el backend SIEMPRE responde algo (default 30) — sólo devolvemos null si
 * la llamada falla o el shape es inválido, para no sobreescribir el 30 default del store.
 */
export async function fetchAutoUtilidad(
  cliente_id: number | null,
  producto_id: number,
): Promise<number | null> {
  if (cliente_id == null) return null;
  try {
    const p = new URLSearchParams({
      cliente_id: String(cliente_id),
      producto_id: String(producto_id),
    });
    const r = await api.get<AutoUtilidadResponse>(`/api/ventas/auto-utilidad?${p.toString()}`);
    const v = Number(r?.sugerido);
    return Number.isFinite(v) ? v : null;
  } catch {
    return null;
  }
}

// web/src/lib/permissions.ts
//
// Helpers centralizados para chequeos de rol en la SPA.
//
// Backend (`/api/auth/me` → `capabilities_for`) entrega `rol` en lowercase
// (`'administrador'`, `'superadmin'`, `'gerente_comercial'`, `'ventas'`,
// `'operativo'`). Cualquier comparación con UPPERCASE como `'ADMINISTRADOR'`
// es un bug: el check siempre da `false` y los admins no ven sus botones.
//
// Estos hooks normalizan a lowercase y aceptan también los aliases legacy
// (`'admin'`, `'asistente'`) por si quedan rows con rol viejo en DB.

import { useAuth } from '@/stores/auth';

function normalize(rol: string | null | undefined): string {
  return (rol ?? '').toLowerCase();
}

/**
 * Admin tier puro: ADMINISTRADOR o SUPERADMIN.
 * Úsalo para acciones destructivas / configuración crítica
 * (eliminar producto, override TC, marcar vencidos, etc.).
 */
export function useIsAdmin(): boolean {
  const user = useAuth((s) => s.user);
  const rol = normalize(user?.rol);
  // 'admin' es alias legacy aceptado por el backend al leer rows viejos.
  return rol === 'administrador' || rol === 'superadmin' || rol === 'admin';
}

/** SUPERADMIN estricto (NO incluye administrador). Para la consola de plataforma. */
export function useIsSuperadmin(): boolean {
  const user = useAuth((s) => s.user);
  return normalize(user?.rol) === 'superadmin';
}

/**
 * Admin tier + Gerente Comercial.
 * Úsalo para vistas/acciones de mando intermedio que NO requieren
 * un admin puro (p.ej. ver totales de ventas en Reportes).
 */
export function useIsAdminOrGerente(): boolean {
  const user = useAuth((s) => s.user);
  const rol = normalize(user?.rol);
  return (
    rol === 'administrador' ||
    rol === 'superadmin' ||
    rol === 'admin' ||
    rol === 'gerente_comercial'
  );
}

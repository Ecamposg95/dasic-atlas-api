// web/src/features/superadmin/hooks/useUsuariosPlataforma.ts
// Hook de gestión de usuarios desde la consola de plataforma (superadmin).
// Usa el mismo backend /api/usuarios/* pero con queryKey separado para no
// contaminar el cache de la sección de usuarios regular.

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Usuario, UsuarioCreate, UsuarioUpdate } from '@/features/usuarios/types';

type ApiErr = { status?: number; detail?: string };

const QK = ['superadmin', 'usuarios'] as const;

// ─── Queries ──────────────────────────────────────────────────────────────────

export function useUsuariosPlataforma() {
  return useQuery<Usuario[], ApiErr>({
    queryKey: QK,
    queryFn: () => api.get<Usuario[]>('/api/usuarios/'),
    staleTime: 30_000,
  });
}

// ─── Mutations ────────────────────────────────────────────────────────────────

export function useCrearUsuario() {
  const qc = useQueryClient();
  return useMutation<Usuario, ApiErr, UsuarioCreate>({
    mutationFn: (body) => api.post<Usuario>('/api/usuarios/', body),
    onSuccess: () => { qc.invalidateQueries({ queryKey: QK }); },
  });
}

export function useEditarUsuario() {
  const qc = useQueryClient();
  return useMutation<Usuario, ApiErr, { id: number; payload: UsuarioUpdate }>({
    mutationFn: ({ id, payload }) => api.put<Usuario>(`/api/usuarios/${id}`, payload),
    onSuccess: () => { qc.invalidateQueries({ queryKey: QK }); },
  });
}

/** Body field is `password` — confirmed from PasswordResetIn in app/routers/usuarios.py */
export function useResetPassword() {
  const qc = useQueryClient();
  return useMutation<unknown, ApiErr, { id: number; password: string }>({
    mutationFn: ({ id, password }) =>
      api.post(`/api/usuarios/${id}/password`, { password }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: QK }); },
  });
}

export function useEliminarUsuario() {
  const qc = useQueryClient();
  return useMutation<unknown, ApiErr, number>({
    mutationFn: (id) => api.delete(`/api/usuarios/${id}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: QK }); },
  });
}

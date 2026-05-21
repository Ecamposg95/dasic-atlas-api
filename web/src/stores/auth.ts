import { create } from 'zustand';

export type User = {
  id: number;
  email: string;
  nombre: string;
  activo: boolean;
  rol: string | null;
  rol_label: string;
  modulos_visibles: string[];
  // Capability flags + gestionar_usuarios (de capabilities_for); pueden variar.
  [key: string]: unknown;
};

type AuthState = {
  user: User | null;
  setUser: (u: User | null) => void;
};

export const useAuth = create<AuthState>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
}));

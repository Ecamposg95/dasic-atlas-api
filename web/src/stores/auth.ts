import { create } from 'zustand';

export type User = {
  id: number;
  email: string;
  nombre: string;
  rol: string;
};

type AuthState = {
  user: User | null;
  setUser: (u: User | null) => void;
};

export const useAuth = create<AuthState>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
}));

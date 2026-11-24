import { create } from 'zustand';

// Estado global de "plataforma suspendida". Lo enciende el wrapper de `api`
// cuando cualquier request responde 423, y lo lee el Layout para tapar la app
// con la pantalla de suspensión — así una sesión ya abierta se entera en la
// siguiente llamada, sin esperar a recargar.
type SuspensionState = {
  mensaje: string | null;
  suspender: (mensaje: string) => void;
  limpiar: () => void;
};

export const useSuspension = create<SuspensionState>((set) => ({
  mensaje: null,
  suspender: (mensaje) => set({ mensaje }),
  limpiar: () => set({ mensaje: null }),
}));

export const STATUS_SUSPENDIDA = 423;

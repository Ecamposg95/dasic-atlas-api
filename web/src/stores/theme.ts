import { create } from 'zustand';

export type ThemeMode = 'light' | 'dark' | 'auto';

const STORAGE_KEY = 'atlas-one-theme';

function readStored(): ThemeMode {
  if (typeof window === 'undefined') return 'dark';
  const v = window.localStorage.getItem(STORAGE_KEY);
  if (v === 'light' || v === 'dark' || v === 'auto') return v;
  return 'dark';
}

function prefersDark(): boolean {
  if (typeof window === 'undefined' || !window.matchMedia) return true;
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
}

export function resolveTheme(mode: ThemeMode): 'light' | 'dark' {
  if (mode === 'auto') return prefersDark() ? 'dark' : 'light';
  return mode;
}

/** Apply the resolved theme class to <html> and persist the chosen mode. */
function applyTheme(mode: ThemeMode) {
  if (typeof document === 'undefined') return;
  const resolved = resolveTheme(mode);
  const root = document.documentElement;
  if (resolved === 'dark') root.classList.add('dark');
  else root.classList.remove('dark');
  root.setAttribute('data-theme', resolved);
}

type ThemeState = {
  mode: ThemeMode;
  setMode: (m: ThemeMode) => void;
  cycle: () => void;
};

export const useTheme = create<ThemeState>((set, get) => ({
  mode: readStored(),
  setMode: (mode) => {
    window.localStorage.setItem(STORAGE_KEY, mode);
    applyTheme(mode);
    set({ mode });
  },
  cycle: () => {
    const order: ThemeMode[] = ['light', 'dark', 'auto'];
    const idx = order.indexOf(get().mode);
    const next = order[(idx + 1) % order.length];
    get().setMode(next);
  },
}));

/** Bootstrap theme on app boot. Call once from main.tsx. */
export function initTheme() {
  const mode = useTheme.getState().mode;
  applyTheme(mode);
  // Listen for system preference changes when in auto mode.
  if (typeof window !== 'undefined' && window.matchMedia) {
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = () => {
      if (useTheme.getState().mode === 'auto') applyTheme('auto');
    };
    mq.addEventListener?.('change', handler);
  }
}

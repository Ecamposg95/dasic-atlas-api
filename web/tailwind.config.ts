import type { Config } from 'tailwindcss';

export default {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Paleta del sidebar via CSS vars (light/dark en index.css).
        sidebar: {
          DEFAULT: 'var(--sidebar-bg)',
          bottom: 'var(--sidebar-bottom)',
          text: 'var(--sidebar-text)',
          dim: 'var(--sidebar-dim)',
          border: 'var(--sidebar-border)',
          hover: 'var(--sidebar-hover)',
          strong: 'var(--sidebar-strong)',
          active: 'var(--sidebar-active)',
          activebg: 'var(--sidebar-activebg)',
        },
        accent: {
          glow: '#00d4e0',
          deep: '#2563eb',
        },
      },
      fontFamily: {
        sans: ['Outfit', 'ui-sans-serif', 'system-ui'],
      },
    },
  },
  plugins: [],
} satisfies Config;

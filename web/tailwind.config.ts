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
          // CIRCUITO · esmeralda técnica (DASIC). Van por CSS var para que la
          // consola de plataforma (.atlas-console) las cambie a ember.
          glow: 'rgb(var(--accent-glow) / <alpha-value>)',
          deep: 'rgb(var(--accent-deep) / <alpha-value>)',
        },
        // Marca Atlas Tech (skill atlas-tech-brand). Solo para la firma de
        // Atlas y la consola de plataforma; la app de DASIC sigue en esmeralda.
        atlas: {
          ember: '#FF6A1F',
          amber: '#FFA14A',
          glow: '#FFD3A8',
          deep: '#7A240A',
          'ember-text': '#B53A09',
          indigo: '#5B58B8',
          lavanda: '#9AA6E0',
          tinta: '#17162B',
          ink: '#F5F2EE',
          black: '#050505',
        },
        // Semantic tokens (HSL channel format for alpha support)
        background: 'hsl(var(--background) / <alpha-value>)',
        surface: {
          DEFAULT: 'hsl(var(--surface) / <alpha-value>)',
          2: 'hsl(var(--surface-2) / <alpha-value>)',
        },
        card: 'hsl(var(--surface) / <alpha-value>)',
        foreground: 'hsl(var(--foreground) / <alpha-value>)',
        'muted-foreground': 'hsl(var(--muted-foreground) / <alpha-value>)',
        border: 'hsl(var(--border) / <alpha-value>)',
        'border-strong': 'hsl(var(--border-strong) / <alpha-value>)',
        ring: 'hsl(var(--ring) / <alpha-value>)',
        primary: {
          DEFAULT: 'hsl(var(--primary) / <alpha-value>)',
          foreground: 'hsl(var(--primary-foreground) / <alpha-value>)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'Segoe UI', 'Arial', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Consolas', 'monospace'],
      },
      boxShadow: {
        'elev-1': '0 1px 2px -1px hsl(var(--shadow-color) / 0.08), 0 2px 6px -2px hsl(var(--shadow-color) / 0.10)',
        'elev-2': '0 2px 4px -2px hsl(var(--shadow-color) / 0.10), 0 8px 24px -6px hsl(var(--shadow-color) / 0.14)',
        'elev-3': '0 8px 32px -8px hsl(var(--shadow-color) / 0.20)',
        'glow-accent': '0 0 0 1px hsl(var(--ring) / 0.20), 0 0 24px -6px hsl(var(--ring) / 0.35)',
      },
      borderRadius: {
        xl: '0.875rem',
        '2xl': '1.25rem',
      },
      transitionTimingFunction: {
        premium: 'cubic-bezier(0.16, 1, 0.3, 1)',
      },
    },
  },
  plugins: [],
} satisfies Config;

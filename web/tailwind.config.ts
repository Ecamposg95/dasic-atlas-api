import type { Config } from 'tailwindcss';

export default {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Paleta dark + cyan accent (matching base.html actual).
        sidebar: {
          DEFAULT: '#0a1429',
          bottom: '#050a1a',
          text: '#cbd5e1',
          dim: '#64748b',
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

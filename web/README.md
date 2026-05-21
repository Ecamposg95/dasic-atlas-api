# DASIC Web — SPA

Frontend con React + Vite + TypeScript + Tailwind + shadcn/ui.

## Scripts

```bash
npm install          # primera vez
npm run dev          # dev server en :5173, proxea /api/* a localhost:8000
npm run build        # build a ../app/static/dist/ (consumido por FastAPI)
npm run typecheck    # solo tipos, sin emit
npm run types:gen    # regenera src/types/api.ts desde /openapi.json (FastAPI corriendo)
```

## Desarrollo local

1. Levanta el backend en otra terminal: `uvicorn app.main:app --reload` (desde la raíz del repo).
2. `npm run dev` en este directorio.
3. Abre `http://localhost:5173/spa/login`.

La cookie de auth se preserva porque ambos puertos están en `localhost`.

## Estructura

```
src/
├── main.tsx                # entry point
├── App.tsx                 # providers (QueryClient, Router)
├── router.tsx              # rutas /spa/*
├── index.css               # Tailwind directives
├── lib/
│   ├── api.ts              # fetch wrapper con credentials:'include'
│   ├── queryClient.ts      # TanStack Query setup
│   └── utils.ts            # cn() helper
├── stores/
│   └── auth.ts             # Zustand: user actual
├── components/
│   ├── ui/                 # shadcn primitives (copy-paste, no es librería)
│   └── layout/             # Sidebar, Header, Layout
├── features/
│   ├── auth/               # login
│   └── hello/              # placeholder Phase 0
└── types/
    └── api.ts              # generado (no editar a mano)
```

## Convenciones

- Tipos compartidos con el backend: `npm run types:gen` los regenera desde el OpenAPI.
- Estado de servidor: TanStack Query. Estado UI local: useState / Zustand store.
- Componentes UI: shadcn/ui copy-paste. Si necesitas modificarlos, vive en `src/components/ui/`.
- Iconos: `lucide-react`. NO Font Awesome.

Migración por fases — ver `docs/superpowers/specs/2026-05-21-spa-migration-phase-0-foundation.md`.

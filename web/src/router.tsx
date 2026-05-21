import { createBrowserRouter, Navigate } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { LoginPage } from '@/features/auth/pages/LoginPage';
import { HelloPage } from '@/features/hello/pages/HelloPage';
import { CotizadorPage } from '@/features/cotizador/pages/CotizadorPage';

export const router = createBrowserRouter([
  {
    path: '/spa',
    element: <Layout />,
    children: [
      { index: true, element: <Navigate to="/spa/hello" replace /> },
      { path: 'login', element: <LoginPage /> },
      { path: 'hello', element: <HelloPage /> },
      { path: 'cotizador', element: <CotizadorPage /> },
    ],
  },
  {
    // Rutas legacy que ya viven en el SPA. Aplica solo cuando el handler de
    // FastAPI para esa URL se haya movido del Jinja al SPA catch-all
    // (swap atómico en Phase 1d).
    path: '/ventas',
    element: <Layout />,
    children: [{ path: 'cotizador', element: <CotizadorPage /> }],
  },
]);

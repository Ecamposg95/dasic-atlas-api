import { createBrowserRouter, Navigate } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { LoginPage } from '@/features/auth/pages/LoginPage';
import { HelloPage } from '@/features/hello/pages/HelloPage';
import { DashboardPage } from '@/features/dashboard/pages/DashboardPage';
import { CotizadorPage } from '@/features/cotizador/pages/CotizadorPage';
import { BorradoresPage } from '@/features/borradores/pages/BorradoresPage';
import { SeguimientoPage } from '@/features/seguimiento/pages/SeguimientoPage';
import { FantasmasPage } from '@/features/fantasmas/pages/FantasmasPage';
import { ClientesPage } from '@/features/clientes/pages/ClientesPage';
import { InventarioPage } from '@/features/inventario/pages/InventarioPage';
import { CatalogosPage } from '@/features/catalogos/pages/CatalogosPage';
import { ComprasPage } from '@/features/compras/pages/ComprasPage';
import { RemisionesPage } from '@/features/remisiones/pages/RemisionesPage';
import { GastosPage } from '@/features/gastos/pages/GastosPage';
import { ReportesPage } from '@/features/reportes/pages/ReportesPage';
import { ReportesServicioPage } from '@/features/reportes_servicio/pages/ReportesServicioPage';
import { CuentasPorCobrarPage } from '@/features/cxc/pages/CuentasPorCobrarPage';
import { FxPage } from '@/features/fx/pages/FxPage';
import { PreciosPage } from '@/features/precios/pages/PreciosPage';
import { UsuariosPage } from '@/features/usuarios/pages/UsuariosPage';
import { ServiciosPage } from '@/features/servicios/pages/ServiciosPage';

export const router = createBrowserRouter([
  {
    path: '/spa',
    element: <Layout />,
    children: [
      { index: true, element: <Navigate to="/spa/dashboard" replace /> },
      { path: 'login', element: <LoginPage /> },
      { path: 'hello', element: <HelloPage /> },
      { path: 'dashboard', element: <DashboardPage /> },
      { path: 'cotizador', element: <CotizadorPage /> },
      { path: 'borradores', element: <BorradoresPage /> },
      { path: 'seguimiento', element: <SeguimientoPage /> },
      { path: 'fantasmas', element: <FantasmasPage /> },
      { path: 'clientes', element: <ClientesPage /> },
      { path: 'inventario', element: <InventarioPage /> },
      { path: 'catalogos', element: <CatalogosPage /> },
      { path: 'compras', element: <ComprasPage /> },
      { path: 'remisiones', element: <RemisionesPage /> },
      { path: 'gastos', element: <GastosPage /> },
      { path: 'reportes', element: <ReportesPage /> },
      { path: 'reportes-servicio', element: <ReportesServicioPage /> },
      { path: 'cuentas-por-cobrar', element: <CuentasPorCobrarPage /> },
      { path: 'fx', element: <FxPage /> },
      { path: 'precios', element: <PreciosPage /> },
      { path: 'usuarios', element: <UsuariosPage /> },
      { path: 'servicios', element: <ServiciosPage /> },
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
  {
    // Ruta legacy /borradores — swap cuando FastAPI ceda la URL al SPA.
    path: '/borradores',
    element: <Layout />,
    children: [{ index: true, element: <BorradoresPage /> }],
  },
  {
    // Ruta legacy /seguimiento — swap cuando FastAPI ceda la URL al SPA.
    path: '/seguimiento',
    element: <Layout />,
    children: [{ index: true, element: <SeguimientoPage /> }],
  },
  {
    // Ruta legacy /fantasmas — swap cuando FastAPI ceda la URL al SPA.
    path: '/fantasmas',
    element: <Layout />,
    children: [{ index: true, element: <FantasmasPage /> }],
  },
  {
    // Ruta legacy /clientes — swap cuando FastAPI ceda la URL al SPA.
    path: '/clientes',
    element: <Layout />,
    children: [{ index: true, element: <ClientesPage /> }],
  },
  {
    // Ruta legacy /inventario — swap cuando FastAPI ceda la URL al SPA.
    path: '/inventario',
    element: <Layout />,
    children: [{ index: true, element: <InventarioPage /> }],
  },
  {
    // Ruta legacy /catalogos — swap cuando FastAPI ceda la URL al SPA.
    path: '/catalogos',
    element: <Layout />,
    children: [{ index: true, element: <CatalogosPage /> }],
  },
  {
    // Ruta legacy /dashboard — swap cuando FastAPI ceda la URL al SPA.
    path: '/dashboard',
    element: <Layout />,
    children: [{ index: true, element: <DashboardPage /> }],
  },
  {
    // Ruta legacy /compras — swap cuando FastAPI ceda la URL al SPA.
    path: '/compras',
    element: <Layout />,
    children: [{ index: true, element: <ComprasPage /> }],
  },
  {
    // Ruta legacy /remisiones — swap cuando FastAPI ceda la URL al SPA.
    path: '/remisiones',
    element: <Layout />,
    children: [{ index: true, element: <RemisionesPage /> }],
  },
  {
    // Ruta legacy /gastos — swap cuando FastAPI ceda la URL al SPA.
    path: '/gastos',
    element: <Layout />,
    children: [{ index: true, element: <GastosPage /> }],
  },
  {
    // Ruta legacy /reportes — swap cuando FastAPI ceda la URL al SPA.
    path: '/reportes',
    element: <Layout />,
    children: [{ index: true, element: <ReportesPage /> }],
  },
  {
    // Ruta legacy /reportes-servicio — swap cuando FastAPI ceda la URL al SPA.
    path: '/reportes-servicio',
    element: <Layout />,
    children: [{ index: true, element: <ReportesServicioPage /> }],
  },
  {
    // Ruta legacy /cuentas-por-cobrar — swap cuando FastAPI ceda la URL al SPA.
    path: '/cuentas-por-cobrar',
    element: <Layout />,
    children: [{ index: true, element: <CuentasPorCobrarPage /> }],
  },
  {
    // Ruta legacy /fx — swap cuando FastAPI ceda la URL al SPA.
    path: '/fx',
    element: <Layout />,
    children: [{ index: true, element: <FxPage /> }],
  },
  {
    // Ruta legacy /precios — swap cuando FastAPI ceda la URL al SPA.
    path: '/precios',
    element: <Layout />,
    children: [{ index: true, element: <PreciosPage /> }],
  },
  {
    // Ruta legacy /usuarios — swap cuando FastAPI ceda la URL al SPA.
    path: '/usuarios',
    element: <Layout />,
    children: [{ index: true, element: <UsuariosPage /> }],
  },
  {
    // Ruta legacy /servicios — swap cuando FastAPI ceda la URL al SPA.
    path: '/servicios',
    element: <Layout />,
    children: [{ index: true, element: <ServiciosPage /> }],
  },
]);

import { createBrowserRouter, Navigate } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { LoginPage } from '@/features/auth/pages/LoginPage';

// Code-split: cada página se carga on-demand al navegar a ella.
// React Router v6.4 acepta `lazy: async () => ({ Component })` por route.
// LoginPage queda eager porque es la ruta crítica del primer paint.
//
// Esto baja el bundle inicial de ~520kB a ~150kB (vendor + shell + dashboard).
// Las otras pages bajan en chunks separados según el usuario navega.

const lazyPage = <K extends string>(loader: () => Promise<Record<K, React.ComponentType>>, key: K) =>
  async () => {
    const mod = await loader();
    return { Component: mod[key] };
  };

const hello = lazyPage(() => import('@/features/hello/pages/HelloPage'), 'HelloPage');
const dashboard = lazyPage(() => import('@/features/dashboard/pages/DashboardPage'), 'DashboardPage');
const cotizador = lazyPage(() => import('@/features/cotizador/pages/CotizadorPage'), 'CotizadorPage');
const borradores = lazyPage(() => import('@/features/borradores/pages/BorradoresPage'), 'BorradoresPage');
const seguimiento = lazyPage(() => import('@/features/seguimiento/pages/SeguimientoPage'), 'SeguimientoPage');
const fantasmas = lazyPage(() => import('@/features/fantasmas/pages/FantasmasPage'), 'FantasmasPage');
const clientes = lazyPage(() => import('@/features/clientes/pages/ClientesPage'), 'ClientesPage');
const unificarEmpresas = lazyPage(() => import('@/features/clientes/pages/UnificarEmpresasPage'), 'UnificarEmpresasPage');
const contactos = lazyPage(() => import('@/features/contactos/pages/ContactosPage'), 'ContactosPage');
const inventario = lazyPage(() => import('@/features/inventario/pages/InventarioPage'), 'InventarioPage');
const catalogos = lazyPage(() => import('@/features/catalogos/pages/CatalogosPage'), 'CatalogosPage');
const compras = lazyPage(() => import('@/features/compras/pages/ComprasPage'), 'ComprasPage');
const remisiones = lazyPage(() => import('@/features/remisiones/pages/RemisionesPage'), 'RemisionesPage');
const crearRemision = lazyPage(() => import('@/features/remisiones/pages/CrearRemisionPage'), 'CrearRemisionPage');
const gastos = lazyPage(() => import('@/features/gastos/pages/GastosPage'), 'GastosPage');
const reportes = lazyPage(() => import('@/features/reportes/pages/ReportesPage'), 'ReportesPage');
const reportesServicio = lazyPage(() => import('@/features/reportes_servicio/pages/ReportesServicioPage'), 'ReportesServicioPage');
const reportesServicioDocs = lazyPage(
  () => import('@/features/reportes_servicio_docs/pages/ReportesServicioDocsPage'),
  'ReportesServicioDocsPage',
);
const cxc = lazyPage(() => import('@/features/cxc/pages/CuentasPorCobrarPage'), 'CuentasPorCobrarPage');
const fx = lazyPage(() => import('@/features/fx/pages/FxPage'), 'FxPage');
const precios = lazyPage(() => import('@/features/precios/pages/PreciosPage'), 'PreciosPage');
const usuarios = lazyPage(() => import('@/features/usuarios/pages/UsuariosPage'), 'UsuariosPage');
const servicios = lazyPage(() => import('@/features/servicios/pages/ServiciosPage'), 'ServiciosPage');
const superadmin = lazyPage(() => import('@/features/superadmin/pages/SuperAdminPage'), 'SuperAdminPage');

// Helper: ruta legacy que envuelve el mismo Layout y mounta el mismo lazy.
const legacyRoute = (path: string, lazyLoader: ReturnType<typeof lazyPage>) => ({
  path,
  element: <Layout />,
  children: [{ index: true, lazy: lazyLoader }],
});

export const router = createBrowserRouter([
  // Login (público) — fuera del Layout (sin sidebar/header).
  // Sirve también la URL `/` (matching el flujo previo de Jinja).
  { path: '/', element: <LoginPage /> },
  { path: '/login', element: <LoginPage /> },
  {
    path: '/spa',
    element: <Layout />,
    children: [
      { index: true, element: <Navigate to="/spa/dashboard" replace /> },
      { path: 'login', element: <LoginPage /> },
      { path: 'hello', lazy: hello },
      { path: 'dashboard', lazy: dashboard },
      { path: 'cotizador', lazy: cotizador },
      { path: 'borradores', lazy: borradores },
      { path: 'seguimiento', lazy: seguimiento },
      { path: 'fantasmas', lazy: fantasmas },
      { path: 'clientes', lazy: clientes },
      { path: 'empresas-unificar', lazy: unificarEmpresas },
      { path: 'contactos', lazy: contactos },
      { path: 'inventario', lazy: inventario },
      { path: 'catalogos', lazy: catalogos },
      { path: 'compras', lazy: compras },
      { path: 'remisiones', lazy: remisiones },
      { path: 'remisiones-nueva', lazy: crearRemision },
      { path: 'gastos', lazy: gastos },
      { path: 'reportes', lazy: reportes },
      { path: 'reportes-servicio', lazy: reportesServicio },
      { path: 'reportes-servicio-docs', lazy: reportesServicioDocs },
      { path: 'cuentas-por-cobrar', lazy: cxc },
      { path: 'fx', lazy: fx },
      { path: 'precios', lazy: precios },
      { path: 'usuarios', lazy: usuarios },
      { path: 'servicios', lazy: servicios },
      { path: 'superadmin', lazy: superadmin },
    ],
  },
  // Rutas legacy — FastAPI sirve el mismo dist/index.html para estas URLs.
  // React Router las captura y monta el mismo componente que /spa/<x>.
  {
    path: '/ventas',
    element: <Layout />,
    children: [{ path: 'cotizador', lazy: cotizador }],
  },
  legacyRoute('/dashboard', dashboard),
  legacyRoute('/borradores', borradores),
  legacyRoute('/seguimiento', seguimiento),
  legacyRoute('/fantasmas', fantasmas),
  legacyRoute('/clientes', clientes),
  legacyRoute('/inventario', inventario),
  legacyRoute('/catalogos', catalogos),
  legacyRoute('/compras', compras),
  legacyRoute('/remisiones', remisiones),
  legacyRoute('/gastos', gastos),
  legacyRoute('/reportes', reportes),
  legacyRoute('/reportes-servicio', reportesServicio),
  legacyRoute('/reportes-servicio-docs', reportesServicioDocs),
  legacyRoute('/cuentas-por-cobrar', cxc),
  legacyRoute('/fx', fx),
  legacyRoute('/precios', precios),
  legacyRoute('/usuarios', usuarios),
  legacyRoute('/servicios', servicios),
]);

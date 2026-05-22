import { NavLink } from 'react-router-dom';
import { Activity, BarChart3, BookMarked, FileText, FileClock, Ghost, Home, LayoutDashboard, ListChecks, Package, Receipt, ShoppingCart, Truck, Users } from 'lucide-react';

const NAV = [
  { to: '/spa/dashboard', label: 'Dashboard', Icon: LayoutDashboard },
  { to: '/spa/hello', label: 'Inicio', Icon: Home },
  { to: '/spa/cotizador', label: 'Cotizador', Icon: FileText },
  { to: '/spa/borradores', label: 'Borradores', Icon: FileClock },
  { to: '/spa/seguimiento', label: 'Seguimiento', Icon: ListChecks },
  { to: '/spa/fantasmas', label: 'Fantasmas', Icon: Ghost },
  { to: '/spa/clientes', label: 'Clientes', Icon: Users },
  { to: '/spa/inventario', label: 'Inventario', Icon: Package },
  { to: '/spa/catalogos', label: 'Catálogos', Icon: BookMarked },
  { to: '/spa/compras', label: 'Compras', Icon: ShoppingCart },
  { to: '/spa/remisiones', label: 'Remisiones', Icon: Truck },
  { to: '/spa/gastos', label: 'Gastos', Icon: Receipt },
  { to: '/spa/reportes', label: 'Reportes', Icon: BarChart3 },
  { to: '/spa/reportes-servicio', label: 'Reportes Servicio', Icon: Activity },
];

export function Sidebar() {
  return (
    <aside className="w-64 bg-sidebar text-sidebar-text border-r border-slate-800 p-4">
      <div className="text-xl font-bold mb-6">
        DASIC <span className="text-accent-glow">·</span> SPA
      </div>
      <nav className="space-y-1">
        {NAV.map(({ to, label, Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-2 px-3 py-2 rounded-lg transition ${
                isActive ? 'bg-accent-glow/10 text-accent-glow' : 'hover:bg-slate-800'
              }`
            }
          >
            <Icon className="h-4 w-4" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}

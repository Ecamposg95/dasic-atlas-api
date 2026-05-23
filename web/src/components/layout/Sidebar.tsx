import { NavLink } from 'react-router-dom';
import type { LucideIcon } from 'lucide-react';
import {
  Activity, BarChart3, BookMarked, ClipboardCheck, Coins, FileClock, FileText, Ghost,
  LayoutDashboard, ListChecks, Package, Receipt, ShoppingCart, Tags,
  Truck, UserCog, Users, Wallet, Wrench,
} from 'lucide-react';

type NavItem = { to: string; label: string; Icon: LucideIcon };
type NavSection = { title: string; items: NavItem[] };

// Secciones semánticas: el sidebar agrupa por dominio funcional para que el
// vendedor encuentre rápido lo que usa (Comercial), el operativo lo suyo
// (Operación), y el catálogo de datos quede separado del flujo diario.
const SECTIONS: NavSection[] = [
  {
    title: 'Comercial',
    items: [
      { to: '/spa/dashboard', label: 'Dashboard', Icon: LayoutDashboard },
      { to: '/spa/cotizador', label: 'Cotizador', Icon: FileText },
      { to: '/spa/borradores', label: 'Borradores', Icon: FileClock },
      { to: '/spa/seguimiento', label: 'Seguimiento', Icon: ListChecks },
      { to: '/spa/clientes', label: 'Clientes', Icon: Users },
    ],
  },
  {
    title: 'Operación',
    items: [
      { to: '/spa/compras', label: 'Compras', Icon: ShoppingCart },
      { to: '/spa/fantasmas', label: 'Fantasmas', Icon: Ghost },
      { to: '/spa/remisiones', label: 'Remisiones', Icon: Truck },
      { to: '/spa/reportes-servicio-docs', label: 'Reportes de servicio', Icon: ClipboardCheck },
      { to: '/spa/gastos', label: 'Gastos', Icon: Receipt },
    ],
  },
  {
    title: 'Catálogo',
    items: [
      { to: '/spa/inventario', label: 'Catálogo de productos', Icon: Package },
      { to: '/spa/servicios', label: 'Servicios', Icon: Wrench },
      { to: '/spa/precios', label: 'Precios', Icon: Tags },
      { to: '/spa/catalogos', label: 'Diccionarios', Icon: BookMarked },
    ],
  },
  {
    title: 'Finanzas',
    items: [
      { to: '/spa/cuentas-por-cobrar', label: 'Cuentas por cobrar', Icon: Wallet },
      { to: '/spa/fx', label: 'Tipo de cambio', Icon: Coins },
    ],
  },
  {
    title: 'Reportes',
    items: [
      { to: '/spa/reportes', label: 'Reportes', Icon: BarChart3 },
      { to: '/spa/reportes-servicio', label: 'Reportes servicio', Icon: Activity },
    ],
  },
  {
    title: 'Sistema',
    items: [
      { to: '/spa/usuarios', label: 'Usuarios', Icon: UserCog },
    ],
  },
];

export function Sidebar() {
  return (
    <aside className="w-64 bg-sidebar text-sidebar-text border-r border-slate-800 flex flex-col">
      <div className="px-4 pt-4 pb-3 shrink-0 border-b border-slate-800/60">
        <div className="text-xl font-bold leading-tight">Atlas ONE</div>
        <div className="text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-0.5">
          DASIC <span className="text-accent-glow">·</span> Sistema Industrial
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-3 space-y-4">
        {SECTIONS.map((section) => (
          <div key={section.title}>
            <div className="px-2 mb-1 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">
              {section.title}
            </div>
            <div className="space-y-0.5">
              {section.items.map(({ to, label, Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  className={({ isActive }) =>
                    `flex items-center gap-2 px-2.5 py-1.5 rounded-md text-[13px] transition ${
                      isActive
                        ? 'bg-accent-glow/10 text-accent-glow font-medium'
                        : 'text-slate-300 hover:bg-slate-800/60 hover:text-slate-100'
                    }`
                  }
                >
                  <Icon className="h-3.5 w-3.5 shrink-0" />
                  <span className="truncate">{label}</span>
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>
    </aside>
  );
}

import { useNavigate } from 'react-router-dom';
import { ShieldCheck, SlidersHorizontal, ScrollText, Activity, Database } from 'lucide-react';
import { useIsSuperadmin } from '@/lib/permissions';

const CARDS = [
  { to: '/spa/superadmin/config', icon: SlidersHorizontal, title: 'Configuración', desc: 'IVA y vigencia de cotización, sin redeploy.', activo: true },
  { to: '/spa/superadmin/audit', icon: ScrollText, title: 'Auditoría', desc: 'Línea de tiempo de actividad registrada.', activo: true },
  { to: '', icon: Activity, title: 'Salud del sistema', desc: 'Métricas y estado (próximamente).', activo: false },
  { to: '', icon: Database, title: 'Datos y mantenimiento', desc: 'Herramientas de datos (próximamente).', activo: false },
];

export function SuperAdminPage() {
  const navigate = useNavigate();
  const isSuper = useIsSuperadmin();
  if (!isSuper) {
    return <div className="p-6 text-sm text-slate-500">Solo el super-administrador puede acceder a esta consola.</div>;
  }
  return (
    <div className="p-6 max-w-5xl mx-auto space-y-4">
      <header className="flex items-center gap-2">
        <ShieldCheck className="h-5 w-5 text-accent-glow" />
        <h1 className="text-2xl font-semibold">Consola de plataforma</h1>
      </header>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {CARDS.map((c) => (
          <button
            key={c.title}
            type="button"
            disabled={!c.activo}
            onClick={() => c.activo && navigate(c.to)}
            className={`text-left border rounded-xl p-4 transition ${c.activo ? 'border-slate-200 dark:border-slate-800 hover:border-accent-glow' : 'border-dashed border-slate-200 dark:border-slate-800 opacity-60 cursor-not-allowed'}`}
          >
            <c.icon className="h-5 w-5 text-accent-glow mb-2" />
            <div className="font-semibold text-slate-800 dark:text-slate-200">{c.title}</div>
            <div className="text-xs text-slate-500 mt-1">{c.desc}</div>
          </button>
        ))}
      </div>
    </div>
  );
}

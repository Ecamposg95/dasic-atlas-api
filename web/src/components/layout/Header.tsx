import { useAuth } from '@/stores/auth';

export function Header() {
  const user = useAuth((s) => s.user);
  return (
    <header className="h-16 border-b border-slate-800 px-6 flex items-center justify-between bg-slate-900">
      <h2 className="text-sm uppercase tracking-wider text-slate-400">DASIC ERP — SPA</h2>
      {user && (
        <div className="text-sm">
          {user.nombre} <span className="text-slate-500">· {user.rol}</span>
        </div>
      )}
    </header>
  );
}

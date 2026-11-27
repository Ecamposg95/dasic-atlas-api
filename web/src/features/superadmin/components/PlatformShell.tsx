import { useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useIsSuperadmin } from '@/lib/permissions';
import { AtlasLockup } from '@/components/brand/Atlas';

// ─── Health banner types (minimal — only what the banner needs) ──────────────
type BannerHealth = {
  app?: { version?: string; git_sha?: string; env?: string };
};

// ─── Sub-nav links ────────────────────────────────────────────────────────────
const NAV_LINKS = [
  { to: '/spa/superadmin',               label: 'Overview',        end: true  },
  { to: '/spa/superadmin/usuarios',      label: 'Usuarios',        end: false },
  { to: '/spa/superadmin/acceso',        label: 'Acceso',          end: false },
  { to: '/spa/superadmin/config',        label: 'Configuración',   end: false },
  { to: '/spa/superadmin/audit',         label: 'Auditoría',       end: false },
  { to: '/spa/superadmin/salud',         label: 'Salud',           end: false },
  { to: '/spa/superadmin/mantenimiento', label: 'Mantenimiento',   end: false },
];

// ─── Component ────────────────────────────────────────────────────────────────
interface PlatformShellProps {
  title: string;
  children: React.ReactNode;
}

export function PlatformShell({ title, children }: PlatformShellProps) {
  const isSuperadmin = useIsSuperadmin();

  const { data: health } = useQuery<BannerHealth>({
    queryKey: ['superadmin', 'health', 'banner'],
    queryFn: () => api.get<BannerHealth>('/api/superadmin/health'),
    staleTime: 60_000,
    // Don't throw on error — banner stays visible without badges
    retry: false,
  });

  // La consola usa la marca Atlas Tech (Niebla en claro, Horizon en oscuro):
  // la clase vive en <html> para que también alcance a modales y al sidebar.
  useEffect(() => {
    if (!isSuperadmin) return;
    document.documentElement.classList.add('atlas-console');
    return () => document.documentElement.classList.remove('atlas-console');
  }, [isSuperadmin]);

  if (!isSuperadmin) {
    return (
      <div className="p-6 text-sm text-muted-foreground">
        Solo el super-administrador puede acceder a esta consola.
      </div>
    );
  }

  const version = health?.app?.version;
  const gitSha = health?.app?.git_sha;
  const env = health?.app?.env;
  const shortSha = gitSha ? gitSha.slice(0, 7) : null;
  const tag = 'font-mono text-[10px] px-2 py-0.5 rounded-full border';

  return (
    <div className="relative isolate flex flex-col min-h-full overflow-hidden bg-background">
      {/* Luz de marca: resplandor ember con contraluz índigo, detrás del contenido */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -z-10 -top-40 -right-32 h-[420px] w-[640px] rounded-full blur-3xl opacity-60 dark:opacity-100"
        style={{ background: 'radial-gradient(50% 50% at 50% 50%, rgba(255,106,31,.20), rgba(255,106,31,0))' }}
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -z-10 -bottom-48 -left-40 h-[420px] w-[680px] rounded-full blur-3xl opacity-50 dark:opacity-100"
        style={{ background: 'radial-gradient(50% 50% at 50% 50%, rgba(91,88,184,.20), rgba(91,88,184,0))' }}
      />

      {/* ── Barra de marca ──────────────────────────────────────────────────── */}
      <div className="px-6 py-3 flex items-center gap-3 flex-wrap border-b border-border">
        <AtlasLockup className="text-[15px] text-foreground" markClassName="h-5" />
        <span className="text-[10px] uppercase tracking-[0.22em] text-muted-foreground">
          Consola de plataforma
        </span>
        <span className="flex-1" />
        {/* Tags: solo cuando cargó la salud */}
        {env && <span className={`${tag} uppercase border-accent-glow/40 text-primary`}>{env}</span>}
        {version && <span className={`${tag} border-border-strong text-foreground`}>v{version}</span>}
        {shortSha && <span className={`${tag} border-border text-muted-foreground`}>{shortSha}</span>}
      </div>

      {/* ── Sub-navegación ──────────────────────────────────────────────────── */}
      <nav className="flex items-center gap-1 px-5 py-2 border-b border-border overflow-x-auto">
        {NAV_LINKS.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.end}
            className={({ isActive }) =>
              [
                'text-[13px] px-3.5 py-1.5 rounded-full whitespace-nowrap border transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-atlas-amber',
                isActive
                  ? 'bg-foreground text-background border-transparent font-medium'
                  : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border-strong',
              ].join(' ')
            }
          >
            {link.label}
          </NavLink>
        ))}
      </nav>

      {/* ── Título ──────────────────────────────────────────────────────────── */}
      <div className="px-6 pt-7 pb-4">
        <h1 className="text-[30px] leading-none font-light tracking-[-0.035em] text-foreground">
          {title}
          <span className="text-primary">.</span>
        </h1>
      </div>

      <div className="flex-1 px-6 pb-6">{children}</div>
    </div>
  );
}

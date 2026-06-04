import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ScrollText, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useIsSuperadmin } from '@/lib/permissions';
import { useUsuarios } from '@/features/usuarios/hooks/useUsuarios';
import { useAudit, type AuditFuente, type AuditFiltros } from '../hooks/useAudit';
import { useConfigPlataforma } from '../hooks/useConfigPlataforma';

const PAGE_SIZE = 50;

function fmtFecha(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString('es-MX', { dateStyle: 'short', timeStyle: 'short' });
}

export function AuditPage() {
  const navigate = useNavigate();
  const isSuper = useIsSuperadmin();
  const [fuente, setFuente] = useState<AuditFuente | ''>('');
  const [usuarioId, setUsuarioId] = useState<string>('');
  const [desde, setDesde] = useState<string>('');
  const [hasta, setHasta] = useState<string>('');
  const [page, setPage] = useState(1);

  const { data: usuarios } = useUsuarios();
  const { data: config } = useConfigPlataforma();
  const filtros: AuditFiltros = {
    fuente: fuente || undefined,
    usuario_id: usuarioId ? Number(usuarioId) : undefined,
    desde: desde || undefined,
    hasta: hasta || undefined,
    page,
  };
  const { data, isLoading } = useAudit(filtros);

  if (!isSuper) return <div className="p-6 text-sm text-slate-500">Solo el super-administrador.</div>;

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  function resetPage<T>(setter: (v: T) => void) {
    return (v: T) => { setter(v); setPage(1); };
  }

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-4">
      <header className="flex items-center justify-between gap-2 flex-wrap">
        <h1 className="text-2xl font-semibold flex items-center gap-2">
          <ScrollText className="h-5 w-5 text-accent-glow" /> Auditoría global
        </h1>
        <Button variant="ghost" size="sm" onClick={() => navigate('/spa/superadmin')}>
          <ArrowLeft className="h-4 w-4 mr-1" /> Volver
        </Button>
      </header>
      <p className="text-sm text-slate-500">
        Actividad registrada en el sistema (cotizaciones y fusiones de empresas).
      </p>

      {/* Snapshot de config vigente (platform_config solo guarda estado actual) */}
      {config?.items?.length ? (
        <div className="flex flex-wrap gap-4 text-xs border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-2 bg-slate-50 dark:bg-slate-900/40">
          <span className="text-slate-500 font-medium uppercase tracking-wide">Config vigente:</span>
          {config.items.map((c) => (
            <span key={c.clave} className="flex items-center gap-1">
              <span className="text-slate-500">{c.clave}:</span>
              <span className="font-medium">{String(c.valor_efectivo)}</span>
              <Badge variant={c.overrideado ? 'cyan' : 'slate'}>{c.overrideado ? 'override' : 'default'}</Badge>
            </span>
          ))}
        </div>
      ) : null}

      {/* Filtros */}
      <div className="flex flex-wrap gap-3 items-end">
        <div>
          <label className="block text-[11px] text-slate-500 mb-1">Fuente</label>
          <select
            value={fuente}
            onChange={(e) => resetPage(setFuente)(e.target.value as AuditFuente | '')}
            className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 rounded-md px-2 py-1.5 text-sm"
          >
            <option value="">Todas</option>
            <option value="cotizacion">Cotizaciones</option>
            <option value="fusion_cliente">Fusiones</option>
          </select>
        </div>
        <div>
          <label className="block text-[11px] text-slate-500 mb-1">Usuario</label>
          <select
            value={usuarioId}
            onChange={(e) => resetPage(setUsuarioId)(e.target.value)}
            className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 rounded-md px-2 py-1.5 text-sm"
          >
            <option value="">Todos</option>
            {(usuarios ?? []).map((u) => (
              <option key={u.id} value={u.id}>{u.nombre}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-[11px] text-slate-500 mb-1">Desde</label>
          <input
            type="date"
            value={desde}
            onChange={(e) => resetPage(setDesde)(e.target.value)}
            className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 rounded-md px-2 py-1.5 text-sm"
          />
        </div>
        <div>
          <label className="block text-[11px] text-slate-500 mb-1">Hasta</label>
          <input
            type="date"
            value={hasta}
            onChange={(e) => resetPage(setHasta)(e.target.value)}
            className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 rounded-md px-2 py-1.5 text-sm"
          />
        </div>
      </div>

      {/* Tabla */}
      <div className="border border-slate-200 dark:border-slate-800 rounded-xl overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 dark:bg-slate-900/60 text-slate-500 text-xs uppercase">
            <tr>
              <th className="text-left font-medium px-3 py-2">Fecha</th>
              <th className="text-left font-medium px-3 py-2">Usuario</th>
              <th className="text-left font-medium px-3 py-2">Acción</th>
              <th className="text-left font-medium px-3 py-2">Entidad</th>
              <th className="text-left font-medium px-3 py-2">Detalle</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={5} className="px-3 py-6 text-center text-slate-400">Cargando…</td></tr>
            ) : items.length === 0 ? (
              <tr><td colSpan={5} className="px-3 py-6 text-center text-slate-400">Sin actividad para estos filtros.</td></tr>
            ) : (
              items.map((e, i) => (
                <tr key={`${e.fuente}-${e.fecha}-${i}`} className="border-t border-slate-100 dark:border-slate-800/60 align-top">
                  <td className="px-3 py-2 whitespace-nowrap text-slate-500">{fmtFecha(e.fecha)}</td>
                  <td className="px-3 py-2 whitespace-nowrap">{e.usuario ?? '—'}</td>
                  <td className="px-3 py-2 whitespace-nowrap">
                    <Badge variant={e.fuente === 'fusion_cliente' ? 'slate' : 'cyan'}>{e.accion}</Badge>
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap font-medium">
                    {e.link ? (
                      <Link to={e.link} className="text-accent-glow hover:underline">{e.entidad}</Link>
                    ) : (
                      e.entidad
                    )}
                  </td>
                  <td className="px-3 py-2 text-slate-600 dark:text-slate-300">{e.detalle}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Paginación */}
      <div className="flex items-center justify-between text-sm text-slate-500">
        <span>{total} evento(s)</span>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Anterior</Button>
          <span>Página {page} de {totalPages}</span>
          <Button variant="ghost" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>Siguiente</Button>
        </div>
      </div>
    </div>
  );
}

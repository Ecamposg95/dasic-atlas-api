import { useState } from 'react';
import { confirm } from '@/lib/confirm';
import { useNavigate } from 'react-router-dom';
import { GitMerge, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { toast } from '@/lib/toast';
import { useIsAdmin } from '@/lib/permissions';
import { useDuplicados, useMergeEmpresas } from '../hooks/useDuplicados';
import type { GrupoDuplicado } from '../types';

function fmt(n: number) {
  return `$${Number(n || 0).toLocaleString('es-MX', { minimumFractionDigits: 2 })}`;
}

function GrupoCard({ grupo }: { grupo: GrupoDuplicado }) {
  const [survivor, setSurvivor] = useState<number>(grupo.miembros[0]?.id ?? 0);
  const merge = useMergeEmpresas();
  const losers = grupo.miembros.filter((m) => m.id !== survivor);

  async function onConfirm() {
    const surv = grupo.miembros.find((m) => m.id === survivor);
    const resumen =
      `Se moverán al sobreviviente «${surv?.nombre_empresa}»:\n` +
      losers.reduce((a, l) => a + l.n_ordenes, 0) + ' órdenes, ' +
      losers.reduce((a, l) => a + l.n_transacciones, 0) + ' transacciones, ' +
      losers.reduce((a, l) => a + l.n_remisiones, 0) + ' remisiones, ' +
      losers.reduce((a, l) => a + l.n_contactos, 0) + ' contactos.\n' +
      `Se BORRARÁN ${losers.length} empresa(s). Esta acción no se puede deshacer.\n¿Continuar?`;
    if (!(await confirm({ mensaje: resumen, tono: 'danger' }))) return;
    merge.mutate(
      { survivor_id: survivor, loser_ids: losers.map((l) => l.id) },
      {
        onSuccess: (r) => toast({ kind: 'success', title: `Fusionadas ${r.merged} empresa(s)` }),
        onError: (e) => {
          if (e.status === 401) { window.location.href = '/spa/login'; return; }
          toast({ kind: 'error', title: 'No se pudo fusionar', description: e.detail });
        },
      },
    );
  }

  return (
    <div className="border border-slate-200 dark:border-slate-800 rounded-xl p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">RFC <span className="font-mono">{grupo.rfc}</span> · {grupo.miembros.length} registros</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm min-w-[640px]">
          <thead className="text-[11px] uppercase text-slate-500">
            <tr>
              <th className="p-2 text-center">Sobrevive</th>
              <th className="p-2 text-left">Empresa</th>
              <th className="p-2 text-left">Contacto</th>
              <th className="p-2 text-right">Saldo</th>
              <th className="p-2 text-right">Crédito</th>
              <th className="p-2 text-center">Órd</th>
              <th className="p-2 text-center">Trans</th>
              <th className="p-2 text-center">Remis</th>
              <th className="p-2 text-center">Cont</th>
            </tr>
          </thead>
          <tbody>
            {grupo.miembros.map((m) => (
              <tr key={m.id} className={`border-t border-slate-100 dark:border-slate-800 ${m.id === survivor ? 'bg-emerald-50 dark:bg-emerald-900/10' : ''}`}>
                <td className="p-2 text-center">
                  <input type="radio" name={`surv-${grupo.rfc}`} checked={m.id === survivor} onChange={() => setSurvivor(m.id)} />
                </td>
                <td className="p-2">{m.nombre_empresa}</td>
                <td className="p-2 text-slate-500">{m.contacto_nombre || '—'}</td>
                <td className="p-2 text-right font-mono">{fmt(m.saldo_actual)}</td>
                <td className="p-2 text-right font-mono">{fmt(m.limite_credito)}</td>
                <td className="p-2 text-center">{m.n_ordenes}</td>
                <td className="p-2 text-center">{m.n_transacciones}</td>
                <td className="p-2 text-center">{m.n_remisiones}</td>
                <td className="p-2 text-center">{m.n_contactos}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between">
        <p className="text-xs text-slate-500">El saldo del sobreviviente se recalcula desde sus transacciones.</p>
        <Button size="sm" onClick={onConfirm} disabled={merge.isPending || losers.length === 0}>
          {merge.isPending ? 'Fusionando…' : `Fusionar ${losers.length} → sobreviviente`}
        </Button>
      </div>
    </div>
  );
}

export function UnificarEmpresasPage() {
  const navigate = useNavigate();
  const isAdmin = useIsAdmin();
  const { data, isLoading } = useDuplicados();

  if (!isAdmin) {
    return <div className="p-6 text-sm text-slate-500">Solo administradores pueden unificar empresas.</div>;
  }

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-4">
      <header className="flex items-center justify-between gap-2 flex-wrap">
        <h1 className="text-2xl font-semibold flex items-center gap-2">
          <GitMerge className="h-5 w-5 text-accent-glow" /> Unificar empresas duplicadas
        </h1>
        <Button variant="ghost" size="sm" onClick={() => navigate('/spa/clientes')}>
          <ArrowLeft className="h-4 w-4 mr-1" /> Volver
        </Button>
      </header>
      <p className="text-sm text-slate-500">
        Empresas con el mismo RFC. Elige el sobreviviente por grupo; las demás se fusionan en él
        (órdenes, transacciones, remisiones y contactos se mueven; el saldo se recalcula) y se borran.
        Acción irreversible — toma un respaldo antes.
      </p>
      {isLoading ? (
        <p className="text-sm text-slate-400">Cargando…</p>
      ) : !data?.length ? (
        <div className="text-center py-12">
          <Badge variant="emerald">Sin duplicados por RFC 🎉</Badge>
        </div>
      ) : (
        <div className="space-y-4">
          {data.map((g) => <GrupoCard key={g.rfc} grupo={g} />)}
        </div>
      )}
    </div>
  );
}

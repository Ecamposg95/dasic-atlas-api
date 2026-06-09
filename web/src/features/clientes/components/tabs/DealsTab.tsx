import { useEmpresaDeals } from '../../hooks/useEmpresa360';

export function DealsTab({ clienteId }: { clienteId: number }) {
  const { data, isLoading } = useEmpresaDeals(clienteId);
  if (isLoading) return <div className="text-sm text-muted-foreground p-4">Cargando deals…</div>;
  if (!data?.length) return <div className="text-sm text-muted-foreground p-4">Sin deals en el pipeline.</div>;
  return (
    <ul className="space-y-2 p-1">
      {data.map((d) => (
        <li key={d.id} className="flex items-center justify-between rounded-lg border border-border bg-surface-2 p-3">
          <div>
            <div className="text-sm text-foreground">{d.titulo}</div>
            <div className="text-xs text-muted-foreground">{d.stage ?? '—'} · {d.owner ?? ''}</div>
          </div>
          <div className="text-sm font-semibold text-foreground">
            {d.monto != null ? `$${d.monto.toLocaleString('es-MX')} ${d.moneda ?? ''}` : '—'}
          </div>
        </li>
      ))}
    </ul>
  );
}

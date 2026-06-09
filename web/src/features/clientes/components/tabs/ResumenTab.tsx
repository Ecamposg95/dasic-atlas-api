import { useEmpresaResumen } from '../../hooks/useEmpresa360';

const money = (n: number) => `$${n.toLocaleString('es-MX', { minimumFractionDigits: 2 })}`;

export function ResumenTab({ clienteId }: { clienteId: number }) {
  const { data, isLoading } = useEmpresaResumen(clienteId);
  if (isLoading || !data) return <div className="text-sm text-muted-foreground p-4">Cargando métricas…</div>;
  const cards: [string, string][] = [
    ['Total vendido', money(data.total_vendido)],
    ['Ventas', String(data.n_ventas)],
    ['Cotizaciones', String(data.n_cotizaciones)],
    ['Ticket promedio', money(data.ticket_promedio)],
    ['Última compra', data.ultima_compra ? new Date(data.ultima_compra).toLocaleDateString('es-MX') : '—'],
    ['Saldo actual', money(data.saldo_actual)],
    ['Crédito disponible', money(data.credito_disponible)],
  ];
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 p-1">
      {cards.map(([label, val]) => (
        <div key={label} className="rounded-lg border border-border bg-surface-2 p-3">
          <div className="text-xs text-muted-foreground">{label}</div>
          <div className="text-lg font-semibold text-foreground mt-1">{val}</div>
        </div>
      ))}
    </div>
  );
}

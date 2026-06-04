import { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import type { BadgeProps } from '@/components/ui/badge';
import { DealCard } from './DealCard';
import type { Stage, Deal } from '../types';
import type { Cliente } from '@/features/clientes/types';
import type { Usuario } from '@/features/usuarios/types';

type BadgeVariant = BadgeProps['variant'];

// Map backend color string → Badge variant token.
function colorToVariant(color: string | null): BadgeVariant {
  if (!color) return 'default';
  const c = color.toLowerCase();
  if (c.includes('cyan') || c.includes('blue') || c.includes('lead')) return 'cyan';
  if (c.includes('amber') || c.includes('yellow') || c.includes('orange')) return 'amber';
  if (c.includes('green') || c.includes('emerald') || c.includes('won') || c.includes('ganado')) return 'emerald';
  if (c.includes('red') || c.includes('rose') || c.includes('lost') || c.includes('perdido')) return 'rose';
  if (c.includes('violet') || c.includes('purple')) return 'violet';
  if (c.includes('slate') || c.includes('gray') || c.includes('grey')) return 'slate';
  // Fallback: use es_ganado / es_perdido (passed via props)
  return 'default';
}

function stageVariant(stage: Stage): BadgeVariant {
  if (stage.es_ganado) return 'emerald';
  if (stage.es_perdido) return 'rose';
  return colorToVariant(stage.color);
}

function sumMontos(deals: Deal[]): number {
  return deals.reduce((acc, d) => acc + (d.monto ?? 0), 0);
}

function formatSum(n: number): string {
  if (n === 0) return '';
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: 'MXN',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(n);
}

type Props = {
  stage: Stage;
  deals: Deal[];
  clientesMap: Map<number, Cliente>;
  usuariosMap: Map<number, Usuario>;
  onEdit: (deal: Deal) => void;
  onDelete: (deal: Deal) => void;
  onDrop: (dealId: number, stageId: number) => void;
};

export function KanbanColumn({ stage, deals, clientesMap, usuariosMap, onEdit, onDelete, onDrop }: Props) {
  const [isDragOver, setIsDragOver] = useState(false);

  function handleDragOver(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setIsDragOver(true);
  }

  function handleDragLeave(e: React.DragEvent<HTMLDivElement>) {
    // Only clear if leaving the column entirely (not entering a child).
    if (!e.currentTarget.contains(e.relatedTarget as Node)) {
      setIsDragOver(false);
    }
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragOver(false);
    const raw = e.dataTransfer.getData('text/plain');
    const dealId = parseInt(raw, 10);
    if (!isNaN(dealId)) {
      onDrop(dealId, stage.id);
    }
  }

  const variant = stageVariant(stage);
  const total = sumMontos(deals);

  return (
    <div className="flex flex-col w-64 shrink-0">
      {/* Column header */}
      <div className="flex items-center justify-between mb-2 px-1">
        <div className="flex items-center gap-1.5 min-w-0">
          <Badge variant={variant}>{stage.nombre}</Badge>
          <span className="text-[11px] text-muted-foreground font-medium shrink-0">
            {deals.length}
          </span>
        </div>
        {total > 0 && (
          <span className="text-[10px] text-muted-foreground tabular-nums shrink-0">
            {formatSum(total)}
          </span>
        )}
      </div>

      {/* Drop zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`flex-1 min-h-[120px] rounded-xl p-2 space-y-2 transition-all duration-150 ${
          isDragOver
            ? 'ring-2 ring-accent-glow bg-accent-glow/5'
            : 'bg-surface-2/50'
        }`}
      >
        {deals.length === 0 && (
          <div className="flex items-center justify-center h-20 text-[11px] text-muted-foreground opacity-50 border-2 border-dashed border-border rounded-lg">
            Sin deals
          </div>
        )}
        {deals.map((deal) => (
          <DealCard
            key={deal.id}
            deal={deal}
            clientesMap={clientesMap}
            usuariosMap={usuariosMap}
            onEdit={onEdit}
            onDelete={onDelete}
          />
        ))}
      </div>
    </div>
  );
}

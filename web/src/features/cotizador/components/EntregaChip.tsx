import { Clock } from 'lucide-react';

type Props = {
  min: number | null;
  max: number | null;
  unidad: 'dias' | 'semanas' | null;
};

export function EntregaChip({ min, max, unidad }: Props) {
  const completo = min != null && max != null && unidad != null;
  if (!completo) {
    return (
      <span className="text-[10px] bg-slate-800 text-slate-400 border border-dashed border-slate-700 px-1.5 py-0.5 rounded flex items-center gap-1">
        <Clock className="h-2.5 w-2.5" /> + Entrega
      </span>
    );
  }
  const lbl = min === max ? `${min}` : `${min}–${max}`;
  const u = unidad === 'dias' ? 'd' : 'sem';
  return (
    <span className="text-[10px] bg-cyan-900/30 text-cyan-300 px-1.5 py-0.5 rounded flex items-center gap-1">
      <Clock className="h-2.5 w-2.5" /> {lbl} {u}
    </span>
  );
}

type Props = { utilidad: number };

export function MargenChip({ utilidad }: Props) {
  let cls = 'bg-emerald-900/30 text-emerald-300';
  if (utilidad < 5) cls = 'bg-rose-900/30 text-rose-300 font-bold';
  else if (utilidad < 15) cls = 'bg-amber-900/30 text-amber-300';
  return (
    <span className={`text-[10px] px-1.5 py-0.5 rounded ${cls}`}>
      {utilidad.toFixed(1)}% util.
    </span>
  );
}

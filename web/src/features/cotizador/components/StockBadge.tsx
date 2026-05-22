type Props = { stock: number; qty: number };

export function StockBadge({ stock, qty }: Props) {
  if (stock >= qty) {
    return (
      <span className="text-[10px] bg-emerald-900/30 text-emerald-300 px-1.5 py-0.5 rounded font-medium">
        {stock} en stock
      </span>
    );
  }
  if (stock > 0) {
    return (
      <span className="text-[10px] bg-amber-900/30 text-amber-300 px-1.5 py-0.5 rounded font-medium">
        {stock}/{qty} · OC
      </span>
    );
  }
  return (
    <span className="text-[10px] bg-rose-900/30 text-rose-300 px-1.5 py-0.5 rounded font-medium">
      Sin stock · OC
    </span>
  );
}
